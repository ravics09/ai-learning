# 03 — OpenAI / Claude (LLM APIs)

Direct integration with LLM provider APIs: OpenAI, Anthropic Claude, and compatible providers.

## Learning Objectives
- Master the request/response lifecycle for chat, tools, and streaming.
- Control cost, latency, and reliability in production.
- Understand prompt engineering and structured outputs.

## Core Topics
### Request Fundamentals
- Chat completions / messages API: roles (system, user, assistant).
- Parameters: `temperature`, `top_p`, `max_tokens`, `stop`, `seed`.
- Streaming responses (SSE) for low perceived latency.
- Multimodal inputs (images, audio, documents).

### Tool / Function Calling
- Defining tool schemas (JSON Schema).
- Parsing tool calls and returning tool results.
- Parallel tool calls and multi-turn tool loops.

### Prompt Engineering
- System prompts, few-shot examples, chain-of-thought.
- Output formatting: JSON mode, structured outputs.
- Prompt caching (Anthropic/OpenAI) to reduce cost.

### Production Concerns
- Token counting and cost estimation.
- Rate limits, retries with exponential backoff, idempotency.
- Timeouts, fallbacks, and provider failover.
- Safety, moderation, and content filtering.

## Provider Nuances
- **OpenAI**: Chat Completions, Responses API, Assistants, embeddings.
- **Anthropic Claude**: Messages API, system prompt separation, prompt caching, large context windows, tool use.

## Interview Questions
1. How does `temperature` differ from `top_p`?
2. How would you reliably get valid JSON from an LLM?
3. How do you handle rate limits at scale?
4. Explain the full tool-calling loop.
5. How do you reduce token cost for a long-running chat?
6. What is prompt caching and when does it help?
7. How do you estimate the cost of a feature before shipping?

## Hands-On
- [ ] Build a streaming chatbot with token-by-token output.
- [ ] Implement a tool-calling loop (e.g., weather + calculator).
- [ ] Add retry/backoff, timeout, and provider fallback logic.

## Resources
- OpenAI docs: https://platform.openai.com/docs
- Anthropic docs: https://docs.anthropic.com/
