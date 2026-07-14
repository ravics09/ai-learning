"""
multi_provider_litellm.py
=========================
WHY THIS FILE:
    The single most important ecosystem skill is NOT locking yourself to one provider.
    LiteLLM gives every model (OpenAI, Anthropic, Gemini, Groq, local vLLM/Ollama, ...) the
    SAME OpenAI-style interface. That means you can:
        - swap models with a one-line change (no vendor lock-in),
        - build a cheap-first "cascade" that escalates hard requests to a frontier model,
        - add fallbacks so a provider outage doesn't take you down.

    This is the "gateway" pattern from the detailed guide, in ~80 lines.

SETUP:
    pip install litellm
    export OPENAI_API_KEY=...        # and/or ANTHROPIC_API_KEY, GEMINI_API_KEY, etc.

RUN:
    python multi_provider_litellm.py
"""

from __future__ import annotations

import os

# litellm.completion mirrors the OpenAI chat API but works across 100+ providers.
from litellm import completion


def ask(model: str, prompt: str) -> str:
    """Call ANY provider with the same signature.

    WHY: keeping one function for every model means the rest of the app never needs to know
    which vendor answered — the whole point of a gateway abstraction.
    """
    resp = completion(
        model=model,  # e.g. "gpt-4o-mini", "claude-3-5-haiku-latest", "gemini/gemini-1.5-flash"
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,  # low temp = more deterministic; good for factual/coding tasks
        max_tokens=300,
    )
    return resp["choices"][0]["message"]["content"]


def ask_with_fallback(models: list[str], prompt: str) -> str:
    """Try models in order until one succeeds.

    WHY: real production traffic hits rate limits and 5xx errors. A fallback chain
    (cheap/local first, frontier/cloud last) keeps you resilient AND cost-aware.
    """
    last_err: Exception | None = None
    for model in models:
        try:
            print(f"  -> trying {model}")
            return ask(model, prompt)
        except Exception as e:  # noqa: BLE001 - we deliberately catch and continue
            last_err = e
            print(f"     {model} failed: {e}")
    raise RuntimeError(f"All models failed. Last error: {last_err}")


def looks_uncertain(answer: str) -> bool:
    """Toy confidence check for the cascade demo.

    WHY: a cascade only saves money if you can tell when the cheap model struggled.
    In production you'd use self-consistency, a verifier, or logprobs — not string matching.
    """
    hedges = ("i'm not sure", "i am not sure", "cannot", "unclear", "i don't know")
    return any(h in answer.lower() for h in hedges) or len(answer.strip()) < 10


def cascade(prompt: str) -> str:
    """Cheap-first, escalate-on-uncertainty. The core cost-optimization pattern."""
    cheap = "gpt-4o-mini"       # fast + inexpensive default tier
    strong = "gpt-4o"           # frontier tier, only used when needed
    answer = ask(cheap, prompt)
    if looks_uncertain(answer):
        print("  cheap model unsure -> escalating to frontier model")
        answer = ask(strong, prompt)
    return answer


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY (and optionally other provider keys) to run this demo.")

    question = "In one sentence, what problem does an LLM gateway solve?"

    print("\n[1] Same code, different providers:")
    # Swap any of these — the calling code is identical (the gateway benefit).
    for m in ["gpt-4o-mini", "claude-3-5-haiku-latest", "gemini/gemini-1.5-flash"]:
        try:
            print(f"\n{m}:\n{ask(m, question)}")
        except Exception as e:  # noqa: BLE001
            print(f"\n{m}: (skipped - {e})")

    print("\n[2] Fallback chain (resilience):")
    print(ask_with_fallback(["gpt-4o-mini", "claude-3-5-haiku-latest"], question))

    print("\n[3] Cost cascade (cheap-first, escalate on doubt):")
    print(cascade("What is 17 * 23? Answer with just the number."))
