from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter
from fastapi.responses import Response

# ── Metrics definitions ────────────────────────────────────────────────────────

# Total requests broken down by endpoint and status
REQUEST_COUNT = Counter(
    "documind_requests_total",
    "Total number of requests",
    ["endpoint", "method", "status"],
)

# Request latency histogram — buckets tuned for LLM workloads (slow!)
REQUEST_LATENCY = Histogram(
    "documind_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120, 300],
)

# RAG pipeline specific latency — retrieval + generation combined
RAG_LATENCY = Histogram(
    "documind_rag_latency_seconds",
    "RAG pipeline latency in seconds",
    buckets=[1, 2, 5, 10, 30, 60, 120, 300],
)

# LLM generation time only
LLM_LATENCY = Histogram(
    "documind_llm_latency_seconds",
    "LLM generation latency in seconds",
    buckets=[1, 2, 5, 10, 30, 60, 120, 300],
)

# Document ingestion metrics
DOCS_INGESTED = Counter(
    "documind_documents_ingested_total",
    "Total documents ingested",
)

CHUNKS_STORED = Counter(
    "documind_chunks_stored_total",
    "Total chunks stored in ChromaDB",
)

# Active requests gauge — goes up on request start, down on end
ACTIVE_REQUESTS = Gauge(
    "documind_active_requests",
    "Number of active requests",
)

# RAG retrieval — how many chunks were retrieved per query
CHUNKS_RETRIEVED = Histogram(
    "documind_chunks_retrieved",
    "Number of chunks retrieved per RAG query",
    buckets=[1, 2, 3, 5, 10],
)


# ── Metrics endpoint ───────────────────────────────────────────────────────────

router = APIRouter()


@router.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus scrape endpoint.
    Add this URL to your Prometheus config as a scrape target.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )