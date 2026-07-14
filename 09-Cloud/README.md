# 09 — Cloud for AI

Cloud platforms provide the compute, managed AI services, and scaling infrastructure for AI applications.

## Learning Objectives
- Deploy and scale AI workloads on major clouds.
- Use managed AI/LLM services.
- Optimize for cost, security, and reliability.

## Core Topics
### Compute
- VMs, containers, serverless (Lambda/Cloud Functions).
- GPU instances and availability/quotas.
- Kubernetes (EKS/GKE/AKS).

### Managed AI Services
- **AWS**: Bedrock, SageMaker, OpenSearch (vectors).
- **Azure**: Azure OpenAI, AI Foundry, ML Studio.
- **GCP**: Vertex AI, Gemini API.

### Storage & Data
- Object storage (S3/GCS/Blob) for docs & artifacts.
- Managed databases and vector search.

### Serverless & Edge
- Deploying inference at the edge.
- Event-driven architectures (queues, pub/sub).

### Cost & Reliability
- Cost optimization: spot instances, autoscaling, caching.
- Multi-region, high availability, disaster recovery.
- Infrastructure as Code (Terraform, CDK).

## Interview Questions
1. How would you deploy a scalable LLM API on AWS?
2. Bedrock vs self-hosting a model — trade-offs?
3. How do you handle GPU cost and availability?
4. What is serverless and when is it a bad fit for AI?
5. How do you secure secrets and API keys in the cloud?
6. Explain Infrastructure as Code and its benefits.

## Hands-On
- [ ] Deploy an LLM app on AWS Bedrock or Azure OpenAI.
- [ ] Write Terraform to provision the infrastructure.
- [ ] Add autoscaling and a cost budget alarm.

## Resources
- AWS Bedrock: https://docs.aws.amazon.com/bedrock/
- Azure OpenAI: https://learn.microsoft.com/azure/ai-services/openai/
- Google Vertex AI: https://cloud.google.com/vertex-ai/docs
