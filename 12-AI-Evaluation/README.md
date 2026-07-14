# 12 — AI Evaluation

You can't improve what you can't measure. Evaluation is the discipline of measuring LLM/AI system quality.

## Learning Objectives
- Design evaluation datasets and metrics.
- Automate evals in CI/CD.
- Detect regressions and quality drift.

## Evaluation Types
### Offline Evaluation
- Curated test sets with expected behavior.
- Golden datasets and ground truth.
- Regression testing on prompt/model changes.

### Online Evaluation
- A/B testing, canary rollouts.
- User feedback (thumbs up/down), implicit signals.
- Production monitoring of live traffic.

## Metrics
### Classic NLP
- BLEU, ROUGE, METEOR (reference-based).
- Exact match, F1 for QA/classification.

### LLM-as-a-Judge
- Using an LLM to score outputs (with rubrics).
- Pairwise comparison and rankings.
- Watch for bias (position, verbosity, self-preference).

### RAG Metrics
- Faithfulness, answer relevance, context precision/recall.
- Retrieval: precision@k, recall@k, MRR, nDCG.

### Agent Metrics
- Task success rate, tool-call accuracy, step efficiency, cost per task.

## Frameworks & Tools
- RAGAS, DeepEval, TruLens, promptfoo, LangSmith, Langfuse, OpenAI Evals.

## Interview Questions
1. How do you evaluate an LLM app without ground truth?
2. What is LLM-as-a-judge and what are its pitfalls?
3. How do you evaluate a RAG system's retrieval vs generation separately?
4. How do you catch regressions when changing a prompt or model?
5. Which metrics matter for an agent?
6. Offline vs online evaluation — when to use each?

## Hands-On
- [ ] Build a golden dataset and run automated evals in CI.
- [ ] Implement an LLM-as-judge scorer with a clear rubric.
- [ ] Add a RAGAS pipeline and track scores over time.

## Resources
- RAGAS: https://docs.ragas.io/
- promptfoo: https://www.promptfoo.dev/
