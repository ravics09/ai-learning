"""
embeddings_similarity.py
========================
The absolute foundation: turn text into vectors and compare them with the three
similarity metrics (cosine, dot product, Euclidean/L2).

WHY this file exists:
- Before you touch any index, you must internalize that "similarity == geometry".
- The single most common bug in vector search is using the wrong metric or forgetting
  to normalize. This file makes those effects visible.

Run:
    python embeddings_similarity.py

It uses sentence-transformers if available (real embeddings); otherwise it falls back to
deterministic random vectors so the script still runs with numpy only.
"""

from __future__ import annotations
import numpy as np


# ---------------------------------------------------------------------------
# 1. Get embeddings. Real model if available, else a deterministic fallback.
# ---------------------------------------------------------------------------
def get_embedder():
    try:
        from sentence_transformers import SentenceTransformer

        # bge-small is cosine-trained and only 384-dim => fast and cheap.
        model = SentenceTransformer("BAAI/bge-small-en-v1.5")

        def embed(texts, normalize=True):
            # WHY normalize=True: unit vectors make dot product == cosine similarity,
            # which is what this model was trained for.
            return np.asarray(
                model.encode(list(texts), normalize_embeddings=normalize),
                dtype="float32",
            )

        return embed, "sentence-transformers (bge-small)"
    except Exception:
        # Fallback: hash each text to a seed so "same text => same vector" (deterministic).
        def embed(texts, normalize=True):
            out = []
            for t in texts:
                rng = np.random.default_rng(abs(hash(t)) % (2**32))
                v = rng.standard_normal(384).astype("float32")
                if normalize:
                    v /= np.linalg.norm(v) + 1e-12
                out.append(v)
            return np.vstack(out)

        return embed, "random fallback (install sentence-transformers for real vectors)"


# ---------------------------------------------------------------------------
# 2. The three metrics, written out so the math is explicit.
# ---------------------------------------------------------------------------
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    # Angle only: divides out magnitude. Range [-1, 1], higher = more similar.
    return float(np.dot(a, b) / ((np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12))


def dot_product(a: np.ndarray, b: np.ndarray) -> float:
    # Magnitude-sensitive. On normalized vectors this equals cosine.
    return float(np.dot(a, b))


def l2_distance(a: np.ndarray, b: np.ndarray) -> float:
    # Straight-line distance. LOWER = more similar (opposite direction to the others).
    return float(np.linalg.norm(a - b))


def main() -> None:
    embed, backend = get_embedder()
    print(f"Embedding backend: {backend}\n")

    texts = [
        "a fluffy dog resting on a sofa",   # 0
        "a canine sleeping on a couch",     # 1  (paraphrase of 0)
        "quarterly revenue grew 12 percent",  # 2 (unrelated)
    ]
    vecs = embed(texts, normalize=True)  # normalized => cosine == dot

    print("Pairwise scores (query = text 0: 'a fluffy dog resting on a sofa'):")
    print(f"{'candidate':<40}{'cosine':>10}{'dot':>10}{'L2 (↓ better)':>16}")
    for i in (1, 2):
        c = cosine_similarity(vecs[0], vecs[i])
        d = dot_product(vecs[0], vecs[i])
        l = l2_distance(vecs[0], vecs[i])
        print(f"{texts[i]:<40}{c:>10.4f}{d:>10.4f}{l:>16.4f}")

    # WHY this matters: the paraphrase (text 1) should score HIGHER cosine/dot and LOWER
    # L2 than the unrelated sentence (text 2). If it doesn't, your embeddings or metric
    # are wrong — debug that before blaming the index.

    # ---------------------------------------------------------------------
    # 3. Demonstrate the normalization gotcha with dot product.
    # ---------------------------------------------------------------------
    print("\nWhy normalization matters for dot product:")
    a = np.array([1.0, 0.0], dtype="float32")
    b = np.array([0.9, 0.1], dtype="float32")      # very similar direction
    hub = np.array([10.0, 10.0], dtype="float32")  # long 'hub' vector, different direction

    print(f"  dot(a, b)   = {dot_product(a, b):.3f}  (similar direction, correct)")
    print(f"  dot(a, hub) = {dot_product(a, hub):.3f}  (wrong winner: long vector dominates)")
    print(f"  cosine(a,b) = {cosine_similarity(a, b):.3f}  vs cosine(a,hub) = "
          f"{cosine_similarity(a, hub):.3f}  (cosine picks the right one)")
    # Lesson: on UNnormalized vectors, dot product can be hijacked by long 'hub' vectors.
    # Normalize on ingest, or use cosine.


if __name__ == "__main__":
    main()
