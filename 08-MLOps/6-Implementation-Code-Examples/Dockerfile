# Dockerfile — production-shaped container for the model service.
#
# WHY CONTAINERIZE: package model + code + exact deps so it runs identically on
# a laptop, in CI, and in production. Kills "works on my machine" bugs.

# Pin a specific slim base — WHY: reproducible builds + smaller attack surface.
FROM python:3.11-slim AS base

# WHY: don't buffer stdout (logs appear immediately) and don't write .pyc.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# --- Dependency layer -------------------------------------------------------
# WHY: copy ONLY requirements first. Docker caches this layer, so changing app
# code doesn't re-run pip install (much faster rebuilds).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Application layer -------------------------------------------------------
COPY . .

# WHY: run as a non-root user — least privilege limits blast radius if the
# container is compromised.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# WHY: a container-level healthcheck lets orchestrators detect a hung process
# even if the port is open. Kubernetes probes usually supersede this, but it's
# good defense-in-depth for plain Docker/Compose.
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; \
    sys.exit(0) if urllib.request.urlopen('http://localhost:8000/health').status==200 else sys.exit(1)"

# WHY: one process per container; let the orchestrator scale replicas.
CMD ["uvicorn", "fastapi_model_serving:app", "--host", "0.0.0.0", "--port", "8000"]
