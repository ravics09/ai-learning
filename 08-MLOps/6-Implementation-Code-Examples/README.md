# MLOps & LLMOps — Implementation Code Examples

Runnable, heavily-commented examples covering the core MLOps/LLMOps building blocks. Every file explains **why**, not just what, so you can read it like a tutorial and defend every line in an interview.

## Files
| File | What it shows |
|---|---|
| `requirements.txt` | Dependencies |
| `mlflow_tracking.py` | Experiment tracking + model registry: log params/metrics, gate on a threshold, promote to Production |
| `fastapi_model_serving.py` | Online inference service: schema validation, health probe, Prometheus metrics, versioning |
| `Dockerfile` | Production-style container: layer caching, non-root user, healthcheck |
| `github_actions_ci.yml` | CI/CD for ML: tests + data validation + **eval gate** that blocks regressions |
| `drift_detection.py` | Data drift with PSI + KS test, with an alert decision and anti-noise logic |
| `langfuse_tracing.py` | LLMOps: prompt versioning, tracing spans, per-request token/cost tracking |

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Suggested reading order
1. `mlflow_tracking.py` — how a model becomes a versioned, promotable artifact.
2. `fastapi_model_serving.py` + `Dockerfile` — how it gets served and packaged.
3. `github_actions_ci.yml` — how CI gates a deploy on quality.
4. `drift_detection.py` — how you know when it's decaying.
5. `langfuse_tracing.py` — the LLMOps twist: prompts, traces, cost.

> These are teaching examples. In production add retries, timeouts, structured logging, auth, and error handling. Files are intentionally not executed here (no side effects / no `__pycache__`).
