"""
04_retries_fallback.py
=====================
Production reliability for LLM calls: retry with exponential backoff + jitter,
a simple circuit breaker, and cross-provider failover.

WHY THIS MATTERS
----------------
Provider APIs return 429 (rate limited) and 5xx (transient server errors), and
networks time out. A naive app fails the user request on the first hiccup. A
resilient app absorbs transient errors and, if a provider is truly degraded,
fails over to another one.

KEY RULES
---------
- Retry ONLY transient errors: 429, 500/502/503/504, timeouts.
  NEVER retry 400/401/403/422 (bad request / auth / validation) -> it will just
  fail again and waste money.
- Use exponential backoff with FULL JITTER: sleep = random(0, base * 2**attempt).
  Jitter prevents many clients retrying in lockstep (a "thundering herd").
- Honor the Retry-After header when the server provides it.
- Use an idempotency key so a retried request that actually succeeded the first
  time (but whose response was lost) does not double-charge / double-act.
- A circuit breaker stops hammering a provider that is clearly down, letting it
  recover instead of drowning it in retries.
"""
import os
import random
import time
import uuid


# ---------------------------------------------------------------------------
# A tiny circuit breaker: after N consecutive failures, "open" for a cooldown.
# ---------------------------------------------------------------------------
class CircuitBreaker:
    def __init__(self, threshold: int = 3, cooldown: float = 10.0):
        self.threshold = threshold
        self.cooldown = cooldown
        self.failures = 0
        self.opened_at = 0.0

    def allow(self) -> bool:
        # If open, only allow a probe request once the cooldown has elapsed.
        if self.failures >= self.threshold:
            if time.time() - self.opened_at < self.cooldown:
                return False
            # half-open: let one request through to test recovery
        return True

    def record_success(self) -> None:
        self.failures = 0

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold:
            self.opened_at = time.time()


def backoff_sleep(attempt: int, base: float = 0.5, retry_after: float | None = None) -> None:
    """Full-jitter exponential backoff, honoring Retry-After if present."""
    if retry_after is not None:
        time.sleep(retry_after)
        return
    time.sleep(random.uniform(0, base * (2 ** attempt)))


def call_openai(prompt: str, idempotency_key: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    # The official SDK also retries internally; here we show explicit control.
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        # An idempotency key lets the server dedupe a retried POST so we do not
        # get billed / served twice for the same logical request.
        extra_headers={"Idempotency-Key": idempotency_key},
    )
    return resp.choices[0].message.content


def call_anthropic(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-5", max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def is_transient(exc: Exception) -> bool:
    """Decide whether an error is worth retrying. Retry 429 + 5xx + timeouts."""
    status = getattr(exc, "status_code", None)
    name = type(exc).__name__.lower()
    if status in (429, 500, 502, 503, 504):
        return True
    if "timeout" in name or "connection" in name or "internalserver" in name:
        return True
    return False


def robust_generate(prompt: str, max_retries: int = 5) -> str:
    """
    Try the primary provider with backoff; if it stays unhealthy, fail over to
    the secondary. The request is normalized (just a prompt) so either provider
    can serve it -- in a real gateway you would normalize messages/tools too.
    """
    idem = str(uuid.uuid4())  # stable across retries of THIS logical request

    providers = []
    if os.getenv("OPENAI_API_KEY"):
        providers.append(("openai", lambda: call_openai(prompt, idem), CircuitBreaker()))
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append(("anthropic", lambda: call_anthropic(prompt), CircuitBreaker()))

    for name, fn, breaker in providers:
        if not breaker.allow():
            print(f"[{name}] circuit open, skipping")
            continue
        for attempt in range(max_retries):
            try:
                out = fn()
                breaker.record_success()
                print(f"[{name}] success on attempt {attempt + 1}")
                return out
            except Exception as exc:  # noqa: BLE001 (demo: broad catch)
                breaker.record_failure()
                if not is_transient(exc) or attempt == max_retries - 1:
                    print(f"[{name}] giving up: {type(exc).__name__} -> failover")
                    break  # move to next provider
                retry_after = getattr(exc, "retry_after", None)
                print(f"[{name}] transient error, retrying (attempt {attempt + 1})")
                backoff_sleep(attempt, retry_after=retry_after)
    return "All providers failed -- return a cached or safe fallback response here."


if __name__ == "__main__":
    if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        print(robust_generate("Give me one tip for reliable API calls."))
    else:
        print("Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY to run this example.")
