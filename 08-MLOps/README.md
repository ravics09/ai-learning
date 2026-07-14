# 08 — MLOps & LLMOps

Operationalizing ML/LLM systems: deployment, monitoring, versioning, and continuous improvement.

## Learning Objectives
- Take models from notebook to reliable production service.
- Monitor quality, cost, latency, and drift.
- Automate the ML lifecycle.

## Core Topics
### Model Lifecycle
- Experiment tracking (MLflow, Weights & Biases).
- Model & data versioning (DVC, model registry).
- Reproducible training pipelines.

### Deployment
- Serving: REST/gRPC, batch vs online inference.
- Containerization (Docker), orchestration (Kubernetes).
- Model servers: vLLM, TGI, Triton, Ollama.
- Autoscaling and GPU scheduling.

### CI/CD for ML
- Automated testing, retraining, and deployment.
- Canary and blue-green deployments.
- Rollbacks.

### Monitoring & Observability
- Data drift, concept drift, model decay.
- LLM observability: prompts, tokens, latency, cost, traces.
- Tools: LangSmith, Langfuse, Arize, Prometheus/Grafana.

### LLMOps Specifics
- Prompt versioning and A/B testing.
- Evaluation pipelines in CI.
- Cost tracking and budget alerts.
- Guardrails and safety monitoring.

## Interview Questions
1. What is model drift and how do you detect it?
2. Batch vs online inference — trade-offs?
3. How do you version prompts and models?
4. How would you set up LLM observability?
5. What is a canary deployment?
6. How do you monitor and control LLM costs in production?
7. What does vLLM do and why is it faster?

## Hands-On
- [ ] Containerize an LLM API and deploy with autoscaling.
- [ ] Add tracing + cost tracking with Langfuse or LangSmith.
- [ ] Build a CI pipeline that runs eval before deploy.

## Resources
- MLOps principles: https://ml-ops.org/
- vLLM: https://docs.vllm.ai/
