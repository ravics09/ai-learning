"""
01 — Basic RAG pipeline (the skeleton every RAG system starts from).

Flow:  chunk -> embed -> store -> retrieve -> generate

Run:   python 01_basic_rag.py
Needs: OPENAI_API_KEY
"""
from __future__ import annotations

import chromadb
from openai import OpenAI

client = OpenAI()

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"


# ---------- 1. Chunking ----------
def chunk_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    """Very simple character chunker with overlap.

    In production use a token-aware, structure-aware splitter
    (e.g. RecursiveCharacterTextSplitter). Overlap preserves context
    that would otherwise be cut at a boundary.
    """
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap  # step back by `overlap`
    return chunks


# ---------- 2. Embedding ----------
def embed(texts: list[str]) -> list[list[float]]:
    """Turn text into vectors. Same model MUST be used for docs and queries."""
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


# ---------- 3. Index ----------
def build_index(documents: list[str]):
    """Store chunks + embeddings in an in-memory Chroma collection."""
    db = chromadb.Client()
    col = db.create_collection("docs")

    all_chunks, metadatas, ids = [], [], []
    for doc_id, doc in enumerate(documents):
        for i, ch in enumerate(chunk_text(doc)):
            all_chunks.append(ch)
            metadatas.append({"doc_id": doc_id})
            ids.append(f"{doc_id}-{i}")

    col.add(
        documents=all_chunks,
        embeddings=embed(all_chunks),
        metadatas=metadatas,
        ids=ids,
    )
    return col


# ---------- 4. Retrieve ----------
def retrieve(col, query: str, k: int = 4) -> list[str]:
    """Embed the query and fetch the k most similar chunks."""
    res = col.query(query_embeddings=embed([query]), n_results=k)
    return res["documents"][0]


# ---------- 5. Generate ----------
def generate(query: str, contexts: list[str]) -> str:
    """Ground the model in retrieved context and force honesty + citations."""
    context_block = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    system = (
        "Answer ONLY using the context. If the answer is not in the context, "
        "say 'I don't have that information.' Cite sources like [1], [2]."
    )
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,  # factual task -> deterministic
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Context:\n{context_block}\n\nQuestion: {query}"},
        ],
    )
    return resp.choices[0].message.content


def rag_answer(col, query: str) -> str:
    contexts = retrieve(col, query)
    return generate(query, contexts)


if __name__ == "__main__":
    docs = [
        "Our refund policy allows returns within 30 days of purchase with a receipt. "
        "Digital goods are non-refundable once downloaded.",
        "The Enterprise plan costs $99/user/month and includes SSO, audit logs, "
        "and priority support with a 1-hour SLA.",
    ]
    collection = build_index(docs)
    print(rag_answer(collection, "How long do I have to return something?"))
    print("---")
    print(rag_answer(collection, "What is included in the Enterprise plan?"))
