"""
fastapi_model_server.py
======================

A compact but production-minded model-serving API. It demonstrates the patterns
interviewers look for:

  1) LOAD THE MODEL ONCE at startup (via lifespan), keep it in memory for the whole
     process. Loading per-request would add huge latency and waste memory.
  2) DON'T BLOCK THE EVENT LOOP: inference is CPU/GPU-bound and often synchronous, so
     we offload it with asyncio.to_thread. One blocking call would freeze EVERY
     concurrent request (asyncio is single-threaded).
  3) VALIDATE INPUT at the boundary with Pydantic (security + reliability): reject
     malformed/oversized requests before they reach the model.
  4) STREAM tokens with a StreamingResponse for better perceived latency.
  5) Expose a health endpoint for load balancers / readiness probes.

Run:  uvicorn fastapi_model_server:app --reload
Test: curl -s -X POST localhost:8000/generate -H 'content-type: application/json' \
           -d '{"prompt":"hello world","max_tokens":8}'
      curl -N -X POST localhost:8000/stream   -H 'content-type: application/json' \
           -d '{"prompt":"stream me some tokens"}'
"""
from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# A stand-in for a real model. In reality this would be a transformer, an ONNX
# session, or a client to a GPU inference server (e.g., vLLM). We simulate a
# SYNCHRONOUS, somewhat slow predict() to represent CPU/GPU-bound work.
# ---------------------------------------------------------------------------
class FakeModel:
    def __init__(self) -> None:
        # Pretend loading weights is expensive — this is exactly why we do it ONCE.
        time.sleep(0.2)
        self.ready = True

    def predict(self, prompt: str, max_tokens: int) -> str:
        # Simulate blocking compute. In async code this MUST be offloaded, not awaited
        # directly, or it will stall the event loop for every other request.
        time.sleep(0.05)
        words = (prompt.split() or ["<empty>"])
        # Deterministic "generation": echo/repeat words up to max_tokens.
        out = [words[i % len(words)] for i in range(max_tokens)]
        return " ".join(out)


# A tiny container for process-wide state (the loaded model).
STATE: dict[str, FakeModel] = {}


# ---------------------------------------------------------------------------
# lifespan: runs code at startup (before serving) and shutdown (after). This is
# the correct place to load models, open pools, and warm caches — ONCE per process.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    STATE["model"] = FakeModel()          # loaded once, reused across all requests
    # (Optionally pre-warm here to avoid a cold first request.)
    yield
    STATE.clear()                          # release resources on shutdown


app = FastAPI(title="Model Server Example", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Request schema. Pydantic enforces these constraints at the edge:
#   - prompt length is bounded (prevents abuse / runaway cost)
#   - max_tokens is bounded (bounds compute + response size => DoS protection)
# Invalid requests get an automatic, structured 422 response.
# ---------------------------------------------------------------------------
class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    max_tokens: int = Field(16, gt=0, le=512)


class GenerateResponse(BaseModel):
    text: str
    latency_ms: float


@app.get("/health")
async def health() -> dict:
    # Load balancers / k8s probes hit this. Report NOT ready until the model is loaded.
    model = STATE.get("model")
    if not model or not getattr(model, "ready", False):
        raise HTTPException(status_code=503, detail="model not ready")
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    model = STATE["model"]
    start = time.perf_counter()
    # Offload the blocking predict() to a worker thread so the event loop stays free
    # to accept and progress other concurrent requests.
    text = await asyncio.to_thread(model.predict, req.prompt, req.max_tokens)
    latency_ms = (time.perf_counter() - start) * 1000
    return GenerateResponse(text=text, latency_ms=round(latency_ms, 2))


# ---------------------------------------------------------------------------
# Streaming endpoint. Instead of waiting for the full answer, we yield tokens as
# they are produced. This dramatically improves PERCEIVED latency for LLM UIs.
# We use an async generator; each yielded chunk is flushed to the client.
# ---------------------------------------------------------------------------
async def token_stream(prompt: str) -> AsyncIterator[bytes]:
    for word in prompt.split():
        # Simulate the model producing one token at a time. asyncio.sleep keeps this
        # non-blocking so other requests continue to be served concurrently.
        await asyncio.sleep(0.05)
        yield f"data: {word}\n\n".encode()   # Server-Sent Events (SSE) format
    yield b"data: [DONE]\n\n"


@app.post("/stream")
async def stream(req: GenerateRequest) -> StreamingResponse:
    # media_type text/event-stream tells clients this is an SSE stream.
    return StreamingResponse(token_stream(req.prompt), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Production notes (would-be next steps, kept out of this teaching example):
#   - Run multiple Uvicorn/Gunicorn workers behind a load balancer.
#   - Move real GPU inference to a separate worker pool + queue with dynamic batching.
#   - Add auth (API key/JWT), per-tenant rate limiting, request IDs, structured logs.
#   - Emit p50/p95/p99 latency metrics; add timeouts and circuit breakers on deps.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
