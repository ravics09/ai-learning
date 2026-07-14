# AI Real Projects — Rapid Fire (50 Q&A)

> 50 fast, one-line answers about the projects and how to present them. Great for last-minute revision. Grouped by theme.

---

## A. Portfolio strategy (1–8)

1. **Why do projects beat certifications?** They prove you *built* something, not just watched a course.
2. **What's the single biggest differentiator?** Real evaluation numbers, not a lucky screenshot.
3. **Depth or breadth?** Depth — two measured, deployed projects beat ten shallow demos.
4. **Minimum bar to impress?** A live/one-command demo + README + architecture diagram + eval numbers.
5. **How many projects for an "AIfolio"?** Roughly 3–5 deployed, one per key pattern.
6. **The four patterns to cover?** RAG, agents/tool-use, multi-agent orchestration, evaluation/observability.
7. **What kills a portfolio fastest?** No demo and no evals ("it works" with one screenshot).
8. **Tutorial clone — okay?** Only with a twist: your own data, a reranker, an eval, or a deployment.

## B. Chat-with-PDF / RAG (9–18)

9. **What is RAG?** Retrieve relevant text from your data, then generate an answer grounded in it.
10. **When to use RAG?** When answers need private/changing/specific facts the model doesn't know.
11. **Two phases of RAG?** Offline ingestion (chunk→embed→index) and online query (retrieve→ground→answer).
12. **Why chunk?** Right-sized chunks make retrieval precise and fit the context budget.
13. **Chunk overlap purpose?** Keeps ideas that cross a boundary from being cut in half.
14. **What's an embedding?** A vector capturing meaning so similar text sits close together.
15. **Why a vector DB?** Fast approximate nearest-neighbor search over millions of embeddings.
16. **What's hybrid search?** Combine keyword (BM25) + vector to catch both exact terms and meaning.
17. **What's a reranker?** A cross-encoder that re-scores retrieved chunks for better top-k precision.
18. **How to stop hallucination in RAG?** Ground strictly, cite sources, and allow "I don't know."

## C. Retrieval & metrics (19–26)

19. **Recall@k measures?** Whether the right chunk is in the top-k results.
20. **MRR measures?** How high the first relevant result ranks.
21. **Faithfulness measures?** Whether every claim traces back to retrieved context.
22. **Context precision vs recall?** Precision = retrieved chunks are relevant; recall = relevant chunks were retrieved.
23. **LLM-as-judge?** Use a model to score outputs against a rubric — cheap, scalable eval.
24. **Eval set size to start?** 30–100 labeled cases is enough to make decisions.
25. **Which latency number matters?** p95/p99, not the average — tails hurt UX.
26. **Name RAG eval tools.** RAGAS, DeepEval, promptfoo.

## D. Agents (27–34)

27. **Chatbot vs agent?** Chatbot answers; agent decides which tools to call and loops.
28. **What's ReAct?** Reason + act loop: think, pick a tool, observe, repeat.
29. **How to stop infinite loops?** Max-step limit, cost budget, and loop detection.
30. **What's MCP for?** A standard way to plug tools/data sources into agents.
31. **Key agent metric?** Task success rate and cost per *successful* task.
32. **Multi-agent roles example?** Planner, searcher, analyst, writer, critic.
33. **Why a critic/verifier agent?** To check claims against sources and cut hallucination.
34. **Multi-agent downside?** Slower and pricier — only justified if metrics improve enough.

## E. SQL agent & tools (35–39)

35. **How does text-to-SQL work?** Give schema → LLM writes SQL → validate → run read-only → explain.
36. **First SQL safety rule?** Read-only DB user — no writes/DDL at the database level.
37. **Other SQL guards?** SELECT-only parse, table allowlist, forced LIMIT, timeout, run on a replica.
38. **Self-correction loop?** Feed the DB error back to the model to fix its query.
39. **Never let a SQL agent do what?** Run DROP/DELETE or hit production directly.

## F. Production & scale (40–46)

40. **How to scale ingestion?** Async queue + worker pool, batched embeddings, idempotent upserts.
41. **Scale query services how?** Keep them stateless behind a load balancer; scale horizontally.
42. **Cut cost without hurting quality?** Cache, route easy queries to cheap models — measure each change.
43. **Routing pitfall?** Sending everything to a cheap model can silently break the product.
44. **Autoscale on what signal?** Queue depth or latency, not just CPU (LLM apps are I/O-bound).
45. **Reliability essentials?** Timeouts, retries with backoff, circuit breakers, fallback, graceful degradation.
46. **Load-test with?** k6 or Locust; watch p95/p99, cost/req, and error rate.

## G. Security & interview delivery (47–50)

47. **What is prompt injection?** Untrusted retrieved/tool text tries to override your instructions.
48. **Multi-tenant isolation rule?** Derive tenant from the auth token, filter server-side; use RLS/namespaces.
49. **How to open "walk me through a project"?** Problem → design + key decision → a metric → demo.
50. **The tradeoff sentence?** "I chose X over Y because Z, verified with metric M; downside W, fixable by V."

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
