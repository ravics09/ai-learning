"""
02 — Hybrid search + Reciprocal Rank Fusion + cross-encoder reranking.

This is the "why naive RAG isn't enough" upgrade:
  - Dense search understands MEANING but misses exact terms (SKUs, codes).
  - BM25 (sparse) nails exact terms but misses paraphrases.
  - Fuse them with RRF, then a cross-encoder reranks for precision.

Run:   python 02_hybrid_search_rerank.py
Needs: OPENAI_API_KEY  (+ sentence-transformers, rank-bm25)
"""
from __future__ import annotations

import numpy as np
from openai import OpenAI
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

client = OpenAI()
EMBED_MODEL = "text-embedding-3-small"

# Cross-encoder reads (query, doc) TOGETHER -> far better relevance than
# the bi-encoder used for first-stage retrieval. Runs only on a shortlist.
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def embed(texts: list[str]) -> np.ndarray:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return np.array([d.embedding for d in resp.data])


def cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a / np.linalg.norm(a, axis=1, keepdims=True)
    b = b / np.linalg.norm(b, axis=1, keepdims=True)
    return a @ b.T


class HybridRetriever:
    def __init__(self, docs: list[str]):
        self.docs = docs
        self.doc_vecs = embed(docs)                       # dense index
        self.bm25 = BM25Okapi([d.lower().split() for d in docs])  # sparse index

    def dense(self, query: str, n: int) -> list[int]:
        scores = cosine(embed([query]), self.doc_vecs)[0]
        return list(np.argsort(scores)[::-1][:n])

    def sparse(self, query: str, n: int) -> list[int]:
        scores = self.bm25.get_scores(query.lower().split())
        return list(np.argsort(scores)[::-1][:n])

    @staticmethod
    def rrf(*ranked_lists: list[int], k: int = 60) -> list[int]:
        """Reciprocal Rank Fusion: combine ranked lists using ranks only,
        so we don't need dense/BM25 scores to be on the same scale."""
        scores: dict[int, float] = {}
        for lst in ranked_lists:
            for rank, doc_id in enumerate(lst):
                scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
        return sorted(scores, key=scores.get, reverse=True)

    def search(self, query: str, first_stage: int = 20, top_k: int = 4) -> list[str]:
        dense_ids = self.dense(query, first_stage)
        sparse_ids = self.sparse(query, first_stage)
        fused = self.rrf(dense_ids, sparse_ids)[:first_stage]

        # Rerank the fused shortlist with the cross-encoder.
        pairs = [(query, self.docs[i]) for i in fused]
        rerank_scores = reranker.predict(pairs)
        order = np.argsort(rerank_scores)[::-1][:top_k]
        return [self.docs[fused[i]] for i in order]


if __name__ == "__main__":
    corpus = [
        "To cancel your subscription, go to Settings > Billing > Cancel Plan.",
        "Error code E-4021 means the payment method was declined by the bank.",
        "You can terminate your plan any time; access continues until period end.",
        "Our office is open Monday to Friday, 9am to 5pm.",
        "Refunds are processed within 5-7 business days after approval.",
    ]
    retriever = HybridRetriever(corpus)

    # Semantic query (paraphrase) -> dense search shines.
    print(retriever.search("how do I stop paying for the service?"))
    # Exact-code query -> BM25 shines; hybrid catches both.
    print(retriever.search("what does E-4021 mean?"))
