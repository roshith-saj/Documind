import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.api.schemas import DocumentUploadResponse, DocumentListItem
from app.core.logging import logger
from app.services.ingestion import ingestion_service
from app.services.embedder import embedder_service
from app.services.vector_store import vector_store_service
from datetime import datetime, timezone

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


@router.post("/", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and index a document. Supported types: PDF, TXT, DOCX.
    The document will be chunked, embedded, and stored in ChromaDB.
    """
    from pathlib import Path
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}")

    logger.info(f"Ingesting file: {file.filename}")
    content = await file.read()
    doc_id = str(uuid.uuid4())

    # 1. Parse + chunk
    chunks = ingestion_service.parse_and_chunk(file.filename, content, doc_id)

    # 2. Embed all chunks
    embeddings = embedder_service.embed_batch([c.text for c in chunks])

    # 3. Store in ChromaDB
    vector_store_service.add_chunks(chunks, embeddings)

    logger.info(f"Successfully indexed '{file.filename}' → doc_id={doc_id}, chunks={len(chunks)}")
    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=file.filename,
        num_chunks=len(chunks),
        message=f"Successfully indexed {len(chunks)} chunks.",
    )


@router.get("/", response_model=list[DocumentListItem], tags=["Documents"])
async def list_documents():
    """List all indexed documents."""
    docs = vector_store_service.list_documents()
    return [
        DocumentListItem(
            doc_id=d["doc_id"],
            filename=d["filename"],
            uploaded_at=datetime.now(timezone.utc),
            num_chunks=d["num_chunks"],
        )
        for d in docs
    ]


@router.delete("/{doc_id}", tags=["Documents"])
async def delete_document(doc_id: str):
    """Remove a document and all its chunks from the vector store."""
    vector_store_service.delete_by_doc_id(doc_id)
    return {"message": f"Document {doc_id} deleted successfully."}