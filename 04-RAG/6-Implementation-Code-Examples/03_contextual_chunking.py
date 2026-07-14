"""
03 — Contextual Retrieval (Anthropic-style).

Problem: an isolated chunk loses its document context. A chunk saying
"the limit was raised to $10,000" is useless if you don't know whose limit.

Fix: before embedding, prepend a short LLM-generated context sentence that
situates the chunk within its parent document. Combined with hybrid + rerank,
this has been shown to cut retrieval failures dramatically.

Trade-off: one extra (cheap, cacheable) LLM call per chunk at index time.

Run:   python 03_contextual_chunking.py
Needs: OPENAI_API_KEY
"""
from __future__ import annotations

from openai import OpenAI

client = OpenAI()
CHAT_MODEL = "gpt-4o-mini"

CONTEXT_PROMPT = """<document>
{document}
</document>

Here is a chunk from the document:
<chunk>
{chunk}
</chunk>

Give a short (1 sentence) context that situates this chunk within the overall
document, to improve search retrieval. Answer ONLY with the context sentence."""


def contextualize(document: str, chunk: str) -> str:
    """Ask the LLM to describe how the chunk fits in the whole document."""
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[{
            "role": "user",
            "content": CONTEXT_PROMPT.format(document=document, chunk=chunk),
        }],
    )
    context = resp.choices[0].message.content.strip()
    # The stored/embedded text becomes: context + original chunk.
    return f"{context}\n\n{chunk}"


if __name__ == "__main__":
    document = (
        "2024 Premium Account Policy. This document covers benefits for Premium "
        "tier customers. Section 3: Credit Limits. The limit was raised to $10,000 "
        "for accounts in good standing as of Q3."
    )
    chunk = "The limit was raised to $10,000 for accounts in good standing as of Q3."

    print("BEFORE (ambiguous chunk):\n", chunk)
    print("\nAFTER (contextualized chunk to embed):\n", contextualize(document, chunk))
