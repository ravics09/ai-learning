"""
05 — Production reliability: retries, model routing, token & cost accounting.

Covers the production concerns interviewers ask about:
  - RETRIES with exponential backoff (handle rate limits / transient errors)
  - MODEL ROUTING (cheap model for easy queries, frontier for hard ones)
  - TOKEN + COST accounting (know your $ before you ship)

Run:   python 05_reliability_router_cost.py
Needs: OPENAI_API_KEY + tenacity, tiktoken
"""
from __future__ import annotations

import tiktoken
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

client = OpenAI()

# Illustrative prices ($ per 1M tokens) — check current provider pricing.
PRICING = {
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},   # cheap
    "gpt-4o":      {"in": 2.50, "out": 10.00},  # frontier
}


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def estimate_cost(model: str, in_tokens: int, out_tokens: int) -> float:
    p = PRICING[model]
    return (in_tokens * p["in"] + out_tokens * p["out"]) / 1_000_000


def is_simple(query: str) -> bool:
    """Toy router heuristic. In practice, use a classifier or the query length,
    retrieval confidence, etc."""
    return len(query.split()) < 12 and "?" in query


# Retry transient failures (rate limits, timeouts) with backoff.
@retry(stop=stop_after_attempt(4), wait=wait_exponential(min=1, max=20))
def call_model(model: str, query: str):
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": query}],
    )


def answer(query: str) -> dict:
    # ROUTING: send easy queries to the cheap model, hard ones to frontier.
    model = "gpt-4o-mini" if is_simple(query) else "gpt-4o"

    resp = call_model(model, query)
    usage = resp.usage
    cost = estimate_cost(model, usage.prompt_tokens, usage.completion_tokens)
    return {
        "model": model,
        "answer": resp.choices[0].message.content,
        "in_tokens": usage.prompt_tokens,
        "out_tokens": usage.completion_tokens,
        "cost_usd": round(cost, 6),
    }


if __name__ == "__main__":
    for q in ["What is 2+2?", "Write a detailed migration plan from a monolith to microservices."]:
        result = answer(q)
        print(f"[{result['model']}] cost=${result['cost_usd']} "
              f"tokens={result['in_tokens']}+{result['out_tokens']}")
