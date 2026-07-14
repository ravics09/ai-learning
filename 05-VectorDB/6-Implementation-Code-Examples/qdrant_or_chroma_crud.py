"""
qdrant_or_chroma_crud.py
========================
End-to-end CRUD against a REAL vector database, using an in-memory / embedded instance so
it runs with zero external services. Shows the full lifecycle every RAG app needs:

    create collection -> upsert (with metadata) -> filtered search -> update -> delete

WHY this file exists:
- The FAISS examples show the raw algorithm; this shows the DATABASE ergonomics:
  payloads/metadata, filtered queries, upsert-by-id, and deletes — the operations you
  actually call in production.
- It prefers Qdrant (great filtering) and falls back to Chroma, then to a tiny numpy
  stand-in, so it always runs and teaches the same mental model.

Run:
    python qdrant_or_chroma_crud.py
"""

from __future__ import annotations
import numpy as np

rng = np.random.default_rng(0)
DIM = 8

# Toy dataset: (id, vector, payload). Payload = the metadata you filter on.
ITEMS = [
    (1, "wireless noise-cancelling headphones", {"category": "audio", "price": 299}),
    (2, "bluetooth portable speaker",           {"category": "audio", "price": 89}),
    (3, "mechanical keyboard rgb",              {"category": "input", "price": 120}),
    (4, "ergonomic wireless mouse",             {"category": "input", "price": 59}),
    (5, "usb-c fast charger",                   {"category": "power", "price": 25}),
]


def toy_vec(text: str) -> list[float]:
    # Deterministic pseudo-embedding so "same text => same vector".
    r = np.random.default_rng(abs(hash(text)) % (2**32))
    v = r.standard_normal(DIM).astype("float32")
    v /= np.linalg.norm(v) + 1e-12
    return v.tolist()


def run_qdrant() -> bool:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import (
            Distance, VectorParams, PointStruct,
            Filter, FieldCondition, Range,
        )
    except Exception:
        return False

    # location=":memory:" => embedded, no server needed. WHY: reproducible demo.
    client = QdrantClient(location=":memory:")
    name = "products"

    # CREATE: declare dimension + distance metric up front (Cosine for text similarity).
    client.recreate_collection(
        collection_name=name,
        vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
    )

    # UPSERT: insert-or-replace by id, attaching payload (metadata) to each point.
    client.upsert(
        collection_name=name,
        points=[
            PointStruct(id=i, vector=toy_vec(text), payload=payload)
            for (i, text, payload) in ITEMS
        ],
    )

    # SEARCH + FILTER: nearest neighbors to "audio" items priced under 150.
    # The filter is pushed into the ANN traversal (efficient pre-filtering in Qdrant).
    hits = client.search(
        collection_name=name,
        query_vector=toy_vec("portable music player"),
        query_filter=Filter(
            must=[
                FieldCondition(key="category", match={"value": "audio"}),
                FieldCondition(key="price", range=Range(lte=150)),
            ]
        ),
        limit=3,
    )
    print("[Qdrant] filtered search (audio, price<=150):")
    for h in hits:
        print(f"   id={h.id} score={h.score:.3f} payload={h.payload}")

    # UPDATE: upserting the same id replaces the vector/payload.
    client.upsert(
        collection_name=name,
        points=[PointStruct(id=2, vector=toy_vec("bluetooth speaker PRO"),
                            payload={"category": "audio", "price": 149})],
    )
    # DELETE by id.
    client.delete(collection_name=name, points_selector=[5])
    remaining = client.count(collection_name=name).count
    print(f"[Qdrant] after update id=2 and delete id=5, count={remaining}")
    return True


def run_chroma() -> bool:
    try:
        import chromadb
    except Exception:
        return False

    client = chromadb.EphemeralClient()  # in-memory
    col = client.create_collection("products", metadata={"hnsw:space": "cosine"})

    # Chroma stores ids as strings; documents + metadatas + embeddings together.
    col.add(
        ids=[str(i) for i, _, _ in ITEMS],
        embeddings=[toy_vec(t) for _, t, _ in ITEMS],
        metadatas=[p for _, _, p in ITEMS],
        documents=[t for _, t, _ in ITEMS],
    )
    res = col.query(
        query_embeddings=[toy_vec("portable music player")],
        n_results=3,
        where={"category": "audio"},  # metadata filter
    )
    print("[Chroma] filtered search (category=audio):")
    for _id, doc, dist in zip(res["ids"][0], res["documents"][0], res["distances"][0]):
        print(f"   id={_id} distance={dist:.3f} doc={doc!r}")
    col.delete(ids=["5"])  # DELETE by id
    print(f"[Chroma] after delete id=5, count={col.count()}")
    return True


def run_numpy_fallback() -> None:
    # Last-resort stand-in so the file always demonstrates the mental model.
    print("[fallback] No vector DB installed; using a numpy stand-in.")
    ids = [i for i, _, _ in ITEMS]
    mat = np.vstack([toy_vec(t) for _, t, _ in ITEMS])
    meta = {i: p for i, _, p in ITEMS}
    q = np.asarray(toy_vec("portable music player"))
    scores = mat @ q
    # Pre-filter to audio, then rank.
    audio = [j for j, i in enumerate(ids) if meta[i]["category"] == "audio"]
    ranked = sorted(audio, key=lambda j: -scores[j])[:3]
    print("[fallback] filtered search (category=audio):")
    for j in ranked:
        print(f"   id={ids[j]} score={scores[j]:.3f} payload={meta[ids[j]]}")


def main() -> None:
    print("Trying real vector DBs (embedded / in-memory)...\n")
    if run_qdrant():
        return
    if run_chroma():
        return
    run_numpy_fallback()
    print("\nInstall a real DB to see production ergonomics: "
          "pip install qdrant-client   (or)   pip install chromadb")


if __name__ == "__main__":
    main()
