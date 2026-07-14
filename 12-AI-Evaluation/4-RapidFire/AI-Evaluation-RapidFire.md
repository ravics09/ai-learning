# AI Evaluation — Rapid Fire (50 Q&A)

One-line answers for quick recall and mock drills. Grouped by theme.

## A. Fundamentals

1. **Why is LLM eval hard?** Open-ended, non-deterministic, multi-dimensional — no single right answer.
2. **Offline eval?** Score a fixed golden set before deploy.
3. **Online eval?** Score real production traffic via traces after deploy.
4. **Why both?** Offline = safe to try; online = actually worked.
5. **Golden dataset?** Versioned, curated inputs + expected outputs/rubrics you score against.
6. **Ideal golden-set size?** 50–200 high-quality, stratified examples beats 10k noisy ones.
7. **Why version the dataset?** Never change dataset + model together — results become uninterpretable.
8. **What's a trace?** Per-request record: input, output, context, tools, latency, tokens, cost.
9. **First thing to build?** Tracing — every other layer sits on top of it.
10. **The layered eval system?** Deterministic → semantic/judge → human anchor → online.

## B. Reference-based metrics

11. **Exact match?** Output equals reference (after normalization); no partial credit.
12. **Token F1?** Precision/recall of overlapping tokens; partial credit for span QA.
13. **BLEU?** n-gram precision + brevity penalty; for machine translation.
14. **ROUGE?** n-gram/longest-subsequence recall; for summarization.
15. **Why BLEU/ROUGE fail on chat?** Measure word overlap, not meaning; penalize paraphrase.
16. **BERTScore?** Embedding cosine similarity of tokens; semantic, less interpretable.
17. **When use deterministic metrics?** SQL, JSON, math, classification — one right answer.
18. **pass@k?** Probability ≥1 of k code samples passes unit tests.

## C. LLM-as-judge

19. **LLM-as-judge?** A strong LLM scores another model's output against a rubric.
20. **Pointwise?** Absolute 1–5 score; drifts and clusters.
21. **Pairwise?** "A or B better?" — more reliable for nuance.
22. **G-Eval?** Chain-of-thought judging against reference/context.
23. **Position bias?** Judge favors first/last option — swap order and average.
24. **Verbosity bias?** Longer answers score higher — instruct to ignore length.
25. **Self-enhancement bias?** Judge favors its own model family — use cross-family judge.
26. **How to trust a judge?** Calibrate vs human labels with Cohen's kappa (≥ ~0.6).
27. **Judge settings for CI?** temperature=0, pinned version, structured JSON verdicts.
28. **Reward hacking risk?** Optimizing toward the judge pleases the judge, not users.

## D. RAG evaluation

29. **RAG's two halves?** Retriever and generator — measure separately.
30. **Context precision?** Fraction of retrieved chunks that are relevant / well-ranked.
31. **Context recall?** Did we retrieve all chunks needed to answer? (needs reference)
32. **Faithfulness?** Every answer claim supported by retrieved context.
33. **Answer relevance?** Does the answer address the question?
34. **Hallucination?** A claim not supported by the context.
35. **How to measure faithfulness?** Decompose into atomic claims, check each vs context.
36. **Low recall symptom?** Great-sounding answer built on incomplete evidence.

## E. Agents

37. **Why agents differ?** Multi-step trajectories, tool use / state changes, multi-turn.
38. **Task completion?** Did the agent achieve the user's goal?
39. **Tool-selection accuracy?** Chose the correct tool for the step.
40. **Trajectory efficiency?** Extra/redundant steps vs optimal path.
41. **Why not outcome-only?** Right answer via unsafe/expensive/lucky path goes undetected.
42. **Why not rigid reference-trajectory?** Many valid paths exist — too strict.

## F. CI, rollout, online

43. **Eval gating?** Block PRs if aggregate or any slice regresses vs baseline.
44. **Report average only?** No — per-slice, or a broken slice hides in the mean.
45. **Canary?** Tiny traffic % + guardrails + auto-rollback.
46. **Shadow eval?** Run new version on real inputs, hide output, compare — zero user risk.
47. **A/B test?** Split traffic, compare primary KPI with statistical significance.
48. **Explicit vs implicit feedback?** Thumbs/ratings (sparse, biased) vs edits/retries (noisy, plentiful).

## G. Benchmarks & tooling

49. **Benchmark contamination?** Test data leaked into training → inflated scores; use private held-out sets, rephrase/time-split to detect.
50. **Framework picks?** RAGAS/DeepEval for offline CI; Langfuse/LangSmith/Phoenix for online tracing; promptfoo for prompt matrix + red-team.

---

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
