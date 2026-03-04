# ── Stage 1: Builder ──────────────────────────────────────────────────────────
# We use a separate stage just to install dependencies.
# This keeps the final image lean — build tools don't end up in production.
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies needed to compile Python packages (e.g. chroma-hnswlib)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies first (separate from code).
# Docker caches this layer — if requirements.txt hasn't changed,
# it won't reinstall packages on every build. Big time saver.
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
# Start fresh from a clean slim image — no build tools, smaller attack surface.
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy only the installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY app/ ./app/

# Create a non-root user — running as root in a container is a security risk
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port FastAPI runs on
EXPOSE 8080

# Health check — Docker and ECS use this to know if the container is alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/api/v1/health').raise_for_status()"

# Start the app
# - host 0.0.0.0 makes it accessible from outside the container
# - workers 2 is a safe default; tune based on CPU in production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]