# Cloud for AI — Implementation Code Examples

Runnable / illustrative, heavily-commented examples. Each file demonstrates ONE core
"cloud for AI" idea, with comments explaining **why** — the same reasoning you'd give in
an interview. Together they walk from "call a managed model" to "run your own model on
autoscaling GPUs, defined as code, kept secure."

## Setup
```bash
pip install -r requirements.txt      # for the Python examples only

# Cloud creds (examples use the default credential chain / IAM roles, NOT hardcoded keys):
export AWS_REGION=us-east-1           # bedrock_invoke.py, terraform_gpu_infra.tf
# gcloud auth application-default login   # for the Vertex path

# Infra tools (install separately):
#   terraform >= 1.9    kubectl / helm    KEDA (in-cluster)
```

## Index
| File | Layer | What it shows | Key "why" |
|---|---|---|---|
| [`bedrock_invoke.py`](./bedrock_invoke.py) | Managed FM API | Call Bedrock (sync + streaming), IAM creds, cache/guardrail hooks | Fastest path; stream for low TTFT; no GPU ops |
| [`sagemaker_or_vertex_deploy.py`](./sagemaker_or_vertex_deploy.py) | Managed custom deploy | Deploy your own model to a SageMaker/Vertex autoscaling endpoint | Control without running K8s; artifacts in object storage |
| [`terraform_gpu_infra.tf`](./terraform_gpu_infra.tf) | IaC | EKS + spot GPU node group + remote state + secrets | Repeatable infra; spot saves 60–90%; no secrets in state |
| [`k8s_llm_deployment.yaml`](./k8s_llm_deployment.yaml) | Self-host serving | vLLM on a GPU pod, GPU request, secret-injected token, probes | Max control + throughput (continuous batching) |
| [`autoscaling_config.yaml`](./autoscaling_config.yaml) | Scale | KEDA/HPA autoscaling on queue depth / GPU util | Scale on serving metrics, NOT CPU% |

## Suggested reading order
1. `bedrock_invoke.py` — the easiest way to ship: a managed model API.
2. `sagemaker_or_vertex_deploy.py` — step up to your own model, still managed.
3. `terraform_gpu_infra.tf` — codify a GPU cluster (spot + remote state + secrets).
4. `k8s_llm_deployment.yaml` — self-host the model with vLLM for full control.
5. `autoscaling_config.yaml` — make it elastic on the *right* metric.

## The mental model these examples teach
```
Managed API  →  Managed custom endpoint  →  Self-host on K8s (IaC + autoscaling)
  least ops  ───────────────────────────────────────────────►  most control / best $ at scale
```
Start managed. Move right as volume grows, GPUs stay busy, and you need latency/data
control. Everything defined as code, scaled on serving metrics, with least-privilege IAM
and secrets pulled from a manager (never hardcoded).

## Notes
- Model IDs / instance types / ARNs are **illustrative** — swap for what you have access to.
- These are teaching scaffolds: add tracing, timeouts, retries, budgets, and evals before
  production (see `../3-Cheatsheet/Cloud-Cheatsheet.md`).
- The `.tf` and `.yaml` files are not executed here (no cloud/cluster) — read the comments
  for the real apply/deploy flow.

> Content synthesized from general domain knowledge and current (2025-2026) documentation and interview trends; rephrased for compliance with licensing restrictions.
