# Cloud for AI — RapidFire (50 One-Liners)

> Fast recall. One question, one crisp answer. Grouped by theme. Great for last-minute
> revision or a rapid verbal round.

## Compute

1. **VM vs container?** VM = you manage the OS; container = packaged app on shared hosts.
2. **When serverless (FaaS)?** Event-driven glue; not for big GPU models (no GPU, timeouts).
3. **When self-host a model?** High steady volume, latency/data control, custom weights.
4. **When managed API?** Fast start, no ops, low/spiky volume, pay-per-token.
5. **What is serverless GPU?** Scale-to-zero GPU compute; pay only while serving.
6. **Best GPU for a 7B model?** L4/L40S/A10G — cheaper than H100 and usually enough.
7. **When H100/H200?** Training or large-model low-latency inference.
8. **What is MIG?** Hardware-partition one big GPU into isolated slices.
9. **Time-slicing?** GPU context-switches between pods; boosts utilization, no isolation.
10. **Fargate/Cloud Run good for?** CPU glue, RAG orchestration, bursty scale-to-zero.

## Managed AI Services

11. **AWS FM API?** Bedrock. **Custom ML platform?** SageMaker.
12. **Azure FM API?** Azure OpenAI / AI Foundry. **Custom?** Azure ML.
13. **GCP FM API?** Vertex AI (Gemini). **Custom?** Vertex Endpoints.
14. **Bedrock vs SageMaker one-liner?** Use a great model now vs build/serve your own.
15. **Managed RAG on AWS?** Bedrock Knowledge Bases.
16. **Bedrock Guardrails?** Content filtering + PII redaction + safety.
17. **Prompt caching benefit?** Reuse shared prefixes → 30–50% inference savings.
18. **Crossover to self-host?** When GPUs stay busy enough that $/token beats the API.

## Storage & Data

19. **Where do model weights live?** Object storage (S3/GCS/Blob).
20. **Where do embeddings live?** Vector DB (Pinecone/Qdrant/pgvector).
21. **App state?** OLTP DB (Postgres/DynamoDB).
22. **pgvector when?** Modest-scale RAG inside existing Postgres.
23. **Biggest silent cloud cost?** Egress / cross-region data transfer.
24. **Data locality rule?** Co-locate GPU + object store + vector DB in one region.

## Kubernetes

25. **Request a GPU in K8s?** `resources.limits: nvidia.com/gpu: 1`.
26. **What installs GPU drivers?** NVIDIA GPU Operator / device plugin.
27. **Top LLM serving engine?** vLLM (PagedAttention + continuous batching).
28. **Scale pods on what metric?** Queue depth / GPU util — not CPU%.
29. **Pod autoscaler?** HPA/KEDA. **Node autoscaler?** Karpenter/Cluster Autoscaler.
30. **Biggest throughput win?** Continuous batching.
31. **Survive node churn?** PodDisruptionBudgets + topology spread + warm replicas.

## Cost

32. **Spot savings?** ~60–90% off, but can be reclaimed.
33. **Reserved savings?** ~40–70% for a 1–3 yr commitment.
34. **Common billing mix?** Reserved baseline + spot burst + on-demand buffer.
35. **Cheapest request?** The one you never run — cache it.
36. **Right-sizing savings?** Route easy→small model, hard→big; 40–70%.
37. **Avoid NAT/egress fees?** VPC/private endpoints + co-locate data.
38. **Key cost metric?** $/request and $/1M tokens.
39. **Quantization benefit?** Fit bigger models on cheaper GPUs, more throughput.

## HA / DR

40. **AZ vs region?** AZ = isolated datacenter; region = geography of AZs.
41. **Minimum HA?** Multi-AZ with health checks + LB.
42. **RTO vs RPO?** Recovery time vs acceptable data loss.
43. **Active-active hardest part?** State/consistency across regions.
44. **DR for vector DB?** Snapshots + cross-region replication; re-embed from source docs.
45. **Why stateless inference?** Respawn anywhere → easy failover/scale.

## Security & IaC

46. **Least privilege?** Each service gets only the permissions it needs.
47. **Better than static keys?** Workload identity (IRSA / GKE Workload Identity).
48. **Where do secrets go?** Secrets manager/Vault; never in git/images/state.
49. **Terraform state at scale?** Remote + locked, separate per env/domain, policy-as-code.
50. **Fast GPU node boot?** Golden AMI (Packer) with drivers/CUDA prebaked.

---

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
