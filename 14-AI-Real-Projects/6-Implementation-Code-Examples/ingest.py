"""
ingest.py — the OFFLINE half of a Chat-with-your-PDF RAG app.

WHY this file exists separately from the query code:
    Ingestion is expensive (parse + embed) and only needs to run when documents
    change. Splitting "index once" from "query many times" mirrors how real RAG
    systems work: a batch/async ingestion pipeline feeds a vector store that the
    online query path reads from. Keeping them separate is the first production
    instinct an interviewer looks for.

WHAT it does:
    PDF file(s) -> extract text -> chunk with overlap -> embed -> save a FAISS
    index + the chunk metadata to disk.

Run:
    python ingest.py path/to/document.pdf
    python ingest.py doc1.pdf doc2.pdf        # multiple files, one shared index
"""

from __future__ import annotations

import os
import sys
import json
import pickle
from dataclasses import dataclass, asdict

import numpy as np
import faiss
import tiktoken
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # WHY: read OPENAI_API_KEY from .env, never hard-code secrets.

# --- Configuration -----------------------------------------------------------
# WHY these defaults: small, cheap embedding model + modest chunks are a sane
# starting point. The RIGHT values come from tuning against an eval set — these
# are just a defensible default, not a magic number.
EMBED_MODEL = "text-embedding-3-small"   # cheap, good enough to start
CHUNK_TOKENS = 350                       # ~1-2 paragraphs of context
CHUNK_OVERLAP = 60                       # overlap so ideas crossing a boundary survive
INDEX_PATH = "index.faiss"
META_PATH = "chunks.pkl"

client = OpenAI()  # reads OPENAI_API_KEY from the environment
_enc = tiktoken.get_encoding("cl100k_base")  # token counter matching the models


@dataclass
class Chunk:
    """One retrievable unit. We keep source + page so we can CITE the answer.
    Citations are what turn a toy demo into something an interviewer trusts."""
    text: str
    source: str
    page: int


def extract_pages(pdf_path: str) -> list[tuple[int, str]]:
    """Return (page_number, text) pairs. WHY track page: citations need it."""
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:  # skip blank/image-only pages
            pages.append((i + 1, text))
    return pages


def chunk_text(text: str, source: str, page: int) -> list[Chunk]:
    """Split into token-sized windows with overlap.

    WHY token-based (not character-based): models think in tokens, and context
    limits + cost are measured in tokens. Chunking on tokens keeps each piece
    within a predictable budget. Overlap prevents a fact that straddles a
    boundary from being cut in half and lost to retrieval.
    """
    tokens = _enc.encode(text)
    chunks: list[Chunk] = []
    step = CHUNK_TOKENS - CHUNK_OVERLAP  # advance less than a full window => overlap
    for start in range(0, len(tokens), step):
        window = tokens[start : start + CHUNK_TOKENS]
        if not window:
            break
        chunks.append(Chunk(text=_enc.decode(window), source=source, page=page))
        if start + CHUNK_TOKENS >= len(tokens):
            break
    return chunks


def embed_batch(texts: list[str]) -> np.ndarray:
    """Embed many texts in ONE call.

    WHY batch: network round-trips dominate cost/latency at scale. Batching is
    the single easiest throughput win when indexing large corpora.
    """
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    vecs = [d.embedding for d in resp.data]
    arr = np.array(vecs, dtype="float32")
    # WHY normalize: we use inner-product search below; on normalized vectors
    # inner product == cosine similarity, the standard semantic distance.
    faiss.normalize_L2(arr)
    return arr


def build_index(pdf_paths: list[str]) -> None:
    all_chunks: list[Chunk] = []
    for path in pdf_paths:
        source = os.path.basename(path)
        for page_no, page_text in extract_pages(path):
            all_chunks.extend(chunk_text(page_text, source, page_no))

    if not all_chunks:
        print("No extractable text found. Is this a scanned/image-only PDF?")
        sys.exit(1)

    print(f"Chunked into {len(all_chunks)} pieces. Embedding...")

    # Embed in batches to stay under request-size limits and keep throughput high.
    vectors = []
    BATCH = 64
    for i in range(0, len(all_chunks), BATCH):
        batch_texts = [c.text for c in all_chunks[i : i + BATCH]]
        vectors.append(embed_batch(batch_texts))
    matrix = np.vstack(vectors)

    # WHY IndexFlatIP for a demo: exact search, zero tuning, correct results.
    # In production with millions of vectors you'd switch to an ANN index
    # (e.g. HNSW) and trade a little recall for big speed/memory gains.
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)

    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump([asdict(c) for c in all_chunks], f)

    print(f"Saved index -> {INDEX_PATH} and metadata -> {META_PATH}")
    print(f"Indexed {len(all_chunks)} chunks from {len(pdf_paths)} file(s).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <file1.pdf> [file2.pdf ...]")
        sys.exit(1)
    build_index(sys.argv[1:])
