"""
agent_memory.py
===============
A minimal but realistic MEMORY system for agents, dependency-free (pure stdlib) so you can
study the mechanics without a vector DB. In production you'd swap the in-memory store for
FAISS / pgvector / Pinecone, and the toy embedding for a real embedding model.

WHY memory is mostly "context management":
    LLM calls are stateless and the context window is finite. The skill is deciding WHAT to
    store (write policy) and WHAT to inject (retrieval), not the storage tech itself. This
    file makes those two decisions explicit.

Shows:
    - Short-term (working) memory: the current conversation buffer, with compaction.
    - Long-term semantic memory: embed -> store -> retrieve top-k by cosine similarity.
    - A write policy (only store 'salient' facts) and a retrieval budget (cap top-k).

Run:  python agent_memory.py
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Toy embedding: bag-of-words vector. NOT semantic — just enough to demonstrate the
# retrieve-top-k mechanic offline. Replace with a real embedding model in practice.
# ---------------------------------------------------------------------------
def embed(text: str) -> Counter:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return Counter(tokens)


def cosine(a: Counter, b: Counter) -> float:
    shared = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in shared)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


# ---------------------------------------------------------------------------
# LONG-TERM SEMANTIC MEMORY
# ---------------------------------------------------------------------------
@dataclass
class MemoryItem:
    text: str
    vector: Counter


class LongTermMemory:
    def __init__(self, min_relevance: float = 0.1):
        self._items: list[MemoryItem] = []
        # WHY: a relevance floor stops junk from being injected just because it's top-k.
        self.min_relevance = min_relevance

    def write(self, text: str) -> None:
        """Write policy: only store salient, non-duplicate facts.
        WHY: storing everything creates noise, cost, and worse retrieval later."""
        if not _is_salient(text):
            return
        vec = embed(text)
        for item in self._items:                     # cheap dedupe
            if cosine(item.vector, vec) > 0.95:
                return
        self._items.append(MemoryItem(text, vec))

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        """Return up to k relevant memories above the relevance floor.
        WHY cap k: retrieved memory competes with the task for context tokens."""
        q = embed(query)
        scored = sorted(((cosine(q, it.vector), it.text) for it in self._items),
                        reverse=True)
        return [text for score, text in scored[:k] if score >= self.min_relevance]


def _is_salient(text: str) -> bool:
    """Heuristic write filter. Real systems use an LLM or rules to extract durable facts."""
    keywords = ("prefer", "name is", "allerg", "deadline", "goal", "always", "never")
    return any(kw in text.lower() for kw in keywords)


# ---------------------------------------------------------------------------
# SHORT-TERM (WORKING) MEMORY with compaction
# ---------------------------------------------------------------------------
@dataclass
class WorkingMemory:
    max_turns: int = 6
    _buffer: list[str] = field(default_factory=list)
    summary: str = ""

    def add(self, turn: str) -> None:
        self._buffer.append(turn)
        if len(self._buffer) > self.max_turns:
            # COMPACTION: fold the oldest turns into a rolling summary instead of dropping
            # them. WHY: keeps older context available cheaply without blowing the window.
            old = self._buffer[: -self.max_turns]
            self._buffer = self._buffer[-self.max_turns:]
            self.summary = (self.summary + " " + " | ".join(old)).strip()

    def context(self) -> str:
        parts = []
        if self.summary:
            parts.append(f"[summary] {self.summary}")
        parts.extend(self._buffer)
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Putting it together: each turn we RETRIEVE relevant long-term memory, build context,
# and WRITE back any salient new facts.
# ---------------------------------------------------------------------------
def assemble_prompt(user_msg: str, working: WorkingMemory, ltm: LongTermMemory) -> str:
    recalled = ltm.retrieve(user_msg, k=3)
    recalled_block = "\n".join(f"- {m}" for m in recalled) or "- (none relevant)"
    return (
        "=== Relevant long-term memory ===\n" + recalled_block + "\n\n"
        "=== Recent conversation ===\n" + working.context() + "\n\n"
        "=== Current message ===\n" + user_msg
    )


if __name__ == "__main__":
    ltm = LongTermMemory()
    working = WorkingMemory(max_turns=3)

    conversation = [
        "Hi! My name is Priya and I prefer concise answers.",   # salient -> stored
        "I'm allergic to peanuts.",                              # salient -> stored
        "What's the weather like today?",                        # not salient
        "Can you plan a snack for me?",                          # will recall allergy
    ]

    for msg in conversation:
        prompt = assemble_prompt(msg, working, ltm)
        print("\n--- PROMPT SENT TO LLM ---")
        print(prompt)
        working.add(f"User: {msg}")
        ltm.write(msg)   # write policy decides what actually gets persisted

    print("\n=== Stored long-term memories ===")
    for m in ltm.retrieve("snack allergy preferences", k=5):
        print(" •", m)
