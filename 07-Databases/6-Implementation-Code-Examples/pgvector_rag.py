"""
pgvector_rag.py
A minimal-but-realistic RAG retrieval layer on PostgreSQL + pgvector.

WHY this file:
    Shows the *data* side of RAG done right -- parameterized inserts, an HNSW
    similarity query that combines a metadata filter with vector search (hybrid),
    and the query-time recall knob (hnsw.ef_search). No LLM call is required to
    understand the database patterns.

Prereqs:
    - Run pgvector_setup.sql against your database first.
    - pip install "psycopg[binary]" pgvector numpy
    - export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"

NOTE: `fake_embed` returns a deterministic pseudo-embedding so the file runs
without an API key. Swap it for a real model in production (see the bottom).
"""

from __future__ import annotations

import hashlib
import os
from typing import Sequence

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

EMBED_DIM = 1536  # MUST match the VECTOR(1536) column and your real model.


def fake_embed(text: str) -> np.ndarray:
    """Deterministic placeholder embedding.

    WHY: lets the demo run offline and reproducibly. We seed a RNG from a hash
    of the text so the same text always maps to the same vector, and we
    L2-normalize because cosine distance assumes unit-length vectors.
    """
    seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    vec = rng.standard_normal(EMBED_DIM).astype(np.float32)
    vec /= np.linalg.norm(vec) + 1e-12  # normalize -> cosine == dot product
    return vec


def connect() -> psycopg.Connection:
    """Open a connection and register the pgvector type adapter.

    WHY register_vector: without it, psycopg doesn't know how to send/receive
    the `vector` type, and you'd have to hand-format strings (error-prone).
    In production you'd get this connection from a pool (PgBouncer / a pool lib)
    rather than opening one per request.
    """
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    register_vector(conn)
    return conn


def ingest(conn: psycopg.Connection, tenant_id: int, source: str,
           chunks: Sequence[str]) -> None:
    """Insert document chunks + embeddings.

    WHY executemany with %s placeholders: parameterized queries prevent SQL
    injection AND let the driver batch the round-trips. We NEVER build SQL by
    string concatenation with user content.
    """
    rows = [
        (tenant_id, source, i, chunk, fake_embed(chunk))
        for i, chunk in enumerate(chunks)
    ]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO documents (tenant_id, source, chunk_index, content, embedding)
            VALUES (%s, %s, %s, %s, %s)
            """,
            rows,
        )
    conn.commit()


def search(conn: psycopg.Connection, tenant_id: int, query: str,
           k: int = 5, ef_search: int = 100) -> list[tuple[int, str, float]]:
    """Hybrid retrieval: tenant filter + vector similarity, top-k.

    WHY SET hnsw.ef_search: this is the query-time recall/latency dial. Higher
    means the HNSW graph is explored more thoroughly (better recall, slower).
    We set it per-transaction so different query paths can use different SLAs.

    WHY `1 - (embedding <=> q)`: `<=>` is cosine *distance* (0 = identical),
    so `1 - distance` gives an intuitive similarity score in [0, 1] for logging.
    """
    q = fake_embed(query)
    with conn.cursor() as cur:
        cur.execute("SET LOCAL hnsw.ef_search = %s", (ef_search,))
        cur.execute(
            """
            SELECT id, content, 1 - (embedding <=> %s) AS similarity
            FROM documents
            WHERE tenant_id = %s          -- structured pre-filter
            ORDER BY embedding <=> %s     -- nearest neighbors first
            LIMIT %s
            """,
            (q, tenant_id, q, k),
        )
        return cur.fetchall()


if __name__ == "__main__":
    # Tiny end-to-end demo. Requires a live DB with pgvector_setup.sql applied.
    with connect() as conn:
        ingest(
            conn,
            tenant_id=7,
            source="handbook.md",
            chunks=[
                "Employees accrue 20 vacation days per year.",
                "Reimbursements are processed within 14 business days.",
                "The office is closed on national public holidays.",
            ],
        )
        results = search(conn, tenant_id=7, query="How much paid leave do I get?")
        for doc_id, content, sim in results:
            print(f"[{sim:.3f}] #{doc_id}: {content}")

# ---------------------------------------------------------------------------
# Swapping in real embeddings (production):
#
#   from openai import OpenAI
#   client = OpenAI()
#   def embed(text: str) -> list[float]:
#       resp = client.embeddings.create(model="text-embedding-3-small", input=text)
#       return resp.data[0].embedding   # length 1536 -> matches VECTOR(1536)
#
# Keep EMBED_DIM, the column type, and the model output dimension in lockstep.
# Changing embedding models means re-embedding + rebuilding the HNSW index.
# ---------------------------------------------------------------------------
