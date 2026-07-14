"""
01 — Chat completion + token streaming.

Streaming yields tokens as they're generated, so the user sees output
immediately (low PERCEIVED latency) even if total generation is slow.

Run:   python 01_chat_and_streaming.py
Needs: OPENAI_API_KEY
"""
from __future__ import annotations

from openai import OpenAI

client = OpenAI()
MODEL = "gpt-4o-mini"


def basic_chat(question: str) -> str:
    """Standard, non-streaming completion."""
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": question},
        ],
    )
    return resp.choices[0].message.content


def streaming_chat(question: str) -> None:
    """Stream tokens to stdout as they arrive."""
    stream = client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        stream=True,
        messages=[{"role": "user", "content": question}],
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)  # print incrementally
    print()


if __name__ == "__main__":
    print(basic_chat("In one sentence, what is an LLM?"))
    print("--- streaming ---")
    streaming_chat("List 3 uses of LLMs, briefly.")
