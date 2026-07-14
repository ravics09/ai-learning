"""
rate_limit_budget.py
====================
Per-tenant rate limiting + token/cost budgets to stop unbounded consumption.

WHY THIS EXISTS
---------------
LLM inference costs money and compute, so an attacker (or a buggy retry loop)
can rack up huge bills or exhaust capacity — "denial-of-wallet" and DoS
(OWASP LLM10). Two complementary controls:

    1. RATE LIMIT  -> token-bucket, caps requests-per-second per tenant.
    2. BUDGET      -> hard ceiling on tokens/cost per period; reject when hit.

Plus per-request caps (max_tokens, agent steps) and anomaly alerting.

This is an in-memory reference. In production, back the token bucket with a
SHARED store (e.g., Redis) so limits hold across many app instances, and
persist budgets in a database.

Run:  python rate_limit_budget.py
"""

import time
from dataclasses import dataclass, field
from typing import Dict


# ---------------------------------------------------------------------------
# Token-bucket rate limiter
# ---------------------------------------------------------------------------
@dataclass
class TokenBucket:
    """Classic token bucket. `capacity` tokens, refilled at `refill_per_sec`.
    Each request costs 1 token. WHY token bucket: allows short bursts while
    enforcing a steady average rate — better UX than a hard fixed window."""
    capacity: float
    refill_per_sec: float
    _tokens: float = field(default=None)
    _last: float = field(default_factory=time.monotonic)

    def __post_init__(self):
        if self._tokens is None:
            self._tokens = self.capacity

    def allow(self, cost: float = 1.0) -> bool:
        now = time.monotonic()
        # Refill based on elapsed time since last check.
        self._tokens = min(self.capacity,
                           self._tokens + (now - self._last) * self.refill_per_sec)
        self._last = now
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False


# ---------------------------------------------------------------------------
# Cost/token budget
# ---------------------------------------------------------------------------
@dataclass
class Budget:
    """Hard ceiling on tokens spent in the current period. Fail CLOSED:
    when the budget is exhausted, reject rather than keep spending."""
    limit_tokens: int
    spent_tokens: int = 0

    def try_spend(self, tokens: int) -> bool:
        if self.spent_tokens + tokens > self.limit_tokens:
            return False
        self.spent_tokens += tokens
        return True

    @property
    def remaining(self) -> int:
        return max(0, self.limit_tokens - self.spent_tokens)


# Per-request hard caps. WHY: prevents a single 'sponge' prompt from being
# arbitrarily expensive, independent of the periodic budget.
MAX_INPUT_TOKENS = 4000
MAX_OUTPUT_TOKENS = 1000
MAX_AGENT_STEPS = 6


class LimitExceeded(Exception):
    pass


@dataclass
class TenantGuard:
    """Bundles the rate limiter + budget for one tenant."""
    bucket: TokenBucket
    budget: Budget

    def admit(self, est_input_tokens: int, est_output_tokens: int) -> None:
        # 1) Per-request caps first (cheap check).
        if est_input_tokens > MAX_INPUT_TOKENS:
            raise LimitExceeded("input exceeds per-request token cap")
        if est_output_tokens > MAX_OUTPUT_TOKENS:
            raise LimitExceeded("requested output exceeds per-request cap")
        # 2) Rate limit.
        if not self.bucket.allow():
            raise LimitExceeded("rate limit exceeded (429) — back off and retry")
        # 3) Budget.
        total = est_input_tokens + est_output_tokens
        if not self.budget.try_spend(total):
            raise LimitExceeded(
                f"token budget exhausted (remaining={self.budget.remaining})")


class Gateway:
    """Front door that enforces limits per tenant and watches for anomalies."""

    def __init__(self):
        self._tenants: Dict[str, TenantGuard] = {}

    def _guard_for(self, tenant_id: str) -> TenantGuard:
        if tenant_id not in self._tenants:
            self._tenants[tenant_id] = TenantGuard(
                bucket=TokenBucket(capacity=5, refill_per_sec=1),
                budget=Budget(limit_tokens=10_000),
            )
        return self._tenants[tenant_id]

    def handle(self, tenant_id: str, in_toks: int, out_toks: int) -> str:
        guard = self._guard_for(tenant_id)
        guard.admit(in_toks, out_toks)
        # Anomaly signal: budget draining unusually fast -> alert (stub).
        if guard.budget.remaining < guard.budget.limit_tokens * 0.1:
            print(f"[alert] tenant {tenant_id} nearing budget exhaustion")
        return f"ok (tenant={tenant_id}, remaining={guard.budget.remaining} tokens)"


if __name__ == "__main__":
    gw = Gateway()
    # Simulate a burst from one tenant.
    for i in range(8):
        try:
            print(gw.handle("tenant-A", in_toks=500, out_toks=200))
        except LimitExceeded as e:
            print(f"request {i}: BLOCKED -> {e}")
        time.sleep(0.1)

    # Oversized single request is rejected by per-request cap.
    try:
        gw.handle("tenant-B", in_toks=99_999, out_toks=10)
    except LimitExceeded as e:
        print("oversize blocked:", e)
