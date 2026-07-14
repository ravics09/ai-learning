# Cloud for AI — Cheatsheet

> Dense, scan-friendly reference. Compute options, cross-cloud AI service map, cost
> levers, HA patterns, security, and IaC — the stuff you want one glance before an
> interview or a design.

---

## 1. Compute Options (spectrum)

```
Bare metal  →  VM/EC2  →  Containers (EKS/GKE/AKS)  →  Serverless containers  →  FaaS  →  Managed API
  most control ───────────────────────────────────────────────────────────────► most managed
```

| Option | Manages | Use for | Watch out |
|---|---|---|---|
| VM (EC2/GCE) | you: OS, drivers, scale | max GPU control, custom server | ops burden |
| Container (EKS/GKE/AKS) | you: cluster; app packaged | scalable prod inference | GPU operator, big images |
| Serverless container (Fargate/Cloud Run) | platform: nodes | CPU glue, bursty, scale-to-0 | limited GPU support |
| FaaS (Lambda) | platform: everything | event glue, embeddings-on-upload | cold start, 15-min limit, no GPU |
| Managed API (Bedrock) | provider: model+GPU | fast GenAI, no ops | per-token cost, less control |
| Serverless GPU (Modal/RunPod) | provider: GPU, scale-to-0 | spiky GPU work | cold start (improving fast) |

**GPU SKUs:** H100/H200/GB200 (train + big inference) · A100 (still common) · L4/L40S/A10G
(cost-efficient inference). Cloud: AWS `p5`/`g6`, GCP `a3`/`g2`, Azure `ND`/`NC`.

---

## 2. Managed AI Services — AWS vs Azure vs GCP

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| FM API (per-token) | **Bedrock** (Claude, Llama, Nova, Titan) | **Azure OpenAI / AI Foundry** (GPT, o-series) | **Vertex AI** (Gemini, Model Garden) |
| Train/deploy custom | **SageMaker** | **Azure ML** | **Vertex AI Training/Endpoints** |
| Managed RAG/vector | Bedrock Knowledge Bases | Azure AI Search | Vertex AI Search / RAG Engine |
| Guardrails/safety | Bedrock Guardrails | AI Content Safety | Vertex safety filters |
| Agents | Bedrock Agents / AgentCore | AI Foundry Agents | Vertex Agent Builder |
| Serverless inference | SageMaker Serverless | Container Apps | Cloud Run (GPU) |
| Pick when | deep AWS + Claude | Microsoft stack + GPT | data/BigQuery + Gemini |

**Managed API vs self-host:** managed = fast, no ops, per-token, less control → low/spiky
volume. Self-host (EKS+vLLM) = cheaper per token at high steady utilization, full latency/
data control → high volume. **Start managed, self-host when GPUs stay busy.**

---

## 3. Storage & Data

| Type | Examples | For | Note |
|---|---|---|---|
| Object | S3, GCS, Blob | weights, datasets, docs, checkpoints | lifecycle tiers; watch egress |
| OLTP | Postgres, Aurora, DynamoDB, Cloud SQL | app state, jobs, metadata | pgvector for modest RAG |
| Vector | Pinecone, Qdrant, Weaviate, Milvus, Vertex Search | embeddings / RAG | managed vs self-host |
| Warehouse/lake | Redshift, BigQuery, Snowflake | analytics, training data | |

**Rule:** co-locate GPUs + object store + vector DB in the **same region** → less egress,
lower latency.

---

## 4. Kubernetes for AI (quick refs)

- **GPU scheduling:** `resources.limits: nvidia.com/gpu: 1`; NVIDIA **GPU Operator**;
  **MIG** (hardware slices) + **time-slicing** (share GPU) for utilization.
- **Model server:** **vLLM** (PagedAttention + continuous batching) · TGI · Triton.
- **Autoscale (2 layers):** pods = **KEDA/HPA on queue depth / GPU util** (not CPU%);
  nodes = **Karpenter / Cluster Autoscaler** (+ spot).
- **Availability:** PodDisruptionBudgets, topology spread, warm replicas vs cold starts.

```yaml
# pin to GPU node + request a GPU
nodeSelector: { cloud.google.com/gke-accelerator: nvidia-l4 }
resources: { limits: { nvidia.com/gpu: 1 } }
```

---

## 5. Cost Levers (biggest first)

| Lever | Typical saving | How |
|---|---|---|
| Model right-sizing / routing | 40–70% | small model for easy, big for hard |
| Caching (prompt/semantic/KV) | 30–50% | reuse prefixes, near-dup answers |
| Spot for interruptible | 60–90% | batch/training/stateless replicas + queue |
| Reserved/committed baseline | 40–70% | 1–3 yr commit for steady load |
| Scale-to-zero | idle → $0 | serverless GPU, min-replica 0 off-peak |
| Utilization (batching) | big | more tokens/sec/GPU |
| Kill egress/NAT | $$ | VPC/private endpoints, co-locate data |
| Quantization | fits cheaper GPU | INT8/FP8/AWQ + eval gate |

**Billing models:** on-demand (bursty) · spot (fault-tolerant, −60–90%) · reserved/committed
(steady, −40–70%). Common mix: **reserved baseline + spot burst + on-demand buffer.**
Track **$/request** & **$/1M tokens**; tag everything; set budget/anomaly alerts.

---

## 6. High Availability & DR

| Pattern | Survives | RTO/RPO | Cost |
|---|---|---|---|
| Single region, multi-AZ | AZ outage | minutes / ~0 | $ |
| Active-passive multi-region | region outage | minutes / seconds | $$ |
| Active-active multi-region | region outage | ~0 / ~0 | $$$ (consistency hard) |

- **RTO** = how fast you recover; **RPO** = how much data you can lose. They drive design.
- Backups: vector snapshots + DB backups → object store, **versioned + cross-region
  replicated**. Keep source docs so you can **re-embed** if the index is lost.
- **Stateless inference** = respawn anywhere. **Test failover** (game days).

---

## 7. Serverless & Edge

- **Serverless inference:** scale-to-zero (SageMaker Serverless, Cloud Run GPU, Modal).
  Fight **cold start** with min warm replica, provisioned concurrency, snapshotting.
- **Edge:** small/quantized models near users → low latency + residency. **Cascade**:
  edge handles easy, escalates hard to cloud big model.

---

## 8. Security Checklist

- [ ] **Least-privilege IAM**; workload identity (IRSA/Workload Identity), no static keys.
- [ ] **Secrets manager** (Secrets Manager/Key Vault/Secret Mgr/Vault); rotate; never in
      git/images/state.
- [ ] **Private/VPC endpoints** (PrivateLink/PSC/Private Endpoint) — no public internet,
      saves egress.
- [ ] **Encryption** at rest (KMS/CMEK) + in transit (TLS/mTLS).
- [ ] **Data residency** pinned to compliant regions; verify no-train-on-your-data.
- [ ] **AI guardrails:** PII redaction, content filter, prompt-injection defense, output
      validation.
- [ ] **Audit logs** (CloudTrail/Audit Logs) → SIEM; retention policy.

---

## 9. IaC (Terraform / CDK)

- **Remote state** (S3 + DynamoDB lock / TF Cloud); **separate state per env & domain**.
- **Modules** for reuse; **pin versions**; review `plan` before `apply`; CI only, no
  laptop applies.
- **Policy as code** (OPA/Sentinel/checkov/tfsec): no public buckets, encryption required,
  approved regions/SKUs, mandatory tags.
- **Golden AMIs (Packer)** with GPU drivers/CUDA prebaked → fast, consistent node boot.
- **Never** put plaintext secrets in state → reference secrets manager.

---

## 10. Design Interview Mantra

> **Four planes:** Edge → Compute → Data, governed by Control (IaC/IAM/Observability).
> **Say out loud:** compute choice + why · autoscale on right metric · cost levers ·
> HA/RTO/RPO · data locality + egress · least-privilege + secrets + private net + encryption ·
> data residency · everything in IaC · observe latency/throughput/GPU/$-per-request.

---

## Further Reading

- Bedrock: https://docs.aws.amazon.com/bedrock/ · SageMaker: https://docs.aws.amazon.com/sagemaker/
- Vertex AI: https://cloud.google.com/vertex-ai/docs · Azure AI Foundry: https://learn.microsoft.com/azure/ai-foundry/
- vLLM: https://docs.vllm.ai/ · Karpenter: https://karpenter.sh/ · Terraform: https://developer.hashicorp.com/terraform/docs

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
