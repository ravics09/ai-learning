# AI Security — Rapid Fire (50 Q&A)

> One-line answers for fast recall. Grouped by theme. Cover the terms; deep-dive lives in Detailed-Learning.

## OWASP LLM Top 10
1. **LLM01?** Prompt Injection — untrusted text overrides instructions.
2. **LLM02?** Sensitive Information Disclosure — leaking PII/secrets.
3. **LLM03?** Supply Chain — trojaned models/datasets/deps.
4. **LLM04?** Data & Model Poisoning — backdoors via tampered data.
5. **LLM05?** Improper Output Handling — output used unsafely.
6. **LLM06?** Excessive Agency — agent has too much power.
7. **LLM07?** System Prompt Leakage — secrets extracted from prompt.
8. **LLM08?** Vector & Embedding Weaknesses — RAG poisoning/cross-tenant leak.
9. **LLM09?** Misinformation — confident false output.
10. **LLM10?** Unbounded Consumption — denial-of-wallet/DoS.

## Prompt Injection
11. **Root cause?** No trust boundary between instructions and data.
12. **Direct injection?** User types malicious instructions (jailbreak).
13. **Indirect injection?** Instructions hidden in retrieved content.
14. **Cross-modal injection?** Hidden instructions in image/audio.
15. **Fully solvable?** No — reduce risk, bound blast radius.
16. **Spotlighting?** Marking untrusted text so model treats it as data.
17. **Best single defense?** Least privilege + egress control on actions.
18. **Canary tokens?** Secret markers that reveal prompt leakage (Rebuff).
19. **Why guardrails alone fail?** Documented ~100% bypass via Unicode/adversarial tricks.
20. **Jailbreak examples?** "Ignore instructions", role-play, base64/encoding.

## Defenses & Guardrails
21. **Guardrails?** Filters wrapping the LLM on input/output.
22. **Safety vs security guardrails?** Toxicity/topic vs injection/exfiltration.
23. **Llama Guard?** Open content-safety classifier.
24. **NeMo Guardrails?** Programmable rails via Colang.
25. **Guardrails AI?** Output validators + RAIL schema.
26. **Rebuff?** Multi-layer anti-prompt-injection.
27. **Presidio?** PII detection/redaction library.
28. **Order guardrails how?** Cheap deterministic first, model checks last.
29. **Fail open or closed?** Closed for irreversible actions, open (logged) for low-risk reads.
30. **Defense-in-depth?** Multiple independent layers, none trusted alone.

## Agents & Output
31. **Excessive agency fix?** Least privilege, scoped tools, HITL, audit.
32. **Run tools as whom?** The end-user, not a superuser account.
33. **Sandbox code how?** Ephemeral container, no net, RO FS, resource caps.
34. **Never do what with output?** `eval()`/exec or string-concat into SQL.
35. **HITL?** Human approval for irreversible/high-value actions.
36. **Egress control?** Allow-list outbound domains/recipients.
37. **Confused deputy?** Privileged tool tricked into misusing its authority.
38. **Bound autonomy how?** Max steps, loop detection, timeouts.
39. **Treat model output as?** Untrusted user input.
40. **Validate output with?** Strict schema (Pydantic/JSON Schema).

## RAG, Tenancy & Supply Chain
41. **Cross-tenant leak fix?** Tenant/ACL filter at retrieval, from verified token.
42. **Hard isolation?** Per-tenant namespaces/indexes.
43. **RAG poisoning?** Malicious docs surfaced as trusted context.
44. **safetensors vs pickle?** Pickle load = RCE; safetensors is safe data.
45. **AI-BOM?** Inventory of models/datasets/adapters.
46. **tenant_id source?** Always the verified auth token, never client field.

## Privacy & Compliance
47. **PII in logs?** Never raw — tokenize/hash only.
48. **Right to be forgotten + fine-tune?** Hard — prefer RAG so data is deletable.
49. **HIPAA needs?** BAA, encryption, access control, audit, minimum-necessary.
50. **GDPR breach notice?** Within 72 hours.

---

*Content synthesized from general domain knowledge and current (2025-2026) trends; rephrased for compliance with licensing restrictions.*
