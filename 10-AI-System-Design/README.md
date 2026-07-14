# 10 — AI System Design

Designing scalable, reliable, cost-effective AI systems — the most important interview round for senior AI engineers.

## Learning Objectives
- Design end-to-end AI systems under real constraints.
- Reason about latency, cost, scale, and reliability trade-offs.
- Communicate architecture clearly.

## Framework for AI System Design
1. **Clarify requirements**: users, scale, latency SLOs, budget, quality bar.
2. **Define functional + non-functional requirements.**
3. **High-level architecture**: ingestion, retrieval, model, serving, storage.
4. **Deep dive** on the hard components.
5. **Address scale, cost, latency, and failure modes.**
6. **Evaluation & monitoring.**

## Key Building Blocks
- API gateway, load balancing, rate limiting.
- LLM inference layer (managed vs self-hosted, vLLM).
- RAG layer: vector DB, retrieval, reranking.
- Caching: semantic cache, prompt cache.
- Async processing: queues for long jobs.
- Guardrails and moderation.
- Observability and evaluation loops.

## Trade-offs to Master
- **RAG vs fine-tuning vs long context.**
- **Managed API vs self-hosted model.**
- **Latency vs cost vs quality.**
- **Streaming vs batch.**
- **Sync vs async request handling.**

## Common Design Questions
1. Design a customer-support chatbot over company docs.
2. Design a code-assistant like Copilot.
3. Design a semantic search engine for millions of documents.
4. Design a multi-tenant RAG SaaS.
5. Design an AI agent platform with tool execution.
6. Design an LLM gateway with caching, routing, and fallback.

## Scaling & Reliability
- Handle rate limits and provider outages (fallback/failover).
- Horizontal scaling of stateless services.
- Cost control: caching, model routing (cheap → expensive).
- Graceful degradation.

## Interview Questions
1. How do you reduce latency in a RAG system?
2. How do you control cost at scale?
3. How do you handle provider outages?
4. RAG vs fine-tuning for a given problem — how do you decide?
5. How do you make an LLM system multi-tenant and secure?

## Hands-On
- [ ] Write a design doc for an LLM gateway (routing, caching, fallback).
- [ ] Diagram a production RAG SaaS architecture.

## Resources
- System Design Primer: https://github.com/donnemartin/system-design-primer
