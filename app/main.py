from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import logger
from app.core.exceptions import DocuMindException
from app.api.routes import health, documents, query

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Ollama model: {settings.OLLAMA_MODEL} @ {settings.OLLAMA_BASE_URL}")
    # TODO: warm up embedding model, ping ChromaDB on startup
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="RAG-powered document Q&A API",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global exception handler ---
@app.exception_handler(DocuMindException)
async def documind_exception_handler(request: Request, exc: DocuMindException):
    logger.error(f"DocuMindException: {exc}")
    return JSONResponse(status_code=400, content={"detail": str(exc)})

# --- Routers ---
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=f"{settings.API_PREFIX}/documents")
app.include_router(query.router, prefix=f"{settings.API_PREFIX}/query")


@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}. Docs at {settings.API_PREFIX}/docs"}