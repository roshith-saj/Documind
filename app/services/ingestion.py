import uuid
from pathlib import Path
from dataclasses import dataclass
from app.core.config import get_settings
from app.core.exceptions import DocuMindException
from app.core.logging import logger

settings = get_settings()


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_id: str
    filename: str
    text: str
    chunk_index: int


class IngestionService:
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    # --- Parsers ---

    def _parse_txt(self, content: bytes) -> str:
        return content.decode("utf-8", errors="ignore")

    def _parse_pdf(self, content: bytes) -> str:
        try:
            import pypdf
            import io
            reader = pypdf.PdfReader(io.BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except Exception as e:
            raise DocuMindException(f"Failed to parse PDF: {e}")

    def _parse_docx(self, content: bytes) -> str:
        try:
            import docx
            import io
            doc = docx.Document(io.BytesIO(content))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            raise DocuMindException(f"Failed to parse DOCX: {e}")

    def parse(self, filename: str, content: bytes) -> str:
        ext = Path(filename).suffix.lower()
        logger.info(f"Parsing {filename} (ext={ext})")
        if ext == ".pdf":
            return self._parse_pdf(content)
        elif ext == ".txt":
            return self._parse_txt(content)
        elif ext == ".docx":
            return self._parse_docx(content)
        else:
            raise DocuMindException(f"Unsupported file type: {ext}")

    # --- Chunker ---

    def chunk_text(self, text: str, doc_id: str, filename: str) -> list[DocumentChunk]:
        """
        Split text into overlapping chunks of ~CHUNK_SIZE characters.
        Overlap ensures context isn't lost at chunk boundaries.
        """
        text = " ".join(text.split())  # normalize whitespace
        chunks = []
        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at a sentence boundary rather than mid-word
            if end < len(text):
                boundary = text.rfind(". ", start, end)
                if boundary != -1 and boundary > start + self.chunk_size // 2:
                    end = boundary + 1  # include the period

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    doc_id=doc_id,
                    filename=filename,
                    text=chunk_text,
                    chunk_index=index,
                ))
                index += 1

            # Move forward by chunk_size minus overlap
            start += self.chunk_size - self.chunk_overlap

        logger.info(f"Chunked '{filename}' into {len(chunks)} chunks "
                    f"(size={self.chunk_size}, overlap={self.chunk_overlap})")
        return chunks

    def parse_and_chunk(self, filename: str, content: bytes, doc_id: str) -> list[DocumentChunk]:
        text = self.parse(filename, content)
        if not text.strip():
            raise DocuMindException(f"No text could be extracted from '{filename}'")
        return self.chunk_text(text, doc_id, filename)


ingestion_service = IngestionService()