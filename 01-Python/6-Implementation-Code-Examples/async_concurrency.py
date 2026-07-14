"""
async_concurrency.py
====================

Demonstrates the concurrency patterns an AI backend actually needs: fanning out
many I/O-bound calls (model providers, vector DBs, web pages) efficiently on a
SINGLE thread with asyncio.

WHY asyncio here (and not threads/processes)?
  - This workload is I/O-bound: we spend almost all our time WAITING on the network.
  - asyncio gives us thousands of concurrent in-flight requests on one thread with
    tiny overhead, because a coroutine yields control while it waits.
  - Threads would also work for I/O (the GIL is released during I/O) but cost more
    memory per task; processes are for CPU-bound work, not this.

Run:  python async_concurrency.py
"""
from __future__ import annotations

import asyncio
import random
import time


# ---------------------------------------------------------------------------
# A fake "network call". We use asyncio.sleep to SIMULATE I/O latency.
# Crucial detail: we use `await asyncio.sleep(...)`, NOT `time.sleep(...)`.
#   - asyncio.sleep yields control back to the event loop (non-blocking).
#   - time.sleep would BLOCK the single thread and freeze every other task.
# ---------------------------------------------------------------------------
async def fake_fetch(item_id: int) -> dict:
    latency = random.uniform(0.1, 0.4)  # pretend the server responds in 100-400ms
    await asyncio.sleep(latency)        # <-- non-blocking wait; loop runs other tasks
    return {"id": item_id, "latency": round(latency, 3)}


# ---------------------------------------------------------------------------
# Pattern 1: bounded fan-out.
# We want high concurrency, but NOT unbounded — opening 10,000 sockets at once
# would exhaust file descriptors and hammer the downstream service. A Semaphore
# caps how many requests are in flight simultaneously (backpressure).
# ---------------------------------------------------------------------------
async def fetch_with_limit(sem: asyncio.Semaphore, item_id: int) -> dict:
    async with sem:                      # acquire a slot; waits if all slots are busy
        # Always bound external calls with a timeout so one slow call can't stall us.
        try:
            async with asyncio.timeout(1.0):   # 3.11+; raises TimeoutError if exceeded
                return await fake_fetch(item_id)
        except TimeoutError:
            # Degrade gracefully instead of crashing the whole batch.
            return {"id": item_id, "error": "timeout"}


async def fan_out(n: int, max_concurrency: int = 20) -> list[dict]:
    """Fetch n items concurrently, at most `max_concurrency` at a time."""
    sem = asyncio.Semaphore(max_concurrency)
    # gather schedules all coroutines on the loop and runs them concurrently.
    return await asyncio.gather(*(fetch_with_limit(sem, i) for i in range(n)))


# ---------------------------------------------------------------------------
# Pattern 2: structured concurrency with TaskGroup (3.11+).
# If ANY child task raises, the group cancels the siblings and re-raises — no
# orphaned tasks leaking in the background. Prefer this for new code.
# ---------------------------------------------------------------------------
async def structured_example() -> list[dict]:
    results: list[dict] = []

    async def worker(i: int) -> None:
        results.append(await fake_fetch(i))

    async with asyncio.TaskGroup() as tg:   # scope ends only when all tasks finish
        for i in range(5):
            tg.create_task(worker(i))
    return results


# ---------------------------------------------------------------------------
# Pattern 3: offloading BLOCKING / CPU-bound work off the event loop.
# Suppose we must call a synchronous, CPU-heavy function (e.g., a tokenizer or a
# blocking model.run()). Calling it directly would freeze the loop. asyncio.to_thread
# runs it in a worker thread so the loop keeps serving other requests.
# ---------------------------------------------------------------------------
def blocking_cpu_work(n: int) -> int:
    # Pure-Python CPU loop — the kind of thing that must NOT run on the loop thread.
    return sum(i * i for i in range(n))


async def offload_example() -> int:
    # The loop stays responsive while this runs in a separate thread.
    return await asyncio.to_thread(blocking_cpu_work, 2_000_000)


async def main() -> None:
    # --- Show the concurrency win: 100 calls of ~250ms avg would take ~25s serially,
    #     but finish in well under a second when run concurrently. ---
    start = time.perf_counter()
    results = await fan_out(100, max_concurrency=20)
    elapsed = time.perf_counter() - start
    errors = sum(1 for r in results if "error" in r)
    print(f"fan_out: fetched {len(results)} items in {elapsed:.2f}s "
          f"({errors} timeouts) — serial would be ~{sum(r.get('latency', 0) for r in results):.1f}s")

    structured = await structured_example()
    print(f"structured TaskGroup: {len(structured)} results")

    total = await offload_example()
    print(f"offloaded CPU work result: {total}")


if __name__ == "__main__":
    # asyncio.run creates the event loop, runs main() to completion, then closes it.
    asyncio.run(main())
