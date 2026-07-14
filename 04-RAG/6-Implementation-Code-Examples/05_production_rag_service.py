"""
05 — Production-style RAG service (FastAPI).

Demonstrates the production concerns interviewers care about:
  - Multi-tenant SECURITY via ACL pre-filtering inside the query
  - Semantic CACHE to cut latency + LLM cost on repeated/similar queries
  - STREAMING responses (SSE) for low perceived latency
  - CITATIONS for trust/auditability

This is a teaching scaffold: swap the in-memory stores for a real vector DB
(Pinecone/Qdrant/pgvector) and Redis for the cache in production.

Run:   uvicorn 05_production_rag_service:app --reload
Needs: OPENAI_API_KEY + fastapi, uvicorn, numpy
"""
from __future__ import annotations

import numpy as np
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()
app = FastAPI()

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
CACHE_THRESHOLD = 0.95  # cosine similarity above which we reuse a cached answer


# ---- fake vector store: each doc carries a tenant_id for access control ----
DOCS = [
    {"text": "Acme refund policy: 30-day returns.", "tenant_id": "acme"},
    {"text": "Globex refund policy: 14-day returns.", "tenant_id": "globex"},
]


def embed(texts: list[str]) -> np.ndarray:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return np.array([d.embedding for d in resp.data])


DOC_VECS = embed([d["text"] for d in DOCS])
SEMANTIC_CACHE: list[tuple[np.ndarray, str]] = []  # (query_vec, answer)


def cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a / np.linalg.norm(a, axis=1, keepdims=True)
    b = b / np.linalg.norm(b, axis=1, keepdims=True)
    return a @ b.T


def retrieve(query_vec: np.ndarray, tenant_id: str, k: int = 3) -> list[str]:
    """SECURITY: pre-filter by tenant BEFORE similarity search.
    Never let one tenant retrieve another tenant's documents."""
    allowed = [i for i, d in enumerate(DOCS) if d["tenant_id"] == tenant_id]
    if not allowed:
        return []
    sims = cosine(query_vec, DOC_VECS[allowed])[0]
    order = np.argsort(sims)[::-1][:k]
    return [DOCS[allowed[i]]["text"] for i in order]


def check_cache(query_vec: np.ndarray) -> str | None:
    """Return a cached answer if a very similar query was seen before."""
    for cached_vec, answer in SEMANTIC_CACHE:
        if cosine(query_vec, cached_vec[None, :])[0][0] >= CACHE_THRESHOLD:
            return answer
    return None


class Query(BaseModel):
    question: str
    tenant_id: str


@app.post("/ask")
def ask(q: Query):
    qvec = embed([q.question])
    cached = check_cache(qvec[0])
    if cached:
        return {"answer": cached, "cached": True}

    contexts = retrieve(qvec, q.tenant_id)
    context_block = "\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": "Answer only from context. Cite [n]."},
            {"role": "user", "content": f"Context:\n{context_block}\n\nQ: {q.question}"},
        ],
    )
    answer = resp.choices[0].message.content
    SEMANTIC_CACHE.append((qvec[0], answer))
    return {"answer": answer, "sources": contexts, "cached": False}


@app.post("/ask/stream")
def ask_stream(q: Query):
    """Stream tokens for low perceived latency."""
    qvec = embed([q.question])
    contexts = retrieve(qvec, q.tenant_id)
    context_block = "\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))

    def token_stream():
        stream = client.chat.completions.create(
            model=CHAT_MODEL,
            temperature=0,
            stream=True,
            messages=[
                {"role": "system", "content": "Answer only from context. Cite [n]."},
                {"role": "user", "content": f"Context:\n{context_block}\n\nQ: {q.question}"},
            ],
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    return StreamingResponse(token_stream(), media_type="text/event-stream")
