# OpenAI / Claude API — Implementation Code Examples

Runnable, heavily-commented examples covering the patterns you must know for production LLM apps. Comments explain **why**, not just what.

## Files
| File | What it demonstrates | Key concepts |
|---|---|---|
| `01_chat_streaming.py` | Streaming chat over SSE for both OpenAI & Claude | TTFT, delta accumulation, usage capture |
| `02_tool_calling.py` | Full multi-turn tool-calling loop (both providers) | JSON Schema tools, parallel calls, loop cap |
| `03_structured_output.py` | Guaranteed-schema JSON extraction | Structured Outputs (`strict`), Pydantic, forced-tool on Claude |
| `04_retries_fallback.py` | Reliability: backoff + jitter + provider failover | Retry policy, circuit breaker, idempotency |
| `05_prompt_caching.py` | Cache a large stable prefix on both providers | `cache_control`, byte-stable prefix, savings math |

## Setup
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Running
```bash
python 01_chat_streaming.py
python 02_tool_calling.py
python 03_structured_output.py
python 04_retries_fallback.py
python 05_prompt_caching.py
```

> **Notes**
> - Model names and prices in these files are illustrative anchors (they change often). The *patterns* are stable.
> - Each file guards provider calls behind an env-var / import check so you can run whichever SDK you have configured.
> - These are teaching examples: they favor clarity over exhaustive edge-case handling. In production, add structured logging, tracing, and metrics as described in the Detailed-Learning guide.

## Concept map (where each idea lives in the guide)
- Request lifecycle, params → `1-Detailed-Learning` §2–4
- Streaming → §5 · Tools → §6 · Structured outputs → §7
- Prompt caching → §9 · Retries/failover → §14–15

*Content synthesized from general domain knowledge and current (2025-2026) provider docs; rephrased for compliance with licensing restrictions.*
