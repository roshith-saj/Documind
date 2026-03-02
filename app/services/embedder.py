from sentence_transformers import SentenceTransformer
from app.core.config import get_settings
from app.core.exceptions import EmbeddingError
from app.core.logging import logger

settings = get_settings()


class EmbedderService:
    def __init__(self):
        self._model = None  # lazy load — don't load on import, only on first use

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded.")
        return self._model

    def embed(self, text: str) -> list[float]:
        """Embed a single string. Used for query embedding at retrieval time."""
        try:
            vector = self.model.encode(text, normalize_embeddings=True)
            return vector.tolist()
        except Exception as e:
            raise EmbeddingError(str(e))

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of strings. Used during document ingestion."""
        try:
            logger.info(f"Embedding batch of {len(texts)} chunks...")
            vectors = self.model.encode(
                texts,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                normalize_embeddings=True,
                show_progress_bar=len(texts) > 10,
            )
            logger.info("Batch embedding complete.")
            return [v.tolist() for v in vectors]
        except Exception as e:
            raise EmbeddingError(str(e))


embedder_service = EmbedderService()