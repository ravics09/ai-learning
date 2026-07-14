# GenAI Ecosystems — Cheatsheet

> Dense, skim-before-the-interview reference. Version numbers churn monthly — memorize the
> *shape*, not the digits.

---

## 1. Model families at a glance

| Provider | Family | Type | Sweet spot | License note |
|---|---|---|---|---|
| OpenAI | GPT / o-series | Closed | All-round, tooling, agents, computer use | API only |
| Anthropic | Claude (Opus/Sonnet/Haiku) | Closed | Coding, agentic reasoning, safe long outputs | API only |
| Google | Gemini (Pro/Flash) | Closed | Multimodal, long context, cheap quality | API only |
| Google | Gemma | Open-weight | Small on-device/edge | Gemma license |
| xAI | Grok | Closed | Real-time/web-grounded, big context | API only |
| Meta | Llama (Scout/Maverick) | Open-weight | Workhorse, ultra-long context variants | Llama community license |
| Mistral | Mistral / Mixtral | Open-weight | Efficient MoE, EU, commercial-friendly | Apache-2.0 (many) |
| Alibaba | Qwen (incl. Coder) | Open-weight | Best small dense coder, multilingual | Apache-2.0 (many) |
| DeepSeek | V3 / R1 / V4 | Open-weight | Cheap reasoning, MoE, agentic coding | MIT (many) |
| Moonshot | Kimi | Open-weight | Long context, strong open scores | Permissive |
| Zhipu | GLM | Open-weight | Clean MIT license, agentic | MIT |
| Microsoft | Phi | Open-weight | SLM, per-param reasoning, edge | MIT |
| Cohere | Command | Closed | Enterprise RAG, retrieval | API |

**Open-weight ≠ open-source.** Apache-2.0 / MIT = cleanest. Llama license has acceptable-use +
scale clauses. Always read the card.

---

## 2. Modalities & go-to tools

| Modality | Task | Open options | API options |
|---|---|---|---|
| Text | Chat/reason/code | Llama, Qwen, Mistral, DeepSeek | GPT, Claude, Gemini, Grok |
| Image gen | Text->image | Stable Diffusion/SDXL/SD3, FLUX | DALL·E, Imagen, Ideogram, Midjourney |
| STT | Speech->text | Whisper, faster-whisper | Deepgram, AssemblyAI, provider realtime |
| TTS | Text->speech | Kokoro, XTTS, Piper | ElevenLabs, OpenAI/Google voices |
| Video | Text->video | Wan, Mochi, LTX | Sora, Veo, Runway, Kling |
| Multimodal/VLM | Image+text reasoning | Qwen-VL, LLaVA, InternVL, Pixtral | GPT, Gemini, Claude |
| Embeddings | Text->vector | BGE, E5, GTE, Nomic, Jina | OpenAI text-embedding-3, Cohere, Voyage |

---

## 3. Concept glossary (one-liners)

- **Token** — sub-word unit (~4 chars EN); billing + reasoning unit.
- **Context window** — max tokens in prompt+output the model attends to.
- **Pretraining** — self-supervised next-token prediction on huge corpus -> base model.
- **SFT** — instruction tuning on prompt->response pairs.
- **RLHF** — reward model from human prefs + RL (PPO).
- **DPO** — align directly on preference pairs, no reward model.
- **RLVR** — RL with automatic verifiers (tests/math) as reward -> reasoning gains.
- **PEFT** — fine-tune a tiny extra param set instead of all weights.
- **LoRA** — trainable low-rank adapters on frozen base; hot-swappable.
- **QLoRA** — LoRA on a 4-bit base; fine-tune big models on one GPU.
- **Quantization** — fewer bits/weight -> less VRAM, faster, small quality loss.
- **MoE** — many experts + router; only a few active per token (capacity of big, cost of small).
- **Distillation** — small student mimics large teacher -> SLMs.
- **SLM** — small language model (1-14B), edge/cheap/high-volume.
- **RAG** — retrieve relevant chunks, ground the prompt.
- **Reasoning model** — spends thinking tokens; better hard tasks, slower/pricier.
- **TTFT / TPOT** — time to first token / per-token latency.
- **KV cache** — stored attention state; dominates VRAM at long context.
- **Hallucination** — confident wrong output; fix with grounding + evals.

---

## 4. Quantization formats

| Format | Bits | Runtime | Use |
|---|---|---|---|
| FP16/BF16 | 16 | all | training, full-precision serving |
| FP8/INT8 | 8 | H100/Blackwell, vLLM | high-throughput serving, tiny loss |
| GPTQ | ~4 | GPU | precise 4-bit serving |
| AWQ | ~4 | GPU (vLLM) | activation-aware 4-bit, good quality |
| GGUF (Q4_K_M...) | ~4-5 eff. | llama.cpp/Ollama | local, CPU+GPU |
| NF4 (bitsandbytes) | 4 | GPU | QLoRA training |

Rule: 4-bit local sweet spot; 8-bit/FP8 for prod; full precision for training.

---

## 5. Inference serving map

| Engine | Key tech | Best for |
|---|---|---|
| **vLLM** | PagedAttention, continuous batching | high-throughput GPU prod |
| **SGLang** | RadixAttention (prefix cache) | shared-prefix chat/RAG/agents |
| **TGI** | continuous batching, HF-native | HF-centric prod |
| **Ollama** | GGUF, one-command | local dev, single user |
| **llama.cpp** | GGUF, CPU/GPU/edge | CPU-only, portability |

Metrics: TTFT, TPOT/ITL, throughput (tok/s), goodput (under SLA).
Levers: continuous batching, prefix/KV caching, quantization, tensor parallel.

---

## 6. Tooling stack map

| Layer | Options |
|---|---|
| Orchestration | LangChain/LangGraph, LlamaIndex, DSPy, Haystack, Semantic Kernel, Pydantic AI |
| Gateway (proxy) | LiteLLM, Portkey, Kong AI Gateway, Bedrock, Vertex |
| Vector DB | pgvector, Pinecone, Qdrant, Weaviate, Milvus, Chroma |
| Observability/Evals | Langfuse, LangSmith, Arize Phoenix, OpenTelemetry GenAI |
| Guardrails | Guardrails AI, NeMo Guardrails, Llama Guard, provider moderation |
| Fine-tune | HF PEFT/TRL, Axolotl, Unsloth, LLaMA-Factory |

---

## 7. Decision rules (fast)

- Sensitive data / on-prem -> **open-weight self-host**.
- Frontier coding/reasoning now, low ops -> **closed API**.
- High volume, cost-critical -> **SLM / discount open + routing**.
- Image/audio/video -> **specialist or native multimodal**.
- Missing facts -> **RAG**; wrong behavior -> **LoRA**; big doc in hand -> **long context**.
- Single-user local -> **Ollama**; many concurrent -> **vLLM/TGI**; CPU/edge -> **llama.cpp**.
- Multi-provider resilience -> **gateway + fallback + eval gate**.

---

## 8. Cost/latency levers

Right-size + quantize · prompt/KV caching · semantic caching · RAG (shrink prompts) · continuous
batching · routing/cascade · cap max tokens · stream · distill to SLM.
Iron triangle: pick 2 of {quality, cost, latency}.

---

## 9. Security checklist (OWASP LLM themes)

Prompt injection (direct + indirect) · PII/data leakage · supply-chain (pin deps, vet gateway) ·
insecure output handling · excessive agency (sandbox tools, HITL) · governance (audit logs, eval
gates, model registry).

---

*Content synthesized from general domain knowledge and current (2025-2026) trends; rephrased for
compliance with licensing restrictions.*
