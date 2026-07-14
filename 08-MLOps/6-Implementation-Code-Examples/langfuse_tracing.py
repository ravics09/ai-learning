"""
langfuse_tracing.py
===================
LLMOps essentials: prompt versioning + tracing + per-request token/cost tracking.

WHY THIS MATTERS
----------------
LLM apps are non-deterministic and multi-step (retrieve -> prompt -> generate).
When something looks "worse" in production, you can't reproduce it from a stack
trace. You need:
  - PROMPT VERSIONING: prompts are code; version them so you can compare, A/B,
    and ROLL BACK a bad prompt WITHOUT redeploying the app.
  - TRACING: capture the full span tree per request (inputs, outputs, latency).
  - COST TRACKING: tokens x price, per request/feature/tenant, with budgets.

This example is written to run WITHOUT network access (a mock LLM + a no-op
tracer fallback) so it demonstrates the pattern safely. Swap in the real
Langfuse client + OpenAI call in production.

Docs: https://langfuse.com/docs
"""
from __future__ import annotations

import os
from dataclasses import dataclass

# --- Prompt registry (versioned) -------------------------------------------
# WHY: in production these live in Langfuse/LangSmith or git with env labels,
# fetched by version/label at runtime. Here we inline a tiny registry to show
# the concept: each prompt has a version so traces are comparable and revert
# is a label change, not a code deploy.
PROMPTS = {
    "support_answer": {
        "v1": "Answer the question.\n\nQ: {q}\nA:",
        "v2": ("You are a support agent. Answer ONLY from the context. "
               "If unknown, say you don't know. Cite sources.\n\n"
               "Context:\n{context}\n\nQ: {q}\nA:"),
    }
}
ACTIVE_LABEL = {"support_answer": "v2"}  # WHY: flip this to roll back instantly


def get_prompt(name: str) -> tuple[str, str]:
    version = ACTIVE_LABEL[name]
    return version, PROMPTS[name][version]


# --- Pricing table for cost tracking ---------------------------------------
# WHY: cost = tokens x price and runs forever; track it per request so you can
# attribute spend per feature/tenant and alert on budget overruns.
PRICE_PER_1K = {"input": 0.00015, "output": 0.00060}  # example $/1K tokens


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int


def mock_llm(prompt: str) -> LLMResponse:
    """Deterministic stand-in for a real API call (offline-safe).

    In production:
        from openai import OpenAI
        resp = OpenAI().chat.completions.create(model=..., messages=[...])
        usage = resp.usage  # prompt_tokens / completion_tokens
    """
    # Rough token estimate: ~4 chars per token.
    in_tok = max(1, len(prompt) // 4)
    text = "Based on the context, here is the grounded answer. [source: doc-1]"
    out_tok = max(1, len(text) // 4)
    return LLMResponse(text=text, input_tokens=in_tok, output_tokens=out_tok)


def cost_usd(r: LLMResponse) -> float:
    return round(
        r.input_tokens / 1000 * PRICE_PER_1K["input"]
        + r.output_tokens / 1000 * PRICE_PER_1K["output"],
        6,
    )


def get_tracer():
    """Return a Langfuse client if configured, else a no-op tracer.

    WHY the fallback: keeps the example runnable offline and shows that tracing
    should never crash the request path if the observability backend is down.
    """
    if os.getenv("LANGFUSE_PUBLIC_KEY"):
        try:
            from langfuse import Langfuse  # type: ignore
            return Langfuse()
        except Exception:
            pass

    class _NoopTrace:
        def span(self, **kw):  # returns something with .end()/.update()
            return self
        def update(self, **kw):
            return self
        def end(self, **kw):
            return self

    class _Noop:
        def trace(self, **kw):
            print(f"[trace] {kw.get('name')} input={kw.get('input')}")
            return _NoopTrace()

    return _Noop()


def answer(question: str, context: str, tenant: str = "acme") -> str:
    tracer = get_tracer()
    # Root trace for the whole request — WHY: one traceable unit per user call.
    trace = tracer.trace(name="support_answer", input={"q": question}, user_id=tenant)

    version, template = get_prompt("support_answer")
    prompt = template.format(q=question, context=context)

    # Child span for the LLM call — WHY: attribute latency/tokens/cost per step.
    span = trace.span(name="llm_call", input={"prompt_version": version})
    resp = mock_llm(prompt)
    c = cost_usd(resp)

    # Attach usage + cost + prompt version so dashboards can slice by any of them.
    span.update(
        output=resp.text,
        metadata={
            "prompt_version": version,
            "input_tokens": resp.input_tokens,
            "output_tokens": resp.output_tokens,
            "cost_usd": c,
            "tenant": tenant,
        },
    )
    span.end()
    trace.update(output=resp.text)

    print(f"prompt_version={version} tokens(in/out)={resp.input_tokens}/"
          f"{resp.output_tokens} cost=${c} tenant={tenant}")
    return resp.text


if __name__ == "__main__":
    out = answer(
        question="How do I reset my password?",
        context="To reset your password, click 'Forgot password' on the login page.",
    )
    print("ANSWER:", out)
    print("\nTip: flip ACTIVE_LABEL['support_answer'] to 'v1' to roll back the "
          "prompt WITHOUT a code deploy - the core LLMOps prompt-versioning win.")
