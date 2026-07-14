# LLMs — Implementation Code Examples

Runnable, heavily-commented examples covering the LLM skills interviewers test: API usage, streaming, tool calling, structured output, a from-scratch attention implementation, and production reliability (retries, routing, token/cost accounting).

## Files
| File | What it shows |
|---|---|
| `requirements.txt` | Dependencies |
| `01_chat_and_streaming.py` | Chat completion + token streaming (low perceived latency) |
| `02_tool_calling.py` | Full function/tool-calling loop |
| `03_structured_output.py` | Enforced, validated JSON with Pydantic |
| `04_attention_from_scratch.py` | Scaled dot-product + multi-head attention in NumPy (no libs) |
| `05_reliability_router_cost.py` | Retries/backoff, model routing, token & cost accounting |

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
```

## How to read these
`04_attention_from_scratch.py` is the one to study for architecture rounds — it implements attention with only NumPy so you can explain every step (Q·Kᵀ/√d_k → softmax → ·V, causal mask, multi-head). The others (`01`–`03`, `05`) cover the applied engineering skills for building on top of LLM APIs.

> Teaching examples — add production error handling, logging, and secrets management before shipping.
