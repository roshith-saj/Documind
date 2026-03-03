import chromadb
import httpx
from dataclasses import dataclass
from app.core.config import get_settings
from app.core.exceptions import VectorStoreError
from app.core.logging import logger
from app.services.ingestion import DocumentChunk

settings = get_settings()


@dataclass
class RetrievedChunk:
    doc_id: str
    filename: str
    chunk_index: int
    text: str
    score: float


class VectorStoreService:
    def __init__(self):
        self._client = None
        self._collection = None

    @property
    def client(self):
        if self._client is None:
            logger.info(f"Connecting to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
            self._client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Using ChromaDB collection: '{settings.CHROMA_COLLECTION}'")
        return self._collection

    def is_healthy(self) -> bool:
        try:
            r = httpx.get(
                f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v1/heartbeat",
                timeout=3,
            )
            return r.status_code == 200
        except Exception:
            return False

    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]):
        try:
            self.collection.add(
                ids=[c.chunk_id for c in chunks],
                embeddings=embeddings,
                documents=[c.text for c in chunks],
                metadatas=[{
                    "doc_id": c.doc_id,
                    "filename": c.filename,
                    "chunk_index": c.chunk_index,
                } for c in chunks],
            )
            logger.info(f"Stored {len(chunks)} chunks in ChromaDB")
        except Exception as e:
            raise VectorStoreError(str(e))

    def query(self, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            chunks = []
            for text, meta, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                chunks.append(RetrievedChunk(
                    doc_id=meta["doc_id"],
                    filename=meta["filename"],
                    chunk_index=meta["chunk_index"],
                    text=text,
                    score=round(1 - distance, 4),
                ))
            return chunks
        except Exception as e:
            raise VectorStoreError(str(e))

    def delete_by_doc_id(self, doc_id: str):
        try:
            results = self.collection.get(where={"doc_id": doc_id})
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for doc_id={doc_id}")
        except Exception as e:
            raise VectorStoreError(str(e))

    def list_documents(self) -> list[dict]:
        try:
            results = self.collection.get(include=["metadatas"])
            seen = {}
            for meta in results["metadatas"]:
                doc_id = meta["doc_id"]
                if doc_id not in seen:
                    seen[doc_id] = {
                        "doc_id": doc_id,
                        "filename": meta["filename"],
                        "num_chunks": 1,
                    }
                else:
                    seen[doc_id]["num_chunks"] += 1
            return list(seen.values())
        except Exception as e:
            raise VectorStoreError(str(e))


vector_store_service = VectorStoreService()