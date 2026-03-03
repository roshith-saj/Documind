from fastapi import APIRouter
from app.api.schemas import HealthResponse
from app.core.config import get_settings
from app.services.llm import ollama_service
from app.services.vector_store import vector_store_service

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    ollama_status = "ok" if await ollama_service.is_healthy() else "unreachable"
    chroma_status = "ok" if vector_store_service.is_healthy() else "unreachable"

    overall = "ok" if all(s == "ok" for s in [ollama_status, chroma_status]) else "degraded"

    return HealthResponse(
        status=overall,
        version=settings.APP_VERSION,
        services={
            "ollama": ollama_status,
            "chromadb": chroma_status,
        },
    )