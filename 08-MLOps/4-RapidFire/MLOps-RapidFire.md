# MLOps & LLMOps Rapid Fire

> 50 one-line questions with one-line answers. Drill them out loud until they're instant. Great for the last 30 minutes before an interview.

---

## Fundamentals

1. **What is MLOps?** DevOps for ML — reproducible, automated, monitored, reliable model systems.
2. **MLOps vs DevOps?** ML versions code + data + models, not just code.
3. **What is LLMOps?** MLOps + prompt versioning, subjective-output evals, token-cost control, guardrails.
4. **Version what in ML?** Code, data, model, prompt, config.
5. **MLOps maturity levels?** L0 manual → L1 automated training/CT → L2 full CI/CD.
6. **Is deploying the end?** No — it's the middle; monitoring/retraining is the rest.
7. **What is Continuous Training (CT)?** Monitoring auto-triggers retrain + redeploy on drift/schedule.
8. **Training/serving skew?** Feature computed differently in training vs serving.
9. **Label leakage?** Using info at train time unavailable at prediction time.
10. **Fix skew + leakage?** Feature store + point-in-time correct joins.

## Tracking, Versioning, Reproducibility

11. **Experiment tracking logs?** Params, metrics, artifacts, git SHA, data version.
12. **MLflow vs W&B?** MLflow = OSS all-in-one; W&B = rich UI + sweeps + collab.
13. **Why not Git for data?** Git chokes on big files; use DVC pointers + remote storage.
14. **What is DVC?** Data versioning: hash pointer in git, real data in S3/GCS.
15. **What is a model registry?** Source of truth for model versions, stages, lineage, approvals.
16. **Registry stages?** Staging → Production → Archived.
17. **Reproducibility needs?** Pin code + data + env + params.
18. **What is a pipeline DAG?** Declarative stages; re-run only changed ones (caching).
19. **Orchestrators?** Airflow, Dagster, Prefect, Kubeflow, Metaflow.
20. **What is a feature store?** Central consistent feature compute for train + serve.

## Deployment & Serving

21. **Batch vs online?** Precompute (cheap) vs per-request ms (always-on).
22. **When online?** Only when per-request freshness is required.
23. **REST vs gRPC?** REST = public/easy; gRPC = internal/binary/HTTP2/streaming/fast.
24. **Serverless downside for LLMs?** Cold starts + size/GPU limits.
25. **Why Docker?** Same deps everywhere; kills "works on my machine."
26. **Why Kubernetes?** Self-healing, autoscaling, rolling updates for containers.
27. **Readiness vs liveness probe?** Ready = accept traffic; live = restart if hung.
28. **What is HPA?** Horizontal Pod Autoscaler — scale replicas on a metric.
29. **What is KEDA?** Event/queue-driven autoscaling + scale-to-zero.
30. **Scale GPU pods on?** Queue depth / GPU util — not CPU.

## Model Servers

31. **Why vLLM fast?** PagedAttention + continuous batching → 2-4×+ concurrency.
32. **PagedAttention does?** Treats KV cache like memory pages; cuts fragmentation to a few %.
33. **Continuous batching?** Merge/evict requests each step vs waiting for a full batch.
34. **TGI sweet spot?** Hugging Face ecosystem + good interactive latency.
35. **Triton sweet spot?** Multi-framework + dynamic batching + ensembles.
36. **Ollama sweet spot?** Local prototyping / low concurrency, zero config.
37. **LLM latency metrics?** TTFT, inter-token (TPOT), tokens/sec, $/1K req.
38. **Fit a huge model?** Quantization + tensor/pipeline parallelism + offload.

## CI/CD & Release

39. **What's extra in ML CI/CD?** Data validation + model eval gate + CT.
40. **Eval gate?** Block deploy if model regresses on the golden set.
41. **Canary?** Small % traffic to new model, ramp if healthy.
42. **Blue-green?** Two full envs, instant flip + instant rollback (2× infra).
43. **Shadow deploy?** New model scores mirrored traffic, output discarded.
44. **Rollback rule?** Immutable artifacts, pin by digest, one-click, auto on SLO breach.

## Monitoring & Drift

45. **Four monitoring layers?** Infra, data, model, business.
46. **Report which latency?** p95/p99 tail, not averages.
47. **Data vs concept drift?** Inputs P(X) change vs relationship P(y|X) changes.
48. **Why is concept drift hard?** Needs ground-truth labels that arrive late/never.
49. **PSI thresholds?** <0.1 stable, 0.1-0.2 watch, >0.2 act; KS oversensitive on big samples.
50. **Detect concept drift w/o labels?** Proxies: prediction drift, confidence collapse, KPI shifts.

## LLMOps Bonus (one-liners)

- **Prompt versioning?** Registry + env labels; roll back without redeploy; A/B variants.
- **Eval in CI?** Hard gates (schema/PII/tool-call) + soft gates (judge, paired test vs baseline).
- **Cheapest cost win?** Semantic + prompt caching.
- **Model routing?** Cheap model for easy queries, frontier for hard ones.
- **LLM tracing?** Full span tree per request with tokens/latency/cost (Langfuse/LangSmith).
- **Indirect prompt injection?** Malicious instructions inside retrieved/tool content — treat as untrusted data.
- **Why safetensors?** Pickle can execute code; safetensors can't.
- **Guardrails?** Input (injection/PII/jailbreak) + output (toxicity/secrets/schema).

*Rephrased for compliance with licensing restrictions.*
