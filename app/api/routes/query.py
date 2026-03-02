from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.api.schemas import QueryRequest, QueryResponse
from app.core.logging import logger
from app.services.llm import ollama_service
import time

router = APIRouter()


@router.post("/", response_model=QueryResponse, tags=["Query"])
async def query_documents(request: QueryRequest):
    """
    Ask a question against indexed documents.
    Returns the LLM answer + source chunks used for context.
    Note: sources will be populated once ChromaDB RAG pipeline is wired up in Week 2.
    """
    start = time.time()
    logger.info(f"Query received: '{request.question}'")

    # Direct LLM call for now — Week 2 will prepend retrieved context (RAG)
    answer = await ollama_service.generate(request.question)

    return QueryResponse(
        question=request.question,
        answer=answer,
        sources=[],  # TODO (Week 2): populate from ChromaDB retrieval
        latency_ms=round((time.time() - start) * 1000, 2),
    )


@router.post("/stream", tags=["Query"])
async def query_documents_stream(request: QueryRequest):
    """
    Same as /query but streams the LLM response token-by-token as Server-Sent Events.
    """
    logger.info(f"Streaming query received: '{request.question}'")

    async def event_stream():
        async for chunk in ollama_service.generate_stream(request.question):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")