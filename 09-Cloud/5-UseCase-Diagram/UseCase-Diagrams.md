# Cloud for AI — Use-Case Diagrams

> Visual reference for the architectures you'll be asked to whiteboard. Each diagram has
> a short "what & why" so you can narrate it in an interview.

## Contents
1. [Scalable LLM API on the Cloud](#1-scalable-llm-api-on-the-cloud)
2. [GPU Autoscaling on Kubernetes](#2-gpu-autoscaling-on-kubernetes)
3. [Multi-Region High Availability](#3-multi-region-high-availability)
4. [Serverless Inference (scale-to-zero)](#4-serverless-inference-scale-to-zero)
5. [Managed FM Architecture (Bedrock / Vertex)](#5-managed-fm-architecture-bedrock--vertex)
6. [IaC Pipeline (Terraform/CDK)](#6-iac-pipeline-terraformcdk)
7. [Secrets Management Flow](#7-secrets-management-flow)
8. [Cost-Optimized Model Router](#8-cost-optimized-model-router)
9. [Edge + Cloud Cascade](#9-edge--cloud-cascade)

---

## 1. Scalable LLM API on the Cloud

**What:** end-to-end request path with auth, cache, routing, and autoscaled GPU serving.
**Why:** protect scarce GPUs, cut cost with cache + routing, stay elastic under load.

```mermaid
flowchart TB
    U[Clients] --> CDN[CDN + WAF]
    CDN --> GW[API Gateway: auth, rate limit, per-tenant quota]
    GW --> C{Cache hit?}
    C -->|yes| R[Return cached]
    C -->|no| RT[Model router]
    RT -->|easy| S[Small model]
    RT -->|hard| B[Large model - vLLM on GPU]
    B --> VDB[(Vector DB / RAG)]
    subgraph X[Cross-cutting]
        SEC[Secrets/KMS]
        OBS[Metrics & $/req]
        IAM[Least-priv IAM]
    end
```

---

## 2. GPU Autoscaling on Kubernetes

**What:** two-layer autoscaling — pods on serving metrics, nodes via Karpenter (spot).
**Why:** CPU% is a bad LLM signal; queue depth/GPU util react to real load.

```mermaid
flowchart LR
    ING[Ingress/gRPC] --> Q[(Queue: NATS/Redis Streams)]
    Q --> P1[vLLM pod GPU]
    Q --> P2[vLLM pod GPU]
    KEDA[KEDA/HPA<br/>queue depth + GPU util] -.scale pods.-> P1
    KEDA -.scale pods.-> P2
    KARP[Karpenter<br/>spot + reserved GPU nodes] -.add/remove nodes.-> P2
    PROM[Prometheus scrapes vLLM metrics] --> KEDA
```

---

## 3. Multi-Region High Availability

**What:** two active regions behind health-based global routing; async-replicated state.
**Why:** survive a region outage; serve users close to them; the hard part is state.

```mermaid
flowchart TB
    DNS[Global DNS: latency + health routing] --> RA
    DNS --> RB
    subgraph RA[Region A - active]
        LBA[LB] --> GA[GPU pods] --> VA[(Vector DB A)]
    end
    subgraph RB[Region B - active]
        LBB[LB] --> GB[GPU pods] --> VB[(Vector DB B)]
    end
    VA <-->|async replication| VB
    OBJ[(Object store: weights, cross-region replicated)] --> GA
    OBJ --> GB
```

---

## 4. Serverless Inference (scale-to-zero)

**What:** requests wake a GPU worker on demand; it scales back to zero when idle.
**Why:** pay nothing when idle — ideal for spiky/low-volume; manage cold starts.

```mermaid
flowchart LR
    U[Request] --> FN[Serverless GPU platform]
    FN --> W{Warm worker?}
    W -->|yes| INF[Infer immediately]
    W -->|no| CS[Cold start: pull image + load weights]
    CS --> INF
    INF --> U
    IDLE[No traffic] -.scale to 0.-> FN
```

---

## 5. Managed FM Architecture (Bedrock / Vertex)

**What:** app calls a managed foundation-model API privately, with guardrails + RAG.
**Why:** zero model ops, built-in safety, fast to ship; data stays on private network.

```mermaid
flowchart TB
    APP[App in private subnet] -->|IAM role, no keys| PL[PrivateLink / PSC endpoint]
    PL --> FM[Bedrock / Vertex FM API]
    APP --> KB[Knowledge Base / Vertex Search - RAG]
    FM --> GR[Guardrails: PII redaction, content filter]
    GR --> APP
    AUD[Audit logs: who called which model] -.records.-> FM
```

---

## 6. IaC Pipeline (Terraform / CDK)

**What:** infra changes flow through Git → CI checks → reviewed plan → automated apply.
**Why:** repeatable, reviewable, auditable; policy-as-code blocks insecure resources.

```mermaid
flowchart LR
    DEV[Git PR: .tf / CDK] --> CI[CI: fmt, validate, tfsec/checkov, OPA]
    CI --> PLAN[terraform plan]
    PLAN --> REV[Human review]
    REV --> APPLY[CD: terraform apply]
    APPLY --> CLOUD[(Cloud resources)]
    STATE[(Remote state: S3 + DynamoDB lock)] --- APPLY
    AMI[Golden AMI - Packer, GPU drivers baked] --> APPLY
```

---

## 7. Secrets Management Flow

**What:** apps fetch short-lived secrets at runtime from a manager; nothing hardcoded.
**Why:** no secrets in git/images/state; rotation + least-privilege limit blast radius.

```mermaid
flowchart LR
    POD[Service pod] -->|workload identity| SM[Secrets Manager / Vault]
    SM -->|short-lived, injected| POD
    KMS[KMS / CMEK] --> SM
    ROT[Auto-rotation] --> SM
    POD -->|uses secret| DB[(Database / API)]
    NOTE[No secrets in git, images, or TF state]
```

---

## 8. Cost-Optimized Model Router

**What:** a router sends each request to the cheapest capable model, cache-first.
**Why:** most traffic is easy — small models + cache handle it; big model only when needed.

```mermaid
flowchart TB
    Q[Query] --> CACHE{Semantic cache?}
    CACHE -->|hit| DONE[Return cached]
    CACHE -->|miss| CLASS[Classify difficulty]
    CLASS -->|easy| SM[Small/cheap model]
    CLASS -->|medium| MID[Mid model]
    CLASS -->|hard| BIG[Large model]
    SM --> LOG[Log tokens + $/req]
    MID --> LOG
    BIG --> LOG
```

---

## 9. Edge + Cloud Cascade

**What:** a small quantized model at the edge answers easy/latency-critical requests and
escalates hard ones to a large cloud model.
**Why:** low latency + data locality for common cases; full power only when required.

```mermaid
flowchart LR
    U[User] --> EDGE[Edge: small quantized model]
    EDGE -->|confident| U
    EDGE -->|low confidence / complex| CLOUD[Cloud: large model]
    CLOUD --> U
```

---

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
