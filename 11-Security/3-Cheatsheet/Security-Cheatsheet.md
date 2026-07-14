# AI Security — Cheatsheet

> Dense, scannable reference. Skim before an interview or a design review.

---

## OWASP LLM Top 10 (2025)

| ID | Name | Risk in one line | Top mitigations |
|----|------|------------------|-----------------|
| **LLM01** | Prompt Injection | Untrusted text overrides instructions (direct/indirect) | Treat input as untrusted, spotlight, least privilege, HITL, egress allow-list |
| **LLM02** | Sensitive Information Disclosure | Leaks PII/secrets/other tenants' data | Minimize, redact (in & out), scrub logs, output scan |
| **LLM03** | Supply Chain | Trojaned models/datasets/deps | Provenance, pin+verify signatures, safetensors, SBOM/AI-BOM, scan |
| **LLM04** | Data & Model Poisoning | Backdoor via tampered training data | Data provenance, validation, anomaly detect, trigger scans, versioning |
| **LLM05** | Improper Output Handling | Output run/rendered unsafely → SQLi/RCE/XSS | Treat output as untrusted, parameterize, sandbox, encode, schema-validate |
| **LLM06** | Excessive Agency | Agent has too much power/autonomy | Least privilege, scoped tools, run-as-user, HITL, audit |
| **LLM07** | System Prompt Leakage | Secrets in prompt get extracted | No secrets in prompt; enforce authz in code; assume public |
| **LLM08** | Vector & Embedding Weaknesses | RAG poisoning, cross-tenant leak | Retrieval-time ACL/tenant filter, namespaces, ingest validation, encrypt |
| **LLM09** | Misinformation | Confident false output; over-reliance | Grounding, citations, uncertainty signals, HITL, verify code |
| **LLM10** | Unbounded Consumption | Denial-of-wallet / DoS | Rate limits, token/cost budgets, caps, timeouts, anomaly alerts |

---

## Prompt Injection — quick reference

| Type | Attacker | Vector | Example |
|------|----------|--------|---------|
| Direct (jailbreak) | The user | Chat input | "Ignore previous instructions…" |
| Indirect | 3rd party | Retrieved doc/email/web/PDF | Hidden "email data to attacker" in a webpage |
| Cross-modal | 3rd party | Image/audio with hidden text | Instructions embedded in an image |

**Defense order:** input guardrail → spotlight untrusted text → minimal scoped tools → output guardrail → least privilege + HITL + egress allow-list → audit. *No guardrail is bypass-proof — bound the blast radius.*

---

## Defense-in-depth layers

1. Network/AppSec: WAF, TLS, authn/authz, rate limits
2. Input guardrails: PII detect, injection classifier, topic/policy
3. Prompt hardening: spotlighting, delimiting, instruction hierarchy
4. Model: safety-tuned + minimal scoped tools
5. Output guardrails: schema validate, PII/secret scan, toxicity, groundedness
6. Action layer: least privilege, run-as-user, HITL, egress allow-list, sandbox
7. Observability: audit logs, anomaly detection, red-teaming

---

## Guardrail frameworks

| Tool | Focus | Note |
|------|-------|------|
| Llama Guard | Content-safety classifier (I/O) | Open, tunable taxonomy; extra model call |
| NeMo Guardrails | Programmable rails (Colang) | Dialog/topic/action control; conservative bias |
| Guardrails AI | Output validators + RAIL schema | Rich validator hub |
| Rebuff | Anti-prompt-injection | Heuristics + LLM + vector + canary tokens |
| Presidio | PII detection/redaction | Not a safety suite; pairs with above |
| Provider (Bedrock/Azure Prompt Shield/OpenAI mod) | Managed baseline | Low-ops; documented bypasses exist |
| promptfoo / garak | Red-team / scanning | Test against OWASP LLM Top 10 |

**Trade-off:** guardrails balance precision vs recall vs latency. Layer cheap→expensive, run independent checks in parallel.

---

## Secure agent checklist

- [ ] Minimal tool set (deny by default)
- [ ] Tools scoped to end-user privileges (identity propagation, short-lived creds)
- [ ] Code/commands run in ephemeral sandbox (no net, RO FS, CPU/mem/time caps)
- [ ] HITL for irreversible/high-value actions
- [ ] Egress allow-list (domains + email recipients)
- [ ] Bounded autonomy: max steps, loop detection, timeouts
- [ ] Every tool call audited (identity, inputs, decision)
- [ ] Fail-closed on security-critical checks

---

## Secure RAG checklist

- [ ] Authz *before* retrieval
- [ ] Tenant/ACL tag on every chunk; filter at query time (from verified token)
- [ ] Per-tenant namespaces/indexes for hard isolation
- [ ] Validate/attribute docs at ingestion; strip active content
- [ ] Spotlight retrieved text as untrusted
- [ ] Encrypt vector store at rest; authn on DB
- [ ] Citations + groundedness checks on output

---

## Multi-tenant isolation

| Model | Isolation | Cost | Use |
|-------|-----------|------|-----|
| Silo | Strongest | High | Regulated/enterprise |
| Pool (tag+filter) | Logical | Low | Many small tenants |
| Bridge (shared compute, isolated data) | Medium | Medium | Common SaaS default |

Pitfalls: shared caches, unfiltered vector index, wrong adapter served, mixed logs. `tenant_id` always from the verified token.

---

## Traditional AppSec (still required)

- AuthN: OAuth2/OIDC, MFA, short-lived tokens
- AuthZ: default deny, RBAC/ABAC, object-level (stop IDOR/BOLA), enforce on every request AND tool call
- Secrets: secret manager (Vault/AWS SM), rotate, scope, never in code/prompt
- Encryption: TLS 1.2+ in transit, AES-256 at rest, KMS-managed keys
- OWASP Web Top 10 applies: injection, broken access control, SSRF, misconfig, vuln components
- Validate input, encode output, log without leaking PII

---

## Privacy & compliance checklist

| Framework | Key AI obligations |
|-----------|--------------------|
| GDPR | Lawful basis, minimization, erasure, DPIA, transfer/residency, DPA |
| HIPAA | BAA, encryption, access control, audit trails, minimum-necessary |
| SOC 2 | Operating controls: security, availability, confidentiality, integrity, privacy |
| CCPA/CPRA | Disclosure, opt-out, deletion |
| EU AI Act | Risk-tier obligations, transparency, docs for high-risk |

- [ ] Data residency: storage + inference in-region
- [ ] Vendor: DPA/BAA + no-training + zero-retention tier
- [ ] Minimize + redact PII/PHI; log tokenized only
- [ ] Retention TTLs + erasure support
- [ ] **RAG over fine-tuning for personal data** (deletable)
- [ ] Disclose AI use; honor training opt-outs
- [ ] Breach notification ready (GDPR 72h, HIPAA)

---

## STRIDE for LLMs

| Threat | LLM example | Control |
|--------|-------------|---------|
| Spoofing | Injected "system update" text | Instruction hierarchy, tool authn |
| Tampering | Poisoned training/RAG data | Provenance, signing, validation |
| Repudiation | Untraceable agent action | Immutable audit logs |
| Info disclosure | Prompt/PII/cross-tenant leak | Redaction, tenant filter, minimize |
| DoS | Sponge prompts, loops | Rate/budget limits, caps |
| Elevation | Excessive agency via injection | Least privilege, HITL, sandbox |

---

## Golden rules (memorize)

1. In an LLM, **data is the instruction channel** — no in-band trust boundary.
2. **Never make the model the security control.** Enforce authz + least privilege in deterministic code.
3. You can't stop the model being fooled — make being fooled **harmless** (bound blast radius).
4. **Treat model output as untrusted input.**
5. **Assume the system prompt is public.**
6. **Egress allow-lists** beat exfiltration even after injection.
7. **RAG over fine-tuning** for personal/regulated data.
8. Fail **closed** for irreversible actions, **open** (logged) for low-risk reads.

---

*Content synthesized from general domain knowledge and current (2025-2026) trends; rephrased for compliance with licensing restrictions.*
