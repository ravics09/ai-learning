# OpenAI / Claude API — Rapid Fire (50 Q&A)

> One-line answers for fast revision. Grouped by theme.

## Fundamentals
1. **What's the core primitive of both APIs?** Messages in, tokens out.
2. **OpenAI's classic chat endpoint?** Chat Completions (`/v1/chat/completions`).
3. **OpenAI's newer stateful surface?** Responses API (March 2025).
4. **Anthropic's chat endpoint?** Messages API (`/v1/messages`).
5. **Where does Claude's system prompt go?** Top-level `system` field, not a message.
6. **Are these APIs stateful?** Chat Completions & Messages are stateless; Responses can hold state (`previous_response_id`).
7. **What's a token?** Sub-word unit; ~4 chars ≈ 1 token.
8. **Roughly how many tokens per English word?** ~0.75.

## Roles & messages
9. **Three main roles?** system, user, assistant (+ tool).
10. **How is memory kept in stateless APIs?** Resend the whole message history each turn.
11. **Claude tool-result envelope?** `user` message with a `tool_result` block.
12. **OpenAI tool-result envelope?** role `tool` keyed by `tool_call_id`.

## Sampling params
13. **temperature at 0 does what?** Near-greedy, focused output (not perfectly reproducible).
14. **top_p meaning?** Nucleus sampling — keep smallest token set with cumulative prob ≥ p.
15. **Tune temperature and top_p together?** No — tune one.
16. **What does `max_tokens` cap?** Output tokens generated.
17. **Is `max_tokens` required on Anthropic?** Yes.
18. **What's `seed` for (OpenAI)?** Best-effort reproducibility (with `system_fingerprint`).
19. **stop sequences do what?** End generation when a string appears.

## Streaming
20. **Streaming protocol?** Server-Sent Events (SSE).
21. **Main benefit of streaming?** Lower time-to-first-token / perceived latency.
22. **How to still get usage while streaming (OpenAI)?** `stream_options={"include_usage":true}`.
23. **Streaming gotcha with tools?** Args arrive as fragments — accumulate before parsing.
24. **Proxy issue with streaming?** Disable response buffering (`X-Accel-Buffering: no`).

## Tool calling
25. **Who executes tools?** Your code — never the model.
26. **How are tools described?** JSON Schema (name + description + params).
27. **Signal that the model wants a tool?** `finish_reason=tool_calls` / `stop_reason=tool_use`.
28. **Parallel tool calls?** Multiple independent calls in one turn, run concurrently.
29. **When disable parallel calls?** Strict schema enforcement or ordered side-effects.
30. **Must-have safety in the tool loop?** Cap iterations to avoid infinite loops.
31. **`tool_choice` options?** auto / required / force a specific function.

## Structured output
32. **JSON mode guarantee?** Valid JSON, but not your schema.
33. **Structured Outputs guarantee?** Output matches your JSON Schema (`strict:true`).
34. **How does strict mode enforce it?** Constrained decoding to the grammar.
35. **Schema rules for strict?** All fields `required`, `additionalProperties:false`.
36. **Claude's structured-output idiom?** Force a tool whose input schema is the target.
37. **Still validate output?** Yes — shape is guaranteed, semantics aren't.

## Prompt caching
38. **OpenAI caching trigger?** Automatic on prompts ≥1024 tokens.
39. **Anthropic caching trigger?** Explicit `cache_control` breakpoints.
40. **Anthropic cache read cost?** ~0.1× input (≈90% off).
41. **Anthropic cache write cost?** ~1.25× (5-min) or ~2× (1-hour TTL).
42. **Cache design rule?** Static prefix first, dynamic last, keep prefix byte-stable.
43. **What busts the cache?** Any changed byte early in the prefix.

## Cost & performance
44. **Which tokens cost more?** Output (~4–5× input).
45. **Biggest cost lever?** Shorter output + prompt caching + model routing.
46. **Batch API discount?** ~50% off for async workloads.
47. **Reasoning-model hidden cost?** Thinking tokens billed as output.

## Reliability & security
48. **Which errors do you retry?** 429 and 5xx/timeouts — never 4xx like 400/401/422.
49. **Backoff strategy?** Exponential + full jitter, honor `Retry-After`.
50. **Top defense against indirect prompt injection?** Treat retrieved text as data + enforce authz in code, not the prompt.

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
