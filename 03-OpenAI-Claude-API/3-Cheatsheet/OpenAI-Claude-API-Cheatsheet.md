# OpenAI / Claude API — Cheatsheet

> Dense quick-reference. Skim before an interview or while coding. Prices/model names are illustrative anchors (they change) — the mechanics are stable.

---

## Core call shapes
```python
# OpenAI Chat Completions
from openai import OpenAI; client = OpenAI()
r = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role":"system","content":"..."},{"role":"user","content":"..."}],
    temperature=0.2, max_tokens=500, stream=False)
r.choices[0].message.content
```
```python
# Anthropic Messages
import anthropic; c = anthropic.Anthropic()
m = c.messages.create(
    model="claude-sonnet-4-5",
    system="...",                      # top-level, NOT a message
    messages=[{"role":"user","content":"..."}],
    max_tokens=500)                    # REQUIRED on Anthropic
m.content[0].text
```

---

## Roles
| Role | OpenAI | Anthropic |
|---|---|---|
| system | first message | `system` param |
| user | `user` | `user` |
| assistant | `assistant` | `assistant` |
| tool result | role `tool` + `tool_call_id` | `user` msg w/ `tool_result` block + `tool_use_id` |

---

## Sampling params
| Param | Effect | Typical |
|---|---|---|
| `temperature` | rescales distribution (0=sharp) | 0 extract, 0.7–1.0 creative |
| `top_p` | nucleus truncation | 0.9–1.0 |
| `top_k` (Anthropic) | keep top k tokens | default |
| `max_tokens` | cap output | always set |
| `stop` | stop sequences | format control |
| `seed` (OpenAI) | best-effort repro | evals |
| `frequency/presence_penalty` (OpenAI) | anti-repetition | 0 |

**Tune one of temperature/top_p, not both.** `temperature=0` ≈ greedy, not perfectly reproducible.

---

## Finish / stop reasons (always check!)
| OpenAI `finish_reason` | Anthropic `stop_reason` | Meaning |
|---|---|---|
| `stop` | `end_turn` | natural end |
| `length` | `max_tokens` | **truncated** — JSON may be broken |
| `tool_calls` | `tool_use` | run the tool loop |
| `content_filter` | (refusal) | blocked — return safe msg |

---

## Streaming (SSE)
```python
for chunk in client.chat.completions.create(model="gpt-4o", stream=True,
        messages=[...], stream_options={"include_usage": True}):
    print(chunk.choices[0].delta.content or "", end="")
```
- Cuts TTFT; disable proxy buffering (`X-Accel-Buffering: no`).
- Lose single `usage` → request `include_usage`.
- Tool args stream as **fragments** → accumulate by index, then `json.loads`.

---

## Tool / function calling
```python
tools=[{"type":"function","function":{"name":"get_weather",
  "parameters":{"type":"object","properties":{"city":{"type":"string"}},
  "required":["city"],"additionalProperties":False}}}]
```
Loop: send tools → `tool_calls` → execute → append result → call again → final. **Cap iterations.**
- `tool_choice`: `auto` | `required` | force a function.
- `parallel_tool_calls=True` (default) → run concurrently; disable for strict schema / ordered side-effects.

---

## Structured output ladder
| Level | OpenAI | Guarantee |
|---|---|---|
| Prompt | "reply JSON" | none |
| JSON mode | `response_format={"type":"json_object"}` | valid JSON, any shape |
| **Structured Outputs** | `response_format={"type":"json_schema","strict":true}` | matches your schema |
| Tool schema | tool `parameters` | args match schema |

Claude: **force a tool** whose input schema = target object (no `json_schema` format). Rules: all fields `required`, `additionalProperties:false`, enums for categoricals. **Always still validate semantics.**

---

## Prompt caching
| | OpenAI | Anthropic |
|---|---|---|
| Trigger | automatic (≥1024 tok, 128-tok steps) | explicit `cache_control:{"type":"ephemeral"}` |
| Read | ~50% off input | ~0.1× (≈90% off) |
| Write | none | ~1.25× (5m TTL) / ~2× (1h TTL) |
| Rule | static prefix first, dynamic last | keep prefix **byte-stable**, ≤4 breakpoints |
Any early byte change (timestamp, reordered key, swapped tool) **busts** everything after it.

---

## Cost math
```
cost = in_tok/1e6*price_in + out_tok/1e6*price_out (+ cache write) (- cache read savings)
~4 chars ≈ 1 token · ~0.75 tok/word · output ≈ 4–5× input price
```
**Example** (@ $3/$15 per 1M): 8k in + 500 out = 8000/1e6*3 + 500/1e6*15 = **$0.0315/turn** → 1M turns ≈ **$31.5k/mo**. Cache the 6k static prefix → ~**$0.015/turn**.

**Levers:** caching · shorter output · model routing · batch API (~50% off) · summarize history.

---

## Rate limits / retries
- Limits: **RPM** (requests/min) + **TPM** (tokens/min), per model/org, rise with spend tier.
- Retry **only** 429/500/502/503/504/timeout. **Never** 400/401/403/422.
- **Backoff + full jitter:** `sleep=random(0, base*2**attempt)`; honor `Retry-After`.
- **Idempotency key** so lost-response retries don't double-charge/act.
- Timeouts: per-request + total; streaming needs **inter-token** timeout.
- Client-side token-bucket limiter + bounded concurrency to avoid 429s.

---

## Reliability patterns
Retry → **failover** (provider B, normalized request) → **circuit breaker** (stop hammering sick provider) → **degrade** (smaller model / cached / safe msg). Track health per provider.

---

## Embeddings (OpenAI; Claude has none first-party)
```python
client.embeddings.create(model="text-embedding-3-small", input=[...])
```
Same model for index+query · normalize · `dimensions` param (Matryoshka) to shrink · batch inputs · cache (deterministic).

---

## Multimodal
Images tiled → billed as **input tokens**; downscale. OpenAI `image_url`/base64; Anthropic `source` base64 block. Combine with Structured Outputs for typed extraction.

---

## Moderation / safety
`client.moderations.create(...)` (free) as pre/post filter. Delimit untrusted text as data. Least-privilege tools. Enforce authz in code, not prompt. Redact PII/secrets on output.

---

## OpenAI vs Claude — one glance
| | OpenAI | Claude |
|---|---|---|
| APIs | Chat Completions + **Responses** (stateful) | **Messages** (stateless) |
| System | first message / `instructions` | `system` field |
| Structured | Structured Outputs (`json_schema`) | forced tool |
| Caching | automatic | explicit `cache_control` |
| Reasoning | o-series | extended thinking (budget) |
| Embeddings | yes | no |
| `max_tokens` | optional | required |
| State | `previous_response_id` | client resends history |

---

## Gotchas checklist
- [ ] Check `finish_reason` before parsing JSON
- [ ] Set `max_tokens` (required on Anthropic)
- [ ] Accumulate streamed tool-call fragments before `json.loads`
- [ ] Keep cache prefix byte-stable; dynamic content last
- [ ] Retry only transient errors, with jitter + `Retry-After`
- [ ] Idempotency key on side-effecting calls
- [ ] Validate structured output semantics, not just shape
- [ ] Same embedding model for index & query
- [ ] Budget for hidden reasoning/thinking tokens

*Content synthesized from general domain knowledge and current (2025-2026) provider docs; rephrased for compliance with licensing restrictions.*
