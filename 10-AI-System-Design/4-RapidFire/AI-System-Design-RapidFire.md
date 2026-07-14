# AI System Design — Rapid Fire (50 One-Liners)

> Grouped, one-line Q&A for last-minute drilling. Cover the answer, guess, reveal.

## Fundamentals
1. **Why is AI system design different?** Non-deterministic, token-priced, variable latency; model is the scarce resource.
2. **Cost scales with what?** Tokens, not requests.
3. **Two phases of LLM latency?** Prefill (parallel, fast) and decode (sequential, slow).
4. **Typical decode speed?** ~30–80 tokens/sec.
5. **Best way to improve perceived latency?** Stream tokens (fast first token).
6. **What's the usual bottleneck?** The GPU/inference layer — often KV-cache memory.
7. **First-token latency target for chat?** Under ~500 ms.
8. **Golden first step in any design?** Clarify requirements; turn adjectives into numbers.

## RAG & Retrieval
9. **What is RAG?** Retrieve relevant docs at query time and put them in the prompt.
10. **What is an embedding?** A dense vector capturing meaning; similar meanings sit close.
11. **What does a vector DB do?** Fast approximate nearest-neighbor search over vectors.
12. **Common ANN indexes?** HNSW, IVF-PQ.
13. **Hybrid search?** BM25 keyword + vector, fused (RRF).
14. **Why hybrid?** Keyword nails exact IDs/jargon; vectors catch intent/paraphrase.
15. **What's a reranker?** Cross-encoder that re-scores top candidates for precision.
16. **Rerank flow?** Retrieve top-50 → rerank → keep top-5.
17. **Good chunk size?** ~300–800 tokens with 10–20% overlap.
18. **Why chunk overlap?** So answers spanning boundaries aren't cut off.
19. **Handle deletes in ANN?** Tombstones + periodic compaction/rebuild.
20. **Freshness pattern?** Hot index for recent writes merged into main index.
21. **Retrieval eval metric?** Recall@k / hit-rate.
22. **"Lost in the middle"?** Models under-use context buried in the middle of long prompts.

## Trade-offs
23. **RAG vs fine-tune?** RAG for knowledge, fine-tuning for behavior.
24. **When long context?** Small inputs, prototypes, one-off docs.
25. **Managed vs self-host — start with?** Managed; self-host for privacy/high-volume/custom.
26. **When self-host wins on cost?** High steady volume (per-token economics).
27. **Model routing/cascade?** Cheap model first, escalate hard queries → big savings.
28. **Sync vs async?** Sync+stream for chat; async queue for long jobs.
29. **When batch?** Offline embeddings/backfills — max GPU utilization.
30. **Fine-tune to save cost?** Yes, for high-volume narrow tasks on a small model.

## Caching
31. **Exact cache?** Identical prompt → stored answer.
32. **Semantic cache?** Similar query (by embedding) → reuse answer.
33. **Prompt/KV cache?** Reuse compute for shared prefixes (system prompt).
34. **Typical cache hit rate?** 30–50% on repetitive traffic.
35. **Semantic cache risk?** Loose threshold returns wrong answer; can leak across tenants.

## Scale, Cost, Latency
36. **Cost formula?** in_tok×price_in + out_tok×price_out.
37. **Cut latency in RAG?** Stream, tune ANN, smaller prompt, cache, faster model.
38. **Cut cost at scale?** Cache + routing + prompt hygiene + budgets.
39. **Vector storage math?** vectors × dim × 4 bytes (÷4 with int8).
40. **Quantization benefit?** ~4× smaller memory, small recall loss.
41. **Continuous batching?** New requests join the running batch each step → higher GPU throughput.
42. **Speculative decoding?** Small draft model proposes tokens the big model verifies.

## Reliability & Security
43. **Provider outage plan?** Multi-provider fallback + circuit breaker.
44. **Rate limit (429) handling?** Backoff + jitter + token bucket + queue.
45. **Degradation ladder?** Full → cached → smaller model → template → retry-later.
46. **#1 LLM security threat?** Prompt injection.
47. **Injection defense?** Separate trusted/untrusted content, least-privilege tools, validate outputs.
48. **Tenant isolation in RAG?** tenant_id on every vector + mandatory query filter; per-tenant namespace.
49. **Agent runaway control?** Step caps, token budgets, timeouts, tool allow-lists, human approval.
50. **Monitoring non-deterministic systems?** Traces + quality evals (golden set + LLM-judge) + op metrics.

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
