# 02 — AI Frameworks

Frameworks that let you build LLM-powered applications: orchestration, chaining, memory, and tool use.

## Learning Objectives
- Understand the role and trade-offs of each major framework.
- Build chains, agents, and RAG pipelines with abstractions.
- Know when to use a framework vs. raw API calls.

## Core Frameworks
### LangChain / LangGraph
- Chains, prompts, output parsers, and runnables (LCEL).
- LangGraph for stateful, multi-step, cyclic agent workflows.
- Memory, callbacks, and streaming.

### LlamaIndex
- Data connectors, indexing, and query engines.
- Strong focus on RAG and structured retrieval.

### Others to Know
- **Haystack** — production RAG pipelines.
- **DSPy** — programming (not prompting) LLMs; optimizers.
- **Semantic Kernel** — Microsoft's orchestration SDK.
- **Pydantic AI / Instructor** — structured, typed LLM outputs.

## Deep Learning Frameworks (foundational)
- **PyTorch** — dominant research + production framework.
- **TensorFlow / Keras** — production and mobile.
- **Hugging Face Transformers** — pretrained models, pipelines, tokenizers.

## Interview Questions
1. When would you use LangChain vs. calling the model API directly?
2. Explain the difference between a chain and an agent.
3. How does LangGraph handle state and cycles?
4. What problems does DSPy solve compared to manual prompting?
5. How do you enforce structured output from an LLM?
6. What is a tokenizer and why does it matter for cost/latency?

## Hands-On
- [ ] Build the same RAG app twice: once with LangChain, once with raw API calls.
- [ ] Build a multi-node LangGraph agent with a tool-calling loop.
- [ ] Use Instructor/Pydantic to get validated JSON from an LLM.

## Resources
- LangChain docs: https://python.langchain.com/
- LlamaIndex docs: https://docs.llamaindex.ai/
- Hugging Face: https://huggingface.co/docs
