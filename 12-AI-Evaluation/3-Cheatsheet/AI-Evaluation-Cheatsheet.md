# AI Evaluation — Cheatsheet

Dense one-page reference. Metric tables by system type, framework comparison, and a shippable
eval checklist.

---

## The layered eval system (memorize this)

```
Deterministic checks (100% rows, ~free)  ->  Semantic + LLM-judge (CI/nightly)
        ->  Human-calibrated anchor set (weekly)  ->  Online eval on sampled traces (continuous)
```
Offline = safe to try. Online = actually worked. You need both.

---

## Metric families at a glance

| Family | Examples | Needs reference? | Best for | Weakness |
|---|---|---|---|---|
| Deterministic | exact-match, schema, regex, JSON-valid | yes/no | structured, tool args, classification | no partial credit |
| Statistical overlap | BLEU, ROUGE-1/2/L, token-F1 | yes | translation, summarization, span QA | misses meaning |
| Model-based | BERTScore, embedding cosine | yes | semantic similarity | opaque |
| LLM-as-judge | pointwise, pairwise, G-Eval | optional | open-ended quality, faithfulness | biases, cost, calibration |
| Human | ratings, pairwise | n/a | gold standard, calibration | slow, expensive |

---

## Metrics by system type

### Plain LLM
| Metric | Measures |
|---|---|
| Correctness | matches expected / gold |
| Relevance | addresses the prompt |
| Coherence / fluency | readable, consistent |
| Safety / toxicity | no harmful content |
| Format compliance | schema / JSON / length |

### RAG (measure the two halves separately)
| Metric | Half | Question | Ref? |
|---|---|---|---|
| Context precision | retriever | relevant chunks ranked high? | sometimes |
| Context recall | retriever | got ALL needed chunks? | yes |
| Context relevance | retriever | on-topic context? | no |
| Faithfulness / groundedness | generator | claims supported by context? | no |
| Answer relevance | generator | answers the question? | no |
| Answer correctness | e2e | right vs gold answer? | yes |

### Agent
| Metric | Measures |
|---|---|
| Task completion / goal success | achieved user goal |
| Tool selection accuracy | correct tool |
| Tool-arg correctness | valid args |
| Trajectory efficiency | extra/redundant steps |
| Reasoning/planning | coherent, recovers |
| Cost / latency / #steps | production budget |
| Safety | no destructive actions |

### Task-specific
| Task | Metric |
|---|---|
| Text-to-SQL | execution accuracy (rows), not string match |
| Code gen | pass@k (unit tests) |
| Summarization | faithfulness + coverage + conciseness |
| Classification/routing | accuracy, precision/recall, confusion matrix |
| Support bot | deflection, escalation, CSAT |

---

## LLM-as-judge — modes & biases

| Mode | Use when |
|---|---|
| Pointwise (1–5) | coarse thresholds, regression tracking |
| Pairwise (A vs B) | compare candidates, preference data (most reliable) |
| Reference/G-Eval | factual grounding vs context |

| Bias | Fix |
|---|---|
| Position | swap order, average, trust only consistent |
| Verbosity | ignore-length instruction, normalize |
| Self-enhancement | cross-family judge |
| Formatting | strip markdown / instruct ignore |
| Leniency | pairwise + rubric anchors |

**Always** calibrate judge↔human with **Cohen's kappa** (≥ ~0.6 to trust). temperature=0, pin
version, structured JSON verdicts.

---

## Framework comparison (2025–2026)

| Tool | Style | Layer | Strength | Watch-out |
|---|---|---|---|---|
| RAGAS | library | offline RAG | faithfulness, ctx recall/precision | RAG-only |
| DeepEval | pytest OSS | offline/CI | many metrics, G-Eval, CI-native | self-host dashboards |
| TruLens | feedback fns | RAG/agent | RAG triad instrumentation | smaller ecosystem |
| promptfoo | YAML/CLI | offline + red-team | fast prompt/model matrix | config sprawl; now OpenAI |
| LangSmith | platform | offline+online | tracing+datasets+eval, great DX | commercial, LangChain-y |
| Langfuse | OSS platform | online + prompt mgmt | self-host tracing + eval | you run infra |
| OpenAI Evals | framework | offline | standardized templates | OpenAI-centric |
| Arize Phoenix | OSS obs | online | tracing + eval, notebooks | obs-leaning |
| Braintrust | commercial | full lifecycle | eval→monitor→gate | paid |

Rule: metrics library (RAGAS/DeepEval) for CI + observability platform (Langfuse/LangSmith/Phoenix)
for online. Tool = plumbing; golden set + rubric + calibration = substance.

---

## Rollout strategies

| Strategy | What | Risk |
|---|---|---|
| Shadow | run new on real inputs, hide output, compare offline | none to users |
| Canary | 1–5% traffic + guardrails + auto-rollback | small blast radius |
| A/B | split traffic, stat-sig on primary KPI | needs volume |
| Full rollout | 100% after A/B win | — |

Guardrail metrics: latency, error rate, cost, refusal rate, safety hits.

---

## Benchmarks & contamination

| Benchmark | Tests |
|---|---|
| MMLU | 57-subject knowledge (MC) |
| GSM8K | grade-school math reasoning |
| HumanEval | Python synthesis (pass@k) |
| LMArena | human pairwise Elo |

Contamination = test data leaked into training → inflated scores. Defend: **private held-out sets**,
rephrase/perturb items, post-cutoff time-split, watch indirect (synthetic) leakage & overfitting.
Public leaderboards ≈ marketing, not your product eval.

---

## Golden dataset rules

- Source from **real prod logs** first; add edge/adversarial cases.
- **Stratify** by intent/difficulty/language; report **per-slice**.
- **Version & freeze** in Git (JSONL); never change dataset + model together.
- 50–200 great rows > 10k noisy ones.
- Isolate from training/prompt-opt data (no leakage).
- Grow it from production failures (flywheel).

---

## Ship-it eval checklist

- [ ] Tracing on: input, output, context, tools, latency, tokens, cost
- [ ] Versioned golden set, stratified, from real data
- [ ] Deterministic checks on 100% (schema, PII, guardrails)
- [ ] Semantic/judge metrics for the right system type (RAG/agent/LLM)
- [ ] Judge calibrated vs human anchor (kappa), temp=0, pinned version, bias controls
- [ ] CI gate: absolute threshold + per-slice baseline diff, blocks merge
- [ ] Report per-slice, not just average
- [ ] Shadow → canary → A/B with guardrails + stat-sig
- [ ] Online eval on sampled traces + drift alerts
- [ ] Red-team / injection suite as gated metric
- [ ] Failures fed back into golden set
- [ ] Cost/latency SLOs for judge eval (cascade, cache, sample)

---

## Quick formulas

```
Precision = relevant_retrieved / retrieved
Recall    = relevant_retrieved / all_relevant
F1        = 2·P·R / (P+R)
Faithfulness = supported_claims / total_claims
Cohen's kappa = (p_o - p_e) / (1 - p_e)   # observed vs chance agreement
pass@k   = 1 - C(n-c, k) / C(n, k)        # prob >=1 of k samples passes
```

---

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
