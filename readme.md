# DocuMind 🧠

A production-grade RAG (Retrieval-Augmented Generation) API that lets you upload documents and ask questions about them. Built with FastAPI, Mistral 7B, ChromaDB, and deployed to AWS ECS.

---

## Architecture

```
┌─────────────┐    ┌──────────────┐     ┌─────────────────┐
│   Client    │───▶│  FastAPI App │───▶│  Mistral 7B     │
│             │    │  (Docker)    │     │  via Ollama     │
└─────────────┘    └──────┬───────┘     └─────────────────┘
                          │
               ┌──────────┼──────────┐
               ▼          ▼          ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ChromaDB  │ │Postgres  │ │Prometheus│
        │(vectors) │ │(metadata)│ │+ Grafana │
        └──────────┘ └──────────┘ └──────────┘
```

### Tech Stack

| Layer | Technology | Why |
|---|---|---|
| API | FastAPI + Python 3.12 | Async, auto-docs, fast |
| LLM | Mistral 7B via Ollama | Open-source, runs locally |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Fast, lightweight, high quality |
| Vector DB | ChromaDB | Simple to self-host, great Python SDK |
| Monitoring | Prometheus + Grafana | Industry standard |
| Deployment | AWS ECS + Fargate | Serverless containers |
| IaC | Terraform | Reproducible infrastructure |

---

## Project Structure

```
documind/
├── app/
│   ├── main.py                   # FastAPI entrypoint, middleware, lifespan
│   ├── api/
│   │   ├── schemas.py            # Pydantic request/response models
│   │   └── routes/
│   │       ├── health.py         # GET /health — liveness probe
│   │       ├── documents.py      # POST/GET/DELETE /documents
│   │       └── query.py          # POST /query, POST /query/stream
│   ├── core/
│   │   ├── config.py             # pydantic-settings, .env management
│   │   ├── logging.py            # structured logging setup
│   │   └── exceptions.py        # custom exception hierarchy
│   ├── services/
│   │   ├── ingestion.py          # PDF/TXT/DOCX parsing + chunking
│   │   ├── embedder.py           # sentence-transformers wrapper
│   │   ├── vector_store.py       # ChromaDB client
│   │   ├── rag_pipeline.py       # orchestrates retrieval + generation
│   │   └── llm.py                # Ollama async client (stream + non-stream)
│   └── monitoring/
│       └── metrics.py            # Prometheus instrumentation (Week 3)
├── docker/
│   └── docker-compose.yml        # ChromaDB + Prometheus + Grafana
├── infra/                        # AWS ECS Terraform (Week 3)
├── tests/
│   └── test_api.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama for Windows](https://ollama.com/download)

### 1. Clone & install

```bash
git clone https://github.com/your-username/documind.git
cd documind

python -m venv .venv
.venv\Scripts\Activate.ps1       # Windows PowerShell
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env if needed — defaults work out of the box on Windows
```

### 3. Start ChromaDB

```bash
cd docker
docker compose up -d
cd ..
```

### 4. Start Ollama + pull model

Download and install Ollama from https://ollama.com/download, then:

```powershell
ollama pull mistral
# Ollama runs automatically as a Windows service after install
```

### 5. Run the API

```powershell
uvicorn app.main:app --reload
```

API is now live at **http://localhost:8000**
Interactive docs at **http://localhost:8000/api/v1/docs**

---

## API Reference

### Health Check
```
GET /api/v1/health
```
Returns status of all dependent services (Ollama, ChromaDB).

### Upload a Document
```
POST /api/v1/documents/
Content-Type: multipart/form-data

file: <your .pdf, .txt, or .docx>
```

### List Documents
```
GET /api/v1/documents/
```

### Delete a Document
```
DELETE /api/v1/documents/{doc_id}
```

### Query (RAG)
```
POST /api/v1/query/
Content-Type: application/json

{
  "question": "What does the document say about X?",
  "top_k": 5
}
```

### Query (Streaming)
```
POST /api/v1/query/stream
```
Same as above but streams the response as Server-Sent Events.

---

## How the RAG Pipeline Works

```
User question
     │
     ▼
Embed question          ← sentence-transformers/all-MiniLM-L6-v2
     │
     ▼
Query ChromaDB          ← cosine similarity search, top_k chunks
     │
     ▼
Build context prompt    ← inject retrieved chunks into prompt template
     │
     ▼
Generate with Mistral   ← Ollama REST API
     │
     ▼
Return answer + sources ← includes which chunks were used and similarity scores
```

---

## Development Progress

- [x] **Week 1** — FastAPI skeleton, config, Ollama + Mistral 7B, document ingestion (PDF/TXT/DOCX), sentence-transformers embeddings, ChromaDB vector store, full RAG pipeline with sources
- [ ] **Week 2** — Dockerize full stack, add Docker Compose for all services
- [ ] **Week 3** — Deploy to AWS ECS with Fargate, CI/CD via GitHub Actions
- [ ] **Week 4** — Prometheus metrics, Grafana dashboards, polish & demo

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `mistral` | Model to use for generation |
| `CHROMA_HOST` | `localhost` | ChromaDB host |
| `CHROMA_PORT` | `8000` | ChromaDB port |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `CHUNK_SIZE` | `512` | Characters per chunk |
| `CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `TOP_K_RESULTS` | `5` | Chunks retrieved per query |

---

## Running Tests

```powershell
pytest tests/ -v
```

---

## License

MIT