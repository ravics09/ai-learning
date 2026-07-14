"""
04 — Attention from scratch (NumPy only).

Study this for architecture interviews. It implements:
  - scaled dot-product attention:  softmax(Q·Kᵀ / √d_k) · V
  - causal masking (a token only attends to itself and earlier tokens)
  - multi-head attention (split into heads, attend, concat, project)

No ML frameworks used, so you can explain every line.

Run: python 04_attention_from_scratch.py
"""
from __future__ import annotations

import numpy as np


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    # subtract max for numerical stability (avoids overflow in exp)
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=axis, keepdims=True)


def scaled_dot_product_attention(Q, K, V, causal: bool = True):
    """Q,K,V: (seq_len, d_k). Returns (seq_len, d_k) context vectors."""
    d_k = Q.shape[-1]

    # 1. Relevance scores between every query and every key.
    scores = Q @ K.T                      # (seq, seq)

    # 2. Scale by sqrt(d_k) -> keeps softmax gradients stable.
    scores = scores / np.sqrt(d_k)

    # 3. Causal mask: forbid attending to FUTURE tokens (set to -inf).
    if causal:
        seq = scores.shape[0]
        mask = np.triu(np.ones((seq, seq)), k=1).astype(bool)  # upper triangle
        scores[mask] = -np.inf

    # 4. Softmax -> attention weights that sum to 1 per row.
    weights = softmax(scores, axis=-1)

    # 5. Weighted sum of Values -> context-aware representation.
    return weights @ V, weights


class MultiHeadAttention:
    """Minimal multi-head attention with random (fixed) projection weights."""

    def __init__(self, d_model: int, n_heads: int, seed: int = 0):
        assert d_model % n_heads == 0, "d_model must divide by n_heads"
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        rng = np.random.default_rng(seed)
        # Learned in real models; random here just to demonstrate the mechanics.
        self.Wq = rng.normal(size=(d_model, d_model)) * 0.1
        self.Wk = rng.normal(size=(d_model, d_model)) * 0.1
        self.Wv = rng.normal(size=(d_model, d_model)) * 0.1
        self.Wo = rng.normal(size=(d_model, d_model)) * 0.1

    def _split_heads(self, x):  # (seq, d_model) -> list of (seq, d_head)
        seq = x.shape[0]
        x = x.reshape(seq, self.n_heads, self.d_head)
        return [x[:, h, :] for h in range(self.n_heads)]

    def forward(self, x: np.ndarray) -> np.ndarray:
        # Project inputs into Q, K, V.
        Q, K, V = x @ self.Wq, x @ self.Wk, x @ self.Wv
        # Each head attends independently...
        head_outputs = []
        for qh, kh, vh in zip(self._split_heads(Q), self._split_heads(K), self._split_heads(V)):
            ctx, _ = scaled_dot_product_attention(qh, kh, vh, causal=True)
            head_outputs.append(ctx)
        # ...then concatenate heads and apply the output projection.
        concat = np.concatenate(head_outputs, axis=-1)   # (seq, d_model)
        return concat @ self.Wo


if __name__ == "__main__":
    seq_len, d_model, n_heads = 5, 16, 4
    x = np.random.default_rng(1).normal(size=(seq_len, d_model))

    mha = MultiHeadAttention(d_model, n_heads)
    out = mha.forward(x)
    print("input shape :", x.shape)
    print("output shape:", out.shape)  # same shape -> stackable in residual stream

    # Show the causal attention pattern for a single head.
    _, weights = scaled_dot_product_attention(x[:, :4], x[:, :4], x[:, :4], causal=True)
    print("\nCausal attention weights (row=query, col=key):")
    print(np.round(weights, 2))  # upper triangle is 0 -> no peeking at the future
