"""
run_local_model_ollama.py
=========================
WHY THIS FILE:
    Not every workload should hit a paid API. Running an OPEN-WEIGHT model locally with
    Ollama gives you:
        - privacy (data never leaves the machine — great for sensitive/on-prem use),
        - zero per-token cost (you own the hardware),
        - offline capability and no rate limits.
    Ollama wraps llama.cpp and serves quantized GGUF models with one command. It's the
    "local dev / single-user" tier from the serving comparison — for high concurrency you'd
    graduate to vLLM or TGI.

SETUP:
    1) Install Ollama: https://ollama.com/download
    2) Pull a model:   ollama pull llama3.2   (small, fast; ~2GB quantized)
    3) pip install ollama

RUN:
    python run_local_model_ollama.py
"""

from __future__ import annotations

import ollama

MODEL = "llama3.2"  # any local tag: qwen2.5, mistral, gemma2, phi3, deepseek-r1, ...


def basic_chat(prompt: str) -> str:
    """One-shot local completion.

    WHY: shows the model runs entirely on your box — no API key, no network egress.
    """
    resp = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.3},  # sampling knobs work the same as cloud models
    )
    return resp["message"]["content"]


def streaming_chat(prompt: str) -> None:
    """Stream tokens as they are generated.

    WHY: streaming improves *perceived* latency (TTFT) massively — users see text
    immediately instead of waiting for the full response. This matters for UX.
    """
    stream = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in stream:
        # Print incrementally, no newline, so it reads like live typing.
        print(chunk["message"]["content"], end="", flush=True)
    print()


def local_embeddings(text: str) -> list[float]:
    """Ollama can also serve embedding models locally.

    WHY: keeping embeddings local means your RAG index never sends documents to a vendor —
    a common requirement for private/regulated data.
    """
    # Pull first:  ollama pull nomic-embed-text
    resp = ollama.embeddings(model="nomic-embed-text", prompt=text)
    return resp["embedding"]


if __name__ == "__main__":
    print(f"Using local model: {MODEL}\n")

    print("[1] Basic local chat:")
    try:
        print(basic_chat("Explain quantization in two sentences."))
    except Exception as e:  # noqa: BLE001
        print(f"(Is Ollama running and '{MODEL}' pulled? Error: {e})")

    print("\n[2] Streaming (better perceived latency):")
    try:
        streaming_chat("List 3 reasons to self-host an open-weight model.")
    except Exception as e:  # noqa: BLE001
        print(f"(stream failed: {e})")

    print("\n[3] Local embeddings (privacy-preserving RAG):")
    try:
        vec = local_embeddings("vector databases power retrieval")
        print(f"embedding dim = {len(vec)}; first values = {vec[:5]}")
    except Exception as e:  # noqa: BLE001
        print(f"(pull 'nomic-embed-text' first. Error: {e})")
