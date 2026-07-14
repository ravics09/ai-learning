"""
embeddings_compare.py
=====================
WHY THIS FILE:
    Embeddings are the backbone of RAG and semantic search — but they are NOT generative,
    and choosing one is a real trade-off (quality vs dimension vs cost vs privacy).
    This script:
        1) embeds a few sentences with a local open model (no API key, private),
        2) computes cosine similarity to show semantic closeness,
        3) demonstrates the retrieval step (query -> nearest documents),
        4) optionally compares against an API embedding model.

    Takeaway for interviews: you must use the SAME model for indexing and querying, and you
    should benchmark on YOUR data — leaderboards are only a starting filter.

SETUP:
    pip install sentence-transformers numpy
    # optional API comparison:  pip install openai ; export OPENAI_API_KEY=...

RUN:
    python embeddings_compare.py
"""

from __future__ import annotations

import os

import numpy as np
from sentence_transformers import SentenceTransformer


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity = how aligned two vectors are (1.0 = identical direction).

    WHY cosine and not raw distance: embeddings encode *direction* (meaning); magnitude is
    mostly noise, so we normalize it out.
    """
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def demo_local_embeddings() -> None:
    """Embed with a small, fast, open model that runs locally."""
    # bge-small / all-MiniLM are tiny (384-dim) yet strong — good default for local RAG.
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    docs = [
        "vLLM uses PagedAttention for high-throughput serving.",
        "Ollama makes running open-weight models locally simple.",
        "Diffusion models generate images by removing noise.",
        "The capital of France is Paris.",
    ]
    # normalize_embeddings=True lets us treat similarity as a plain dot product later.
    doc_vecs = model.encode(docs, normalize_embeddings=True)
    print(f"Local model dim = {doc_vecs.shape[1]}  (smaller dim = cheaper storage/search)\n")

    query = "How do I serve a lot of requests fast on a GPU?"
    q_vec = model.encode(query, normalize_embeddings=True)

    # Retrieval = rank documents by similarity to the query. This is the heart of RAG.
    scored = sorted(
        ((cosine(q_vec, dv), d) for dv, d in zip(doc_vecs, docs)),
        reverse=True,
    )
    print(f"Query: {query}\nMost relevant documents:")
    for score, doc in scored:
        print(f"  {score:.3f}  {doc}")


def demo_api_embeddings() -> None:
    """Optional: compare against a hosted embedding model.

    WHY compare: API models often score higher and offer huge context, but cost per token
    and send your data off-box. Weigh that against local privacy + zero marginal cost.
    """
    if not os.getenv("OPENAI_API_KEY"):
        print("\n(Set OPENAI_API_KEY to compare against a hosted embedding model.)")
        return

    from openai import OpenAI

    client = OpenAI()
    # dimensions=256 uses Matryoshka truncation: shrink vectors without a new model,
    # trading a little accuracy for cheaper storage and faster search.
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input="How do I serve a lot of requests fast on a GPU?",
        dimensions=256,
    )
    print(f"\nAPI embedding dim = {len(resp.data[0].embedding)} (Matryoshka-truncated to 256)")


if __name__ == "__main__":
    print("[1] Local open embeddings + retrieval demo:\n")
    demo_local_embeddings()
    print("\n[2] Optional hosted-embedding comparison:")
    demo_api_embeddings()
