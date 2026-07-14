# AI Evaluation — Implementation Code Examples

Runnable, heavily-commented examples. Each file demonstrates ONE evaluation idea, with comments
explaining **why** — the same reasoning you'd give in an interview.

## Setup
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...      # needed by the LLM-judge / RAGAS examples
```
Run one at a time:
```bash
python llm_as_judge.py
python golden_set_regression.py --fail-under 0.9
python ab_test_analysis.py
python ragas_eval.py
npx promptfoo@latest eval -c promptfoo_config.yaml   # promptfoo is a Node CLI
```

## Index
| File | What it shows | Key "why" |
|---|---|---|
| [`llm_as_judge.py`](./llm_as_judge.py) | Pairwise LLM-judge with position-swap bias control + kappa calibration | A judge you never calibrated is just an opinion |
| [`ragas_eval.py`](./ragas_eval.py) | RAG metrics (faithfulness, answer/context relevance, context recall) | Measure retriever vs generator separately |
| [`golden_set_regression.py`](./golden_set_regression.py) | CI gate: run golden set, per-slice diff, exit non-zero | Evals are the unit tests of an AI system |
| [`ab_test_analysis.py`](./ab_test_analysis.py) | Two-proportion z-test for an online A/B win | "Higher number" isn't a win without significance |
| [`promptfoo_config.yaml`](./promptfoo_config.yaml) | Declarative prompt/model matrix eval + assertions | Fast, versionable, CI-friendly prompt testing |

## Suggested reading order
1. `llm_as_judge.py` — the core reference-free scoring primitive + bias control.
2. `ragas_eval.py` — apply metrics to a RAG pipeline.
3. `golden_set_regression.py` — wire evals into a CI deploy gate.
4. `ab_test_analysis.py` — prove an online win with statistics.
5. `promptfoo_config.yaml` — declarative alternative for prompt/model matrices.

## Notes
- Model names (`gpt-4o`, `gpt-4o-mini`) are illustrative — swap for what you have access to.
- These are teaching scaffolds: add tracing, retries, caching, and sampling before production.
- The judge examples cost a few tokens per run; `ab_test_analysis.py` and the stats are free/offline.
- No files here execute network calls at import time; API calls happen inside `main()` guards.

> Content synthesized from general domain knowledge and current (2025-2026) documentation and interview trends; rephrased for compliance with licensing restrictions.
