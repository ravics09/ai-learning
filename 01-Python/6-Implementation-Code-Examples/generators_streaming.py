"""
generators_streaming.py
=======================

Why generators matter for AI engineering: datasets and logs are often larger than
RAM, and LLM responses arrive token-by-token. Generators let us process data ONE
item at a time (lazy evaluation) so memory stays O(1) regardless of input size, and
they let us build clean, composable pipelines.

Run:  python generators_streaming.py
"""
from __future__ import annotations

import sys
from collections.abc import Iterator, Iterable


# ---------------------------------------------------------------------------
# 1. A source generator.
# `yield` turns this function into a generator: each call to next() runs the body
# until the next yield, produces one value, then PAUSES (keeping local state).
# Nothing is computed until someone iterates — this is lazy evaluation.
# ---------------------------------------------------------------------------
def generate_events(n: int) -> Iterator[dict]:
    for i in range(n):
        # In real life this might read one line from a 50GB file or one row from a DB
        # cursor. The point: we never hold all n items in memory at once.
        yield {"id": i, "value": i % 7, "kind": "click" if i % 3 == 0 else "view"}


# ---------------------------------------------------------------------------
# 2. Pipeline STAGES that are themselves generators.
# Each stage takes an iterable and yields transformed items. Because they're lazy,
# chaining them does NOT create intermediate lists — one item flows end-to-end.
# ---------------------------------------------------------------------------
def only_clicks(events: Iterable[dict]) -> Iterator[dict]:
    for e in events:
        if e["kind"] == "click":
            yield e


def add_score(events: Iterable[dict]) -> Iterator[dict]:
    for e in events:
        # Pretend this is an expensive transform (feature engineering / embedding).
        yield {**e, "score": e["value"] * 1.5}


def batched(iterable: Iterable[dict], size: int) -> Iterator[list[dict]]:
    """Group a stream into fixed-size batches WITHOUT materializing everything.

    WHY batch? Amortize per-call overhead — e.g., send `size` texts to an embedding
    API in one request instead of one call per item. (Python 3.12+ has
    itertools.batched; this hand-rolled version explains the mechanics.)
    """
    batch: list[dict] = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []          # reset; previous batch can be garbage-collected
    if batch:                   # don't forget the final partial batch
        yield batch


# ---------------------------------------------------------------------------
# 3. Simulating STREAMING LLM tokens.
# A generator is the natural way to stream tokens to a client as they're produced,
# instead of waiting for the whole response (much better perceived latency).
# ---------------------------------------------------------------------------
def stream_tokens(text: str) -> Iterator[str]:
    for word in text.split():
        yield word + " "        # each yield could be flushed to an HTTP response


def demo_memory_difference() -> None:
    """Show the memory contrast between a list and a generator for the SAME data."""
    # A list of 1,000,000 numbers materializes every element in memory.
    big_list = [x * x for x in range(1_000_000)]
    # A generator expression holds only its iteration state — a few dozen bytes.
    big_gen = (x * x for x in range(1_000_000))
    print(f"list of 1e6 ints  : {sys.getsizeof(big_list):>10,} bytes")
    print(f"generator object  : {sys.getsizeof(big_gen):>10,} bytes  <-- constant, tiny")


def main() -> None:
    # Build a lazy pipeline: events -> clicks -> scored -> batches of 4.
    # Note: nothing runs until we iterate `pipeline` below.
    events = generate_events(30)
    pipeline = batched(add_score(only_clicks(events)), size=4)

    print("Streaming batches (one item flows through at a time):")
    for i, batch in enumerate(pipeline):
        ids = [e["id"] for e in batch]
        print(f"  batch {i}: ids={ids}")

    print("\nStreaming tokens:")
    print("  ", end="")
    for token in stream_tokens("Generators stream data without loading it all"):
        sys.stdout.write(token)   # imagine flushing each token to the client
        sys.stdout.flush()
    print("\n")

    demo_memory_difference()


if __name__ == "__main__":
    main()
