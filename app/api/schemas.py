from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Document schemas ---

class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    num_chunks: int
    message: str


class DocumentListItem(BaseModel):
    doc_id: str
    filename: str
    uploaded_at: datetime
    num_chunks: int


# --- Query schemas ---

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    collection: Optional[str] = None  # defaults to settings.CHROMA_COLLECTION
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


class SourceChunk(BaseModel):
    doc_id: str
    filename: str
    chunk_index: int
    text: str
    score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceChunk]
    latency_ms: float


# --- Health schema ---

class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, str]