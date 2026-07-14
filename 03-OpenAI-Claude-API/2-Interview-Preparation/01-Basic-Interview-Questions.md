# OpenAI / Claude APIs — Basic Interview Questions

> Foundational Q&A for getting comfortable with LLM provider APIs. Natural-tone answers with code, tables, and the *why* behind each point.

## Quick Coverage Map
| # | Question | Theme |
|---|---|---|
| 1 | What is an LLM chat/messages API? | Fundamentals |
| 2 | What are the message roles? | Roles |
| 3 | temperature vs top_p | Sampling |
| 4 | What is `max_tokens` and why set it? | Params |
| 5 | What is streaming (SSE) and why use it? | Streaming |
| 6 | How do you keep conversation memory? | State |
| 7 | What is tool/function calling? | Tools |
| 8 | How do you get reliable JSON out? | Structured output |
| 9 | What is a system prompt for? | Prompting |
| 10 | How is API cost calculated? | Cost |
| 11 | What are tokens? | Tokenization |
| 12 | OpenAI vs Claude — basic differences | Providers |

---

### 1. What is an LLM chat/messages API?
It's an HTTP endpoint where you send a **list of messages** plus parameters, and the model returns generated text (or tool calls / structured JSON). OpenAI's is **Chat Completions** (`/v1/chat/completions`) and the newer **Responses API**; Anthropic's is the **Messages API** (`/v1/messages`).

The mental model: *messages in, tokens out*. Everything fancy — tools, vision, JSON schemas, caching — is a layer on that same primitive.

```python
from openai import OpenAI
client = OpenAI()
r = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Say hi in one word."}],
)
print(r.choices[0].message.content)  # "Hi"
```

---

### 2. What are the message roles?
| Role | Meaning |
|---|---|
| **system** | Global instructions / persona / rules |
| **user** | The human's input (and retrieved context) |
| **assistant** | The model's previous replies (replayed for memory) |
| **tool** | The result of a function you ran on the model's behalf |

**Nuance:** OpenAI puts the system prompt as the *first message*. Anthropic uses a **top-level `system` field**, not a message in the list. Same idea, different placement.

---

### 3. What's the difference between `temperature` and `top_p`?
Both control randomness, but differently:
- **temperature** rescales the whole probability distribution — low (0–0.3) = focused/deterministic, high (0.8–1.2) = creative/varied.
- **top_p** (nucleus sampling) *truncates* the distribution to the smallest set of tokens whose cumulative probability ≥ p, then samples from that set.

**Why/when:** tune **one**, not both. Use low temperature for extraction/classification; higher for brainstorming/creative writing. Note even `temperature=0` isn't perfectly reproducible (floating-point + routing drift).

---

### 4. What is `max_tokens` and why should you set it?
It caps how many tokens the model may **generate**. Set it because:
- **Cost control** — output tokens cost the most (~4–5× input).
- **Latency** — decoding is sequential, so fewer output tokens = faster.
- **Safety** — prevents runaway generations.

**Gotcha:** if the model hits the cap, `finish_reason=length` and your output is **truncated** — a half-written JSON blob will break your parser. Always check the finish reason. On Anthropic, `max_tokens` is **required**.

---

### 5. What is streaming (SSE) and why use it?
Streaming sends tokens as they're generated over **Server-Sent Events**, instead of waiting for the whole response. It slashes **time-to-first-token**, so the user sees output in ~200ms instead of staring at a spinner for seconds.

```python
stream = client.chat.completions.create(model="gpt-4o", stream=True,
    messages=[{"role": "user", "content": "Count to 5"}])
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```
**Caveat:** you lose the single `usage` object — request `stream_options={"include_usage": True}` to still bill correctly.

---

### 6. How do you keep conversation memory?
In stateless APIs (Chat Completions, Messages), *you* store history and **resend the whole message list** each turn:

```python
history = [{"role": "system", "content": "You are helpful."}]
history.append({"role": "user", "content": "My name is Sam."})
# ... model replies, append it ...
history.append({"role": "assistant", "content": "Hi Sam!"})
history.append({"role": "user", "content": "What's my name?"})  # model now knows
```
**Cost implication:** every turn re-bills the entire history as input tokens — which is why long chats get expensive and why prompt caching matters. (OpenAI's Responses API can hold state server-side via `previous_response_id`.)

---

### 7. What is tool/function calling?
It lets the model **ask your code to run a function** and use the result — it never executes anything itself. You describe tools with JSON Schema; the model returns a structured call with typed arguments; you run it and feed the result back.

Loop: *send tools → model requests call → you execute → append result → call model again → final answer.* Great for weather, DB lookups, calculators, API actions. Always cap loop iterations.

---

### 8. How do you reliably get valid JSON out of an LLM?
Use the strongest mechanism available, not just prompting:
1. **Prompt** ("reply as JSON") — unreliable.
2. **JSON mode** — valid JSON, but not *your* schema.
3. **Structured Outputs** (OpenAI `json_schema` + `strict:true`) — guaranteed to match your schema via constrained decoding.
4. **Tool schema** — define the shape as a tool's parameters (works on both providers; the forced-tool trick is Claude's idiom).

Then **still validate** — shape is guaranteed, correct *values* are not.

---

### 9. What is a system prompt for?
It sets the **contract**: the model's role, scope, tone, hard rules, and output format. It's the highest-leverage place for guardrails ("only answer from the provided context; refuse otherwise"). Keep it **stable** — a steady system prompt is also your prompt-cache prefix, so it saves money too.

---

### 10. How is API cost calculated?
Per **token**, split by direction:
```
cost = input_tokens * price_in + output_tokens * price_out   (per million)
```
Output usually costs 4–5× input. Cached input tokens are heavily discounted. So the biggest levers are: **shorter outputs**, **prompt caching**, and **routing easy work to cheaper models**. Reasoning models also bill hidden "thinking" tokens as output — budget for that.

---

### 11. What are tokens?
Tokens are the sub-word chunks the model actually processes (via a tokenizer like BPE). Roughly **~4 characters ≈ 1 token** (~0.75 tokens per English word). "unhappiness" might be 2–3 tokens. Everything — context limits, pricing, latency — is measured in tokens, so count them (`tiktoken` for OpenAI, SDK `count_tokens` for Anthropic) before you send.

---

### 12. What are the basic differences between OpenAI and Claude?
| | OpenAI | Claude |
|---|---|---|
| API | Chat Completions / Responses | Messages |
| System prompt | first message | top-level `system` field |
| Tool result | role `tool` | `tool_result` block in a `user` msg |
| JSON | Structured Outputs (`json_schema`) | forced tool schema |
| Caching | automatic | explicit `cache_control` |
| Embeddings | first-party | none (use others) |

They share the same core loop; most differences are just **envelope shape**, which is why a thin adapter lets you swap between them.

---

## Further Reading
- [OpenAI API docs](https://platform.openai.com/docs)
- [Anthropic API docs](https://docs.anthropic.com/)
- [OpenAI function calling](https://platform.openai.com/docs/guides/function-calling)

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
