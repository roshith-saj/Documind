from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.api.schemas import QueryRequest, QueryResponse, SourceChunk
from app.core.logging import logger
from app.services.rag_pipeline import rag_pipeline
import time

router = APIRouter()


@router.post("/", response_model=QueryResponse, tags=["Query"])
async def query_documents(request: QueryRequest):
    """
    Ask a question against indexed documents.
    Retrieves relevant chunks from ChromaDB, then generates an answer with Mistral.
    """
    start = time.time()
    logger.info(f"Query: '{request.question}'")

    answer, chunks = await rag_pipeline.query(
        question=request.question,
        top_k=request.top_k,
    )

    return QueryResponse(
        question=request.question,
        answer=answer,
        sources=[
            SourceChunk(
                doc_id=c.doc_id,
                filename=c.filename,
                chunk_index=c.chunk_index,
                text=c.text,
                score=c.score,
            )
            for c in chunks
        ],
        latency_ms=round((time.time() - start) * 1000, 2),
    )


@router.post("/stream", tags=["Query"])
async def query_documents_stream(request: QueryRequest):
    """Streams the LLM response token-by-token as Server-Sent Events."""
    logger.info(f"Streaming query: '{request.question}'")

    async def event_stream():
        async for token in rag_pipeline.query_stream(request.question, request.top_k):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")