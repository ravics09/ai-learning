# AI Frameworks — Implementation Code Examples

Runnable, heavily-commented examples. Each file is self-contained and demonstrates ONE
framework's core idea, with comments explaining **why** — the same reasoning you'd give
in an interview.

## Setup
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...     # required by every example
```
Run one at a time (each costs a few tokens):
```bash
python langchain_lcel_chain.py
```

## Index
| File | Framework | What it shows | Key "why" |
|---|---|---|---|
| [`langchain_lcel_chain.py`](./langchain_lcel_chain.py) | LangChain / LCEL | `prompt \| model \| parser`, invoke/batch/stream, native structured output | Runnables give streaming/batch/async for free |
| [`langgraph_agent.py`](./langgraph_agent.py) | LangGraph | Stateful, cyclic tool-using agent with checkpointing | Cycles + durability + typed state; resume after failure |
| [`llamaindex_rag.py`](./llamaindex_rag.py) | LlamaIndex | End-to-end RAG: chunk → embed → index → query with sources | Purpose-built retrieval; citable, grounded answers |
| [`instructor_structured_output.py`](./instructor_structured_output.py) | Instructor + Pydantic | Guaranteed typed output, retries, cross-field validation | Shape is enforced; correctness still needs checks |
| [`dspy_pipeline.py`](./dspy_pipeline.py) | DSPy | Signature → Module → Optimizer (compile prompts to a metric) | Programming, not prompting; model-portable |

## Suggested reading order
1. `langchain_lcel_chain.py` — the composition mental model (Runnables/LCEL).
2. `llamaindex_rag.py` — retrieval, the backbone of most real apps.
3. `instructor_structured_output.py` — reliable typed data out of an LLM.
4. `langgraph_agent.py` — step up to stateful, durable agents.
5. `dspy_pipeline.py` — optimize prompts instead of hand-tuning them.

## Notes
- Model names (`gpt-4o-mini`) are illustrative — swap for whatever you have access to.
- Version floors in `requirements.txt` target the LangChain 1.0 era (agents on the
  LangGraph runtime). Pin exact versions in real projects.
- These are teaching scaffolds: add tracing, timeouts, retries, and evals before prod
  (see `../3-Cheatsheet/AI-Frameworks-Cheatsheet.md` production checklist).

> Content synthesized from general domain knowledge and current (2025-2026) documentation and interview trends; rephrased for compliance with licensing restrictions.
