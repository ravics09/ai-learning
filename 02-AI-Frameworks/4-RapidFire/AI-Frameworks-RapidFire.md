# AI Frameworks — Rapid Fire (50 one-liners)

> Fast recall drill. Cover the answer, say it out loud, check. Grouped by theme.

## Fundamentals
1. **What is an LLM framework?** Glue around the model: prompts, providers, retrieval, tools, memory, observability.
2. **When skip a framework?** Single call, latency-critical path, or it hides what you must debug.
3. **Framework = ?** A bet its abstractions match your problem; pick the lightest useful one.
4. **Mix frameworks?** Yes — they're libraries, not architecture.
5. **Biggest risk of abstraction?** It hides the real prompt/tokens/errors.

## LangChain / LCEL
6. **LCEL?** LangChain Expression Language — compose with `prompt | model | parser`.
7. **Runnable?** Shared interface: `invoke/batch/stream` + async variants.
8. **Free perks of Runnables?** Streaming, batching, async, retries.
9. **LangChain 1.0 change?** Agents run on LangGraph runtime.
10. **Where did `LLMChain` go?** Into `langchain-classic`.
11. **Output parser?** Coerces text into structured data.
12. **`with_structured_output`?** Native typed output from a chat model.
13. **Prompt template vs f-string?** Reusable, versionable, traceable, chat-aware.
14. **Callbacks?** Hooks on token/tool/error — backbone of observability.
15. **Streaming benefit?** Lower time-to-first-token, better UX.

## LangGraph
16. **LangGraph?** Runtime for stateful, cyclic, durable agents.
17. **Node?** A function that reads/writes shared state.
18. **Edge?** Routing between nodes; can be conditional.
19. **Cycle use?** Agent loop: think → act → observe → repeat.
20. **Reducer?** Rule for merging state updates (append vs replace).
21. **Checkpointing?** Persist state per step to resume after failure.
22. **Human-in-the-loop?** Pause for approval before high-stakes actions.
23. **Time-travel?** Rewind to a prior checkpoint to debug.
24. **DAG vs LangGraph?** DAGs can't loop; LangGraph can.
25. **Philosophy?** Little abstraction — control + durability.

## LlamaIndex
26. **LlamaIndex?** Data/RAG framework connecting LLMs to your data.
27. **Connectors?** 300+ sources via LlamaHub.
28. **Node?** A chunk + metadata.
29. **Index types?** Vector, Summary, KeywordTable, PropertyGraph.
30. **Query engine?** Retrieve → rerank → synthesize answer.
31. **vs LangChain?** LlamaIndex = focused RAG; LangChain = broad app framework.
32. **Ingestion pipeline win?** Cached transformations = cheap re-ingest.

## DSPy
33. **DSPy tagline?** Programming, not prompting.
34. **Signature?** Declarative input→output contract.
35. **Module?** Strategy: Predict, ChainOfThought, ReAct.
36. **Optimizer?** Tunes prompts/demos to a metric.
37. **BootstrapFewShot?** Bootstraps few-shot examples; small data.
38. **MIPROv2?** Jointly optimizes instructions + few-shot demos.
39. **DSPy needs?** A metric and a trainset.
40. **DSPy cost?** Compile step spends LLM calls.

## Structured output
41. **Instructor?** Patches client → validated Pydantic + retries.
42. **Pydantic AI?** Full typed agent framework (tools, DI, streaming).
43. **Shape vs correctness?** Valid JSON isn't necessarily right.
44. **Enforce correctness?** Field + cross-field + grounding + judge evals.

## Foundational
45. **Tokenizer?** Text → token IDs; drives cost/latency/context.
46. **PyTorch loop?** forward → loss → zero_grad → backward → step.
47. **`train()` vs `eval()`?** Toggles dropout/batchnorm.
48. **HF `pipeline`?** One-liner task inference.
49. **PEFT/LoRA?** Freeze base, train small adapters (QLoRA adds quantization).
50. **Cost formula?** ≈ tokens × price — cut tokens, cache, cascade.

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
