# GenAI Ecosystems — Rapid Fire (50 Q&A)

> One-line questions and answers, grouped by theme. Great for last-minute review or a
> whiteboard warm-up.

## Model Landscape (1-8)

1. **Open-weight vs open-source?** Open-weight ships weights only; open-source adds data + code.
2. **Why not just use the "best" model?** No single winner — best model depends on the job.
3. **Which provider for hard coding?** Anthropic Claude is the usual coding/agentic leader.
4. **Which for multimodal + long context + cheap?** Google Gemini.
5. **Which for real-time/web-grounded answers?** xAI Grok.
6. **Best open-weight workhorse to self-host?** Meta Llama family.
7. **Cheapest frontier-ish reasoning, open?** DeepSeek (MoE, aggressive pricing).
8. **Cleanest permissive open licenses?** Apache-2.0 / MIT (Qwen, Mistral, DeepSeek, GLM).

## Modalities (9-16)

9. **What generates images?** Diffusion / diffusion-transformer models.
10. **Default open STT model?** Whisper.
11. **What's a VLM?** Vision-Language Model — takes text + images in one context.
12. **Most compute-hungry modality?** Video generation.
13. **Are embeddings generative?** No — they map data to vectors for search/RAG.
14. **Guidance scale (CFG) controls what?** How strongly image output follows the prompt.
15. **What is TTS?** Text-to-speech (neural voice synthesis).
16. **What's an "omni" model?** One model handling text+image+audio(+video) natively.

## Core Concepts (17-28)

17. **What is a token?** ~4-char sub-word unit; billing/reasoning unit.
18. **Context window?** Max tokens (prompt+output) the model attends to.
19. **Pretraining objective?** Predict the next token (self-supervised).
20. **What is SFT?** Instruction tuning on prompt->response pairs.
21. **RLHF in one line?** Reward model from human prefs + RL to optimize.
22. **DPO advantage?** Aligns directly on pairs — no reward model or RL loop.
23. **What is RLVR?** RL with automatic verifiers (tests/math) as reward.
24. **What is PEFT?** Fine-tune a tiny extra param set, not all weights.
25. **LoRA in one line?** Train low-rank adapters on a frozen base.
26. **QLoRA adds what?** 4-bit base so you fine-tune big models on one GPU.
27. **What is MoE?** Many experts + router; only a few active per token.
28. **What is distillation?** Small student learns to mimic a large teacher.

## Quantization & Efficiency (29-35)

29. **Why quantize?** Less VRAM, faster inference, small quality loss.
30. **GGUF is for?** llama.cpp/Ollama local serving.
31. **AWQ vs GPTQ?** Both 4-bit GPU; AWQ activation-aware, GPTQ error-minimizing.
32. **Sweet-spot bit width locally?** 4-bit.
33. **Best bits for prod quality?** 8-bit / FP8.
34. **Is Q4_K_M exactly 4 bits?** No — effective ~4.9 bits/weight.
35. **What's an SLM?** Small language model (1-14B) for edge/cheap/high-volume.

## Serving & Infra (36-43)

36. **Highest-throughput GPU server?** vLLM.
37. **vLLM's key trick?** PagedAttention + continuous batching.
38. **SGLang shines when?** Shared-prefix workloads (chat/RAG) via prefix caching.
39. **HF-native serving?** TGI.
40. **Simplest local run?** Ollama (`ollama run <model>`).
41. **CPU-only / edge?** llama.cpp.
42. **What is TTFT?** Time to first token.
43. **What dominates VRAM at long context?** The KV cache.

## Tooling & Retrieval (44-47)

44. **What is an LLM gateway?** OpenAI-compatible proxy over many providers (e.g., LiteLLM).
45. **Gateway gives you?** Routing, fallback, caching, cost tracking, key mgmt.
46. **Easiest vector DB if you run Postgres?** pgvector.
47. **What does RAG reduce?** Hallucination — grounds answers in your data.

## Strategy, Security & Trends (48-50)

48. **Best cost cut at scale?** Routing/cascade + caching + RAG (often 50-80%).
49. **#1 GenAI security risk?** Prompt injection (direct and indirect).
50. **Defining 2025-2026 trend?** Agentic models + RLVR reasoning + open-weight catching up.

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends;
rephrased for compliance with licensing restrictions.*
