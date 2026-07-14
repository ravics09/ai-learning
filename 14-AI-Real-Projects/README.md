# 14 — AI Real Projects

Portfolio projects that prove real-world AI engineering skill. Ship, document, and demo these.

## Why Projects Matter
Interviews increasingly test *building*, not trivia. A strong portfolio of shipped projects (with code, README, demo, and eval numbers) beats any certificate.

## Project Ideas (increasing difficulty)

### Beginner
1. **Chat with your PDF** — RAG over documents with citations.
2. **AI resume analyzer** — structured output + scoring against a job description.
3. **Semantic search engine** — embeddings + vector DB over a dataset.

### Intermediate
4. **Customer support bot** — RAG + conversation memory + escalation.
5. **Code review assistant** — analyze diffs, suggest fixes.
6. **Multi-tool agent** — web search + calculator + code execution with a step budget.
7. **SQL analytics agent** — natural language to SQL over a real DB.

### Advanced
8. **Multi-agent research assistant** — supervisor + worker agents (LangGraph).
9. **LLM gateway** — routing, caching, fallback, cost tracking (LiteLLM-style).
10. **Production RAG SaaS** — multi-tenant, auth, evals, observability, deployment.
11. **Voice assistant** — STT → LLM → TTS pipeline, streaming.
12. **Agentic coding tool** — plans and edits a codebase with guardrails.

## What Each Project Should Include
- [ ] Clear README: problem, architecture diagram, setup, demo.
- [ ] Clean, typed, tested code.
- [ ] Evaluation numbers (quality, latency, cost).
- [ ] Deployment (containerized + hosted) where possible.
- [ ] Observability (traces, cost tracking).
- [ ] Notes on trade-offs and what you'd do next.

## Interview Talking Points (per project)
- What problem did it solve and for whom?
- Key architecture decisions and trade-offs.
- How did you evaluate quality?
- How did you control cost and latency?
- What broke, and how did you fix it?
- What would you improve with more time?

## Suggested Path
Ship 1 beginner → 2 intermediate → 1 advanced project, each fully documented in its own subfolder here.
