# LLM Rapid Fire

> One-line questions and one-line answers. Drill until instant. Perfect for last-minute review.

---

## Fundamentals

1. **What is an LLM?** A neural net trained to predict the next token at massive scale.
2. **What is a token?** A chunk of text (~0.75 words / ~4 chars).
3. **Why sub-word tokens?** Handle rare/new words without a giant vocabulary.
4. **What is the Transformer?** Attention-based architecture behind modern LLMs.
5. **Transformer's superpower?** Self-attention + parallel training.
6. **What is attention?** Each token weighs how much to "listen to" others.
7. **Q, K, V?** Query (what I want), Key (what I offer), Value (info passed).
8. **Pretraining vs fine-tuning?** General learning vs task specialization.
9. **What is instruction tuning?** Teaching a base model to follow instructions.
10. **What is a context window?** Max tokens for prompt + response combined.

## Sampling & Decoding

11. **Temperature?** Controls randomness; low = focused, high = creative.
12. **Top-p?** Sample from smallest token set summing to p.
13. **Top-k?** Sample from k most likely tokens.
14. **Greedy decoding?** Always pick the top token.
15. **Beam search?** Track multiple candidate sequences.
16. **Temp for code/extraction?** ~0 (deterministic).
17. **Stop repetition?** Frequency/presence penalties.

## Architecture Deep Cuts

18. **Why divide by √dₖ?** Keeps softmax gradients stable.
19. **Multi-head attention?** Parallel heads learn different relationships.
20. **Why positional encoding?** Attention has no built-in order.
21. **Sinusoidal vs RoPE?** RoPE encodes relative position, extends to long context.
22. **What is the KV cache?** Stores past K/V so decode isn't recomputed.
23. **Prefill vs decode?** Prefill = compute-bound; decode = memory-bound.
24. **Pre-norm vs post-norm?** Pre-norm stabilizes deep networks.
25. **What is MoE?** Route each token to a few experts; big capacity, less compute.
26. **MoE trade-off?** Cheaper compute, still high memory.

## Fine-tuning & Alignment

27. **What is LoRA?** Train tiny adapters, freeze the base model.
28. **What is QLoRA?** 4-bit base + LoRA adapters on one GPU.
29. **What is RLHF?** Align via reward model + RL.
30. **DPO vs PPO?** DPO drops the reward model/RL; simpler and stable.
31. **PEFT?** Parameter-efficient fine-tuning (LoRA family).
32. **Fine-tune to teach facts?** No — use RAG.

## Performance & Serving

33. **What is quantization?** Lower precision weights → less memory, faster.
34. **4-bit vs 8-bit?** 8-bit near-lossless; 4-bit great sweet spot.
35. **70B in FP16 memory?** ~140GB (weights).
36. **What is vLLM known for?** Continuous batching + PagedAttention.
37. **Continuous batching?** Add/remove requests each step to keep GPU busy.
38. **PagedAttention?** KV cache managed like OS virtual memory.
39. **Speculative decoding?** Small model drafts, big model verifies — faster.
40. **TTFT vs TPOT?** Time to first token vs time per output token.
41. **Perceived latency fix?** Stream tokens.
42. **Multi-LoRA serving?** One base model + many swappable adapters.

## Cost

43. **Cost formula?** input×in_price + output×out_price.
44. **Which tokens cost more?** Output (2–4×).
45. **Top cost levers?** Caching, model routing, trim context, cap output.

## Security

46. **Prompt injection?** Malicious input overrides instructions.
47. **Indirect injection?** Injection via retrieved docs/tools.
48. **Excessive agency?** Agent with too much unchecked power.
49. **Insecure output handling?** Trusting LLM output → XSS/SQLi/RCE.
50. **Golden rule?** Never trust model/tool/retrieved input — validate everywhere.

*Rephrased for compliance with licensing restrictions.*
