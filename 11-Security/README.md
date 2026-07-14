# 11 — AI Security

Securing AI systems against unique LLM threats plus traditional application security.

## Learning Objectives
- Understand the LLM threat model and OWASP LLM Top 10.
- Build guardrails and defenses.
- Handle data privacy and compliance.

## LLM-Specific Threats (OWASP LLM Top 10)
- **Prompt injection** (direct & indirect) — attacker overrides instructions.
- **Sensitive information disclosure** — leaking secrets/PII/system prompts.
- **Insecure output handling** — LLM output used unsanitized (XSS, SQLi, RCE).
- **Data / model poisoning** — malicious training/RAG data.
- **Excessive agency** — agents with too much unchecked power.
- **Supply chain** — compromised models/plugins/dependencies.
- **Unbounded consumption** — cost/DoS via expensive prompts.

## Defenses
- Input validation and prompt-injection filters.
- Output sanitization and sandboxing tool execution.
- Least-privilege for agent tools; human-in-the-loop for risky actions.
- Guardrail frameworks (NeMo Guardrails, Llama Guard, Rebuff).
- Rate limiting and spend caps.
- Isolating untrusted content from instructions.

## Traditional AppSec (still essential)
- AuthN/AuthZ, secrets management, encryption in transit/at rest.
- OWASP Top 10 (injection, broken access control, etc.).
- Dependency scanning and least privilege.

## Privacy & Compliance
- PII handling, redaction, and data minimization.
- GDPR, HIPAA, SOC 2 considerations.
- Data residency and retention.
- Not training on customer data without consent.

## Interview Questions
1. What is prompt injection and how do you mitigate it?
2. Direct vs indirect prompt injection?
3. What is "excessive agency" and how do you limit it?
4. How do you safely execute LLM-generated code?
5. How do you prevent secret/PII leakage from an LLM?
6. How do you secure a RAG pipeline against poisoned documents?

## Hands-On
- [ ] Build a prompt-injection test suite against your own app.
- [ ] Add input/output guardrails and a tool-execution sandbox.
- [ ] Implement PII redaction before sending data to an LLM.

## Resources
- OWASP LLM Top 10: https://genai.owasp.org/
- Llama Guard / NeMo Guardrails docs.
