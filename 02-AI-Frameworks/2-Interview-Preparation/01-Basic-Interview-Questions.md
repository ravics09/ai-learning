# AI Frameworks — Basic Interview Questions

> Foundational questions you should answer instantly and confidently. Natural tone, real code, and the *why* behind each answer.

## Quick Coverage Map
| # | Question | Theme |
|---|---|---|
| 1 | What is an AI/LLM framework? | Fundamentals |
| 2 | Framework vs raw API | Trade-offs |
| 3 | What is LangChain? | LangChain |
| 4 | What is LCEL / a Runnable? | LangChain |
| 5 | Chain vs agent | Concepts |
| 6 | What is LangGraph? | LangGraph |
| 7 | What is LlamaIndex for? | LlamaIndex |
| 8 | What is a tokenizer? | Foundational |
| 9 | Prompt template vs f-string | Prompting |
| 10 | Structured output — why & how | Output |
| 11 | What is RAG (framework view)? | RAG |
| 12 | What is Hugging Face `pipeline`? | HF |

---

### 1. What is an AI/LLM framework and why use one?
An LLM is just a text-in/text-out function. A framework wraps the boring-but-necessary parts around it: prompt templating, talking to multiple providers, retrieval, memory, tool calling, retries, streaming, and observability. You use one so you don't re-implement that glue for every project.

**Why/when:** reach for a framework when the boilerplate starts hurting; skip it for a single prompt call.

---

### 2. When would you call the API directly instead of using a framework?
When the task is a single call, when you need tight control over latency (no abstraction tax), or when a framework hides something you must debug. Frameworks add layers; sometimes the layer costs more than it saves.

```python
# Raw is fine here — one prompt, one answer.
from openai import OpenAI
client = OpenAI()
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Summarize photosynthesis in one line."}],
)
print(resp.choices[0].message.content)
```

**Rule of thumb:** start raw for a spike, adopt a framework when glue accumulates. You can mix them.

---

### 3. What is LangChain?
The broadest LLM app framework: prompts, output parsers, retrievers, memory, hundreds of integrations, and the **LCEL** composition layer. It's great for gluing pieces together and swapping providers with one line.

**Heads up (2025–2026):** LangChain 1.0 shipped; agents run on the LangGraph runtime and old classes like `LLMChain`/`initialize_agent` moved to `langchain-classic`. Don't quote those as current.

---

### 4. What is LCEL and what's a Runnable?
**LCEL** (LangChain Expression Language) lets you compose components with a pipe:

```python
chain = prompt | model | parser        # each piece is a "Runnable"
chain.invoke({"topic": "APIs"})
```

Every composable piece implements the **Runnable** interface (`invoke`, `batch`, `stream`, async variants). Because they share that interface, you get **streaming, batching, and async for free** — that's the real win over hand-written glue.

---

### 5. What's the difference between a chain and an agent?
- **Chain:** a fixed sequence of steps. Same path every time. Predictable, cheap, easy to test.
- **Agent:** an LLM in a loop that *decides* which tool to call next based on results, until the task is done. Flexible but less predictable and harder to bound.

**When to use which:** known steps → chain; open-ended task needing dynamic tool use → agent. Always cap an agent's max steps.

---

### 6. What is LangGraph?
A low-level runtime for **stateful, cyclic, durable** agent workflows. You define a graph of nodes that read/write a shared typed **state**; edges (including conditional ones) decide what runs next, and cycles let the agent loop. Its big production features are **checkpointing** (resume after failure) and **human-in-the-loop** (pause for approval).

---

### 7. What is LlamaIndex best for?
Connecting LLMs to your **data**. It's a data/RAG framework with 300+ connectors and deep indexing/query primitives — the fastest path to "answer questions over my documents."

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
index = VectorStoreIndex.from_documents(SimpleDirectoryReader("data").load_data())
print(index.as_query_engine().query("What's our refund policy?"))
```

**When to use:** document Q&A, enterprise search, knowledge bases.

---

### 8. What is a tokenizer and why does it matter?
It converts text into token IDs the model consumes (and back). It matters because you pay **per token**, latency scales with tokens, and context windows are measured in tokens. "3 words" ≠ "3 tokens," and different models tokenize differently, so the same text can cost different amounts across providers.

---

### 9. Why use a prompt template instead of an f-string?
Templates are reusable, versionable, support chat roles and few-shot examples, and plug into the framework's tracing and composition. An f-string scattered across code is hard to version, test, or observe.

```python
from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_template("Translate to {lang}: {text}")
```

---

### 10. What is structured output and how do you enforce it?
Getting the model to return data in a fixed schema (e.g., JSON matching a class) instead of free text. Enforce it with **native structured output** (OpenAI/Anthropic) or a library like **Instructor** that validates against a Pydantic model and retries on failure.

```python
import instructor; from openai import OpenAI; from pydantic import BaseModel
class Person(BaseModel): name: str; age: int
client = instructor.from_openai(OpenAI())
p = client.chat.completions.create(model="gpt-4o-mini", response_model=Person,
    messages=[{"role": "user", "content": "Bob is 40"}])
```

**Nuance:** valid shape ≠ correct values. Still validate content.

---

### 11. In framework terms, what is RAG?
Retrieval-Augmented Generation: retrieve relevant chunks from an index and inject them into the prompt so the model answers from your data, not just its training. Frameworks give you the connectors, chunking, embedding, retrieval, and synthesis steps out of the box (LlamaIndex especially).

---

### 12. What does Hugging Face `pipeline` do?
It's a one-liner that wires tokenizer + model + post-processing for a task, so you can run inference without boilerplate.

```python
from transformers import pipeline
clf = pipeline("sentiment-analysis")
print(clf("I love clean abstractions."))
```

**When to use:** quick inference or prototyping with pretrained models before building anything custom.

---

## Further Reading
- LangChain: https://python.langchain.com/
- LangGraph: https://langchain-ai.github.io/langgraph/
- LlamaIndex: https://docs.llamaindex.ai/
- Instructor: https://python.useinstructor.com/
- Hugging Face: https://huggingface.co/docs/transformers/

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
