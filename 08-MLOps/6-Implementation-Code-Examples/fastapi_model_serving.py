"""
fastapi_model_serving.py
========================
A production-shaped online inference service.

WHY THIS MATTERS
----------------
Serving is where models meet reality. A good serving layer needs:
  - Input VALIDATION (bad input should 422, not crash the model).
  - A HEALTH endpoint so Kubernetes only routes traffic to ready pods.
  - METRICS (latency tail + errors) so you can alert and autoscale.
  - VERSION reporting so you always know which model answered.

Run:
    uvicorn fastapi_model_serving:app --host 0.0.0.0 --port 8000
Try:
    curl -X POST localhost:8000/predict -H 'content-type: application/json' \
         -d '{"features": [0.1, 1.2, -0.3, 4.0]}'
    curl localhost:8000/health
    curl localhost:8000/metrics
"""
from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

MODEL_VERSION = os.getenv("MODEL_VERSION", "v8")
EXPECTED_FEATURES = 4

# --- Metrics: track the tail, not just the average ------------------------
# WHY: users feel p95/p99 latency; averages hide spikes.
LATENCY = Histogram(
    "inference_latency_seconds",
    "Prediction latency",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)
REQUESTS = Counter("inference_requests_total", "Total prediction requests")
ERRORS = Counter("inference_errors_total", "Total prediction errors")

_model = {"ready": False}  # simulated model handle


@asynccontextmanager
async def lifespan(app: FastAPI):
    # WHY: loading a model can take seconds-to-minutes; do it once at startup,
    # and only flip "ready" when done so the readiness probe gates traffic.
    time.sleep(0.2)  # pretend to load weights
    _model["ready"] = True
    yield
    _model["ready"] = False


app = FastAPI(title="Model Serving", version=MODEL_VERSION, lifespan=lifespan)


class PredictRequest(BaseModel):
    # WHY: pydantic validates shape/type at the edge -> bad input returns 422,
    # the model never sees garbage, and errors are clear to callers.
    features: list[float] = Field(..., min_length=EXPECTED_FEATURES,
                                  max_length=EXPECTED_FEATURES)


class PredictResponse(BaseModel):
    prediction: float
    model_version: str


def _run_model(features: list[float]) -> float:
    # Placeholder for a real model.predict(); deterministic for demo.
    return round(sum(features) / len(features), 4)


@app.get("/health")
def health():
    # WHY: readiness/liveness probe target. 503 until the model is loaded so
    # Kubernetes doesn't route traffic to a pod that can't serve yet.
    if not _model["ready"]:
        raise HTTPException(status_code=503, detail="model not ready")
    return {"status": "ok", "model_version": MODEL_VERSION}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    REQUESTS.inc()
    start = time.perf_counter()
    try:
        pred = _run_model(req.features)
        return PredictResponse(prediction=pred, model_version=MODEL_VERSION)
    except Exception:
        ERRORS.inc()  # WHY: alert on error-rate spikes; drives auto-rollback
        raise HTTPException(status_code=500, detail="inference failed")
    finally:
        LATENCY.observe(time.perf_counter() - start)


@app.get("/metrics")
def metrics():
    # WHY: Prometheus scrapes this; Grafana dashboards + alerts + HPA build on it.
    return PlainTextResponse(generate_latest())
