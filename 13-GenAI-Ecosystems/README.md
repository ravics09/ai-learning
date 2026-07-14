# 13 — GenAI Ecosystems

The broader generative AI landscape: models, modalities, tooling, and where the field is heading.

## Learning Objectives
- Map the GenAI ecosystem and key players.
- Understand model families and modalities.
- Stay current with fast-moving trends.

## Model Landscape
### Closed / Proprietary
- OpenAI (GPT family), Anthropic (Claude), Google (Gemini).
- xAI (Grok), Cohere.

### Open Weights
- Meta Llama, Mistral, Qwen, DeepSeek, Gemma.
- Where to find them: Hugging Face.

## Modalities
- **Text** — LLMs.
- **Image** — diffusion models (Stable Diffusion, DALL·E, Midjourney, Flux).
- **Audio/Speech** — Whisper (STT), TTS models.
- **Video** — Sora, Veo, Runway.
- **Multimodal** — vision-language models (VLMs).
- **Embeddings** — retrieval and semantic search.

## Core Concepts
- Pretraining, fine-tuning, RLHF/RLAIF, DPO.
- PEFT: LoRA, QLoRA.
- Quantization (GGUF, AWQ, GPTQ) for efficient inference.
- Context windows and long-context models.
- Mixture-of-Experts (MoE).
- Distillation and small language models (SLMs).

## Tooling Ecosystem
- Inference: vLLM, Ollama, llama.cpp, TGI.
- Orchestration: LangChain, LlamaIndex, DSPy.
- Observability: LangSmith, Langfuse.
- Vector DBs, gateways (LiteLLM), guardrails.

## Interview Questions
1. Open-weight vs proprietary models — trade-offs?
2. What is LoRA/QLoRA and why does it matter?
3. What is quantization and what does it cost you?
4. What is RLHF and how does DPO differ?
5. What is a Mixture-of-Experts model?
6. How do you decide between a large and a small model?

## Hands-On
- [ ] Run an open model locally with Ollama; compare to a hosted API.
- [ ] Fine-tune a small model with LoRA on a custom dataset.
- [ ] Use LiteLLM to route across multiple providers.

## Resources
- Hugging Face: https://huggingface.co/
- LiteLLM: https://docs.litellm.ai/
