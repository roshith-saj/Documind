from fastapi import APIRouter, UploadFile, File, HTTPException
from app.api.schemas import DocumentUploadResponse, DocumentListItem
from app.core.logging import logger

router = APIRouter()


@router.post("/", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and index a document. Supported types: PDF, TXT, DOCX.
    The document will be chunked, embedded, and stored in ChromaDB.
    """
    # TODO (Week 1, Part 2): wire up ingestion + embedding pipeline
    logger.info(f"Received file: {file.filename} ({file.content_type})")

    allowed_types = {"application/pdf", "text/plain",
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")

    return DocumentUploadResponse(
        doc_id="stub-id-001",
        filename=file.filename,
        num_chunks=0,
        message="[Stub] Upload received. Embedding pipeline not yet connected.",
    )


@router.get("/", response_model=list[DocumentListItem], tags=["Documents"])
async def list_documents():
    """List all indexed documents."""
    # TODO (Week 1, Part 2): query ChromaDB metadata
    return []


@router.delete("/{doc_id}", tags=["Documents"])
async def delete_document(doc_id: str):
    """Remove a document and its chunks from the vector store."""
    # TODO: implement deletion from ChromaDB
    return {"message": f"[Stub] Document {doc_id} deletion not yet implemented."}