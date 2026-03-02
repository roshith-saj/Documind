from fastapi import APIRouter
from app.api.schemas import HealthResponse
from app.core.config import get_settings
from app.services.llm import ollama_service

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Liveness probe. Checks connectivity to core services.
    Used by ECS health checks and load balancer.
    """
    ollama_status = "ok" if await ollama_service.is_healthy() else "unreachable"

    return HealthResponse(
        status="ok" if ollama_status == "ok" else "degraded",
        version=settings.APP_VERSION,
        services={
            "ollama": ollama_status,
            "chromadb": "unchecked",  # wired up in Week 1 Part 2
        },
    )