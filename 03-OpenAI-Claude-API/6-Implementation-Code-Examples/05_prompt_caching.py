"""
05_prompt_caching.py
===================
Cache a large, STABLE prompt prefix so repeated requests skip recomputing it --
cutting both cost and time-to-first-token.

THE IDEA
--------
An LLM turns your prompt into a KV cache during "prefill". If the leading part
of your prompt is identical to a recent request, the provider can reuse that
computed state instead of redoing it. That means: cheaper input tokens and much
faster first token.

Typical wins: agents and chat apps that resend a big system prompt, tool
definitions, or a reference document on every turn.

PROVIDER DIFFERENCES
--------------------
- OpenAI: AUTOMATIC. No code change. Kicks in for prompts >= 1024 tokens,
  matching the longest prefix. Cached input is billed at a discount. Just keep
  the static content at the FRONT and the dynamic user turn at the END.
- Anthropic: EXPLICIT. You mark cache breakpoints with
  cache_control={"type": "ephemeral"} on the blocks you want cached.
  A cache WRITE costs ~1.25x a normal input token; a cache READ costs ~0.1x
  (about 90% off). So caching pays off once a prefix is reused more than ~once.

GOLDEN RULE
-----------
The cache key is the EXACT bytes of the prefix. A single changed byte early
(a timestamp, a reordered JSON key, a swapped tool) invalidates the cache for
everything after it. Keep the prefix byte-stable; put anything dynamic last.
"""
import os

# A big, stable block we want to reuse across many requests (imagine a long
# policy document or knowledge base). Kept static == cache-friendly.
LARGE_STABLE_CONTEXT = (
    "You are a support assistant for ACME Cloud.\n"
    "Knowledge base:\n" + ("- ACME Cloud policy line. " * 400)  # ~ a few thousand tokens
)


def openai_cached(question: str) -> None:
    """OpenAI caches automatically -- we just order the prompt correctly."""
    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            # STATIC prefix first -> becomes the cached portion.
            {"role": "system", "content": LARGE_STABLE_CONTEXT},
            # DYNAMIC content last -> the only part that changes per request.
            {"role": "user", "content": question},
        ],
        max_tokens=150,
    )
    usage = resp.usage
    # cached_tokens shows how much of the input was served from cache.
    cached = getattr(usage, "prompt_tokens_details", None)
    cached_tok = getattr(cached, "cached_tokens", 0) if cached else 0
    print(f"OpenAI : in={usage.prompt_tokens} (cached={cached_tok}) "
          f"out={usage.completion_tokens}")
    print("  ->", resp.choices[0].message.content[:80], "...")


def anthropic_cached(question: str) -> None:
    """Anthropic requires an explicit cache_control breakpoint."""
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-5", max_tokens=150,
        # Mark the big system block as cacheable. The breakpoint says "cache
        # everything up to here". Reused within the TTL -> cheap cache reads.
        system=[{
            "type": "text",
            "text": LARGE_STABLE_CONTEXT,
            "cache_control": {"type": "ephemeral"},  # 5-min TTL by default
        }],
        messages=[{"role": "user", "content": question}],  # dynamic, uncached
    )
    u = resp.usage
    # These fields reveal cache behavior: creation (write) vs read (hit).
    print(f"Claude : in={u.input_tokens} out={u.output_tokens} "
          f"cache_write={getattr(u, 'cache_creation_input_tokens', 0)} "
          f"cache_read={getattr(u, 'cache_read_input_tokens', 0)}")
    print("  ->", "".join(b.text for b in resp.content if b.type == "text")[:80], "...")


def savings_note() -> None:
    """Napkin math: why caching a reused prefix is a big deal."""
    prefix_tokens = 6000
    reuses = 30            # e.g., a 30-step agent
    price_in = 3 / 1e6     # $/token (illustrative)
    no_cache = prefix_tokens * reuses * price_in
    # Anthropic-style: 1 write (~1.25x) + 29 reads (~0.1x)
    with_cache = prefix_tokens * (1.25 + (reuses - 1) * 0.1) * price_in
    print(f"\nPrefix cost over {reuses} calls: "
          f"no-cache=${no_cache:.4f}  with-cache=${with_cache:.4f} "
          f"(~{no_cache / with_cache:.1f}x cheaper on the prefix)")


if __name__ == "__main__":
    q = "Can I get a refund after 20 days?"
    if os.getenv("OPENAI_API_KEY"):
        openai_cached(q)
    if os.getenv("ANTHROPIC_API_KEY"):
        anthropic_cached(q)
    savings_note()  # runs without any API key -- pure arithmetic
