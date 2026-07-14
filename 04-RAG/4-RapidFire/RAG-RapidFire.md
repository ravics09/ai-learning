# RAG Rapid Fire

> One-line questions and one-line answers. Drill these out loud until they're instant. Great for the last 30 minutes before an interview.

---

## Fundamentals

1. **What is RAG?** Fetch relevant docs at query time and feed them to the LLM as context.
2. **Why RAG?** Fixes knowledge cutoff, private data, and hallucination.
3. **RAG vs fine-tuning?** RAG changes *what the model knows*; fine-tuning changes *how it behaves*.
4. **Pipeline order?** Load → Chunk → Embed → Store → Retrieve → Rerank → Generate → Cite.
5. **What is an embedding?** A vector capturing meaning; similar text → nearby vectors.
6. **Why chunk?** Size limits, precise retrieval, lower cost.
7. **Default chunk size?** 256–512 tokens, ~50 overlap.
8. **What is top-k?** Return the k most similar chunks.
9. **Best similarity metric for text?** Cosine.
10. **What is a vector DB?** Store + fast nearest-neighbor search over embeddings.

## Retrieval Depth

11. **What is hybrid search?** Dense (vectors) + sparse (BM25) combined.
12. **How to combine rankings?** Reciprocal Rank Fusion (RRF).
13. **What is reranking?** Cross-encoder rescoring of a shortlist for precision.
14. **Bi-encoder vs cross-encoder?** Bi = fast/separate; cross = accurate/joint.
15. **What is HyDE?** Embed a hypothetical answer, search with it.
16. **What is multi-query?** Search several rephrasings, merge results.
17. **Why query rewriting in chat?** Resolve "that/it" into a standalone question.
18. **What is contextual retrieval?** Prepend chunk-level context before embedding.
19. **What is parent-document retrieval?** Retrieve small, answer with the larger parent.
20. **Lost in the middle?** LLMs ignore info stuck in the middle of long context.

## Evaluation

21. **Two eval layers?** Retrieval and generation.
22. **Retrieval metrics?** Recall@k, Precision@k, MRR, nDCG.
23. **Generation metrics?** Faithfulness, answer relevance, context precision/recall.
24. **Eval tools?** RAGAS, DeepEval, TruLens.
25. **What is a golden set?** Curated Q&A used to gate deploys.
26. **LLM-as-judge risk?** Bias toward longer answers and its own style.
27. **Low faithfulness, high recall = ?** Generation/prompt problem.
28. **Low recall = ?** Retrieval problem.

## Security

29. **Indirect prompt injection?** Malicious instructions inside retrieved docs.
30. **Multi-tenant safety?** Pre-filter `tenant_id`/ACL inside the query.
31. **Pre vs post filter for security?** Always pre-filter.
32. **Data poisoning?** Attacker seeds docs to spread false info.
33. **Stop secret leakage?** Redact at ingestion + output guardrails.

## Scale & Performance

34. **Biggest cost/latency win?** Semantic caching.
35. **What is model routing?** Cheap model for easy queries, frontier for hard.
36. **HNSW vs IVF-PQ?** HNSW = fast/RAM-heavy; IVF-PQ = compact/huge-scale.
37. **What does quantization do to vectors?** Shrinks index, minor recall loss.
38. **Latency bottleneck in RAG?** LLM generation, not retrieval.
39. **Scale ingestion how?** Async queue + incremental upserts.
40. **Change embedding model safely?** Blue-green reindex, then switch.

## Advanced Patterns

41. **What is GraphRAG?** Retrieve subgraphs from a knowledge graph; great for multi-hop.
42. **What is agentic RAG?** Agent decides when/what/whether to retrieve again.
43. **Does long context kill RAG?** No — RAG wins on cost, scale, freshness, citations.
44. **When skip RAG?** Small static data, pure reasoning, or style-only needs.
45. **How to keep answers trustworthy?** Grounding instructions + citations.

## Use Cases (one-liners)

46. **Support bot** — answer over help center with citations.
47. **Internal knowledge assistant** — search wikis/Slack/docs.
48. **Legal/medical Q&A** — grounded answers with sources.
49. **Developer copilot** — search product docs/code.
50. **Financial analysis** — Q&A over reports.

*Rephrased for compliance with licensing restrictions.*
