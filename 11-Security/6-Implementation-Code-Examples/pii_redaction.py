"""
pii_redaction.py
================
Reversible PII redaction for LLM pipelines.

WHY THIS EXISTS
---------------
You should send the model the LEAST data necessary (data minimization) and
never log raw PII (OWASP LLM02, GDPR/HIPAA). The pattern here:

    1. Detect PII in the input.
    2. Replace each occurrence with a stable placeholder like <PERSON_1>.
    3. Send the redacted text to the model.
    4. Re-insert the real values into the FINAL answer, but only for the
       authorized user. Logs keep the redacted (tokenized) form forever.

This uses regex for portability. In production, prefer Microsoft Presidio
(NER-based) for names/locations and layer regex for structured secrets.

Run:  python pii_redaction.py
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# Ordered detectors. Each entry: (label, compiled regex). Order matters so
# more specific patterns match before generic ones.
DETECTORS: List[Tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]*?){13,16}\b")),
    ("PHONE", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


@dataclass
class RedactionResult:
    redacted_text: str
    # Maps placeholder -> original value. This is the ONLY place the real
    # value lives after redaction; guard it and never write it to logs.
    mapping: Dict[str, str] = field(default_factory=dict)


def redact(text: str) -> RedactionResult:
    """Replace PII with stable placeholders. Same value -> same placeholder,
    so the model still sees consistent references (helps quality)."""
    mapping: Dict[str, str] = {}
    reverse: Dict[str, str] = {}  # original value -> placeholder (dedupe)
    counters: Dict[str, int] = {}

    def _placeholder(label: str, value: str) -> str:
        if value in reverse:
            return reverse[value]          # reuse for identical values
        counters[label] = counters.get(label, 0) + 1
        ph = f"<{label}_{counters[label]}>"
        mapping[ph] = value
        reverse[value] = ph
        return ph

    redacted = text
    for label, pattern in DETECTORS:
        # Replace right-to-left isn't needed since we re-scan the string each
        # time via sub with a function.
        redacted = pattern.sub(lambda m: _placeholder(label, m.group(0)), redacted)

    return RedactionResult(redacted_text=redacted, mapping=mapping)


def rehydrate(text: str, mapping: Dict[str, str]) -> str:
    """Put the real values back. Call this ONLY when returning the final
    answer to the authorized user — never before logging."""
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text


def safe_log_line(redacted_text: str) -> str:
    """Logs must contain tokenized text only (GDPR/HIPAA minimization)."""
    return f"[audit] processed: {redacted_text}"


def process_with_llm(user_text: str, authorized: bool = True) -> str:
    """Full flow: redact -> (model) -> log tokenized -> rehydrate for user."""
    result = redact(user_text)

    # Send ONLY the redacted text to the model.
    model_reply = _fake_model(result.redacted_text)

    # Log the tokenized form — safe to keep indefinitely.
    print(safe_log_line(result.redacted_text))

    # Only an authorized principal gets real values re-inserted.
    if authorized:
        return rehydrate(model_reply, result.mapping)
    return model_reply  # everyone else sees placeholders only


def _fake_model(redacted_prompt: str) -> str:
    """Stub: echoes back referencing placeholders, proving the model never
    saw the raw PII."""
    return f"I noted your details in: {redacted_prompt}"


if __name__ == "__main__":
    sample = (
        "Hi, I'm Jane. Email jane.doe@example.com, phone (555) 123-4567, "
        "SSN 123-45-6789. Contact me again at jane.doe@example.com."
    )
    print("ORIGINAL:", sample, "\n")

    r = redact(sample)
    print("REDACTED (sent to model & logs):", r.redacted_text)
    print("MAPPING (secret, in-memory only):", r.mapping, "\n")

    print("AUTHORIZED USER SEES:")
    print(process_with_llm(sample, authorized=True), "\n")

    print("UNAUTHORIZED VIEW SEES (placeholders only):")
    print(process_with_llm(sample, authorized=False))
