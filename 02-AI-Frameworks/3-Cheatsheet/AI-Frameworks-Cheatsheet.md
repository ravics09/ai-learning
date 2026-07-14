# AI Frameworks — Cheatsheet

> Dense, skim-before-the-interview reference. Comparison tables, minimal snippets, and gotchas.

---

## 1. Framework-at-a-glance

| Framework | Category | Sweet spot | Abstraction | Language |
|---|---|---|---|---|
| Raw provider SDK | — | Single/simple calls, tight latency | none | any |
| **LangChain (LCEL)** | App framework | General glue, multi-provider | medium | Py/TS |
| **LangGraph** | Agent runtime | Stateful/cyclic/durable agents, HITL | low (by design) | Py/TS |
| **LlamaIndex** | Data/RAG | Document RAG, enterprise search | medium | Py/TS |
| **DSPy** | Prompt optimization | Optimize multi-step pipelines to a metric | declarative | Py |
| **Instructor** | Structured output | Typed JSON, patch a client | very thin | Py/others |
| **Pydantic AI** | Agent framework | Typed agents + tools + DI | medium | Py |
| **Haystack** | RAG pipelines | Explicit production search/RAG graphs | medium | Py |
| **Semantic Kernel** | Orchestration | .NET/enterprise/Azure | medium | C#/Py |
| **PyTorch** | DL framework | Custom models, fine-tuning | low | Py |
| **HF Transformers** | Model library | Pretrained models, pipelines, PEFT | medium | Py |

---

## 2. Decision rules (fast)
- Single call → **raw SDK**.
- Docs Q&A → **LlamaIndex**.
- Multi-step / loops / approval → **LangGraph**.
- Typed extraction only → **Instructor**; typed agent → **Pydantic AI**.
- Optimize prompts to a metric → **DSPy**.
- General glue / swap providers → **LangChain LCEL**.
- .NET/Azure enterprise → **Semantic Kernel**.
- Custom model / fine-tune → **PyTorch + HF/PEFT**.

---

## 3. LangChain / LCEL

```python
chain = prompt | model | parser          # Runnable composition
chain.invoke(x); chain.batch([...]); chain.stream(x)   # + async a*()
model.with_structured_output(MySchema)   # native typed output
```
- Every piece = **Runnable** (`invoke/batch/stream` + async).
- **2025–2026:** LangChain 1.0; agents on LangGraph runtime; `LLMChain`/`initialize_agent` → `langchain-classic`.
- Gotcha: deep stacks hide the real prompt → always add tracing.

## 4. LangGraph

```python
builder = StateGraph(State)
builder.add_node("agent", fn); builder.add_conditional_edges("agent", route)
graph = builder.compile(checkpointer=saver)   # durability
```
- **State** (TypedDict) + **reducers** (append vs replace).
- **Cycles** allowed → agent loop. Conditional edges route.
- Killer features: **checkpointing** (resume), **human-in-the-loop**, time-travel.

## 5. LlamaIndex

```python
index = VectorStoreIndex.from_documents(SimpleDirectoryReader("data").load_data())
qe = index.as_query_engine(similarity_top_k=4); qe.query("...")
```
- Connectors (300+) → Documents → Nodes → Index → Retriever → Synthesizer.
- Indexes: Vector, Summary, KeywordTable, PropertyGraph.
- Ingestion pipeline with caching.

## 6. DSPy

```python
class QA(dspy.Signature):
    question: str = dspy.InputField(); answer: str = dspy.OutputField()
prog = dspy.ChainOfThought(QA)
compiled = dspy.MIPROv2(metric=m).compile(prog, trainset=ds)
```
- **Signature** (contract) → **Module** (Predict/ChainOfThought/ReAct) → **Optimizer**.
- Optimizers: **BootstrapFewShot** (small data), **MIPROv2** (instructions + demos jointly).
- Compile costs LLM calls; needs metric + trainset.

## 7. Instructor / Pydantic AI

```python
client = instructor.from_openai(OpenAI())
obj = client.chat.completions.create(model=..., response_model=MyModel, messages=[...])
```
| | Instructor | Pydantic AI |
|---|---|---|
| Scope | typed output | full agent framework |
| Tools/loop | ❌ | ✅ |
| Setup | patch client | define `Agent` |

Shape ✅ ≠ correctness ✅ → still eval field values.

## 8. Foundational

**PyTorch loop:** `pred=model(x)` → `loss` → `zero_grad()` → `backward()` → `step()`. `train()`/`eval()` toggles dropout/BN.

**Hugging Face:**
```python
pipeline("summarization")(text)          # one-liner inference
```
- Tokenizer → token IDs (cost/latency/context all per-token).
- `Trainer`/`TrainingArguments` for training.
- **PEFT/LoRA**: freeze base, train small adapters; QLoRA adds quantization.

---

## 9. Production checklist
- [ ] Trace every call (prompt, tokens, cost, latency, tools, retries).
- [ ] Decouple orchestration from execution (queue, not HTTP handler).
- [ ] Checkpoint long agent runs; bound loop steps.
- [ ] Timeouts + retries w/ backoff + circuit breakers; provider fallback.
- [ ] Cache (exact + semantic); model cascade for cost.
- [ ] Pin framework versions; version prompts + eval sets.
- [ ] Enforce tenant/access filters at retrieval time (fail closed).
- [ ] Gate destructive tools behind human-in-the-loop.
- [ ] Validate structured output before downstream use.

---

## 10. Common gotchas
| Gotcha | Fix |
|---|---|
| Quoting `LLMChain`/`initialize_agent` as current | Use LCEL + LangGraph |
| Assuming valid JSON = correct data | Field + cross-field + grounding evals |
| Unbounded agent loop | Cap max steps/tool calls |
| Unbounded chat history | Summarize/trim; windowed memory |
| Re-running side-effecting tools on resume | Idempotency keys |
| Injected doc text steering the agent | Treat retrieved text as data, gate tools |
| Missing tenant filter | Fail closed; physical isolation for strict tenants |
| Framework hides prompt | Tracing + escape hatches (raw call in a node) |

> Content synthesized from general domain knowledge and current (2025-2026) documentation and interview trends; rephrased for compliance with licensing restrictions.
