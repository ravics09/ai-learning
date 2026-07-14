# Python for AI Engineering — Rapid Fire (50 one-liners)

> 50 quick Q&A for last-minute review. Say the answer out loud; if you stumble, revisit the
> Detailed-Learning guide.

## Language fundamentals

1. **Is everything an object in Python?** Yes — including functions, classes, and modules.
2. **`==` vs `is`?** `==` compares value; `is` compares identity (same object).
3. **Mutable types?** `list`, `dict`, `set`, most custom objects.
4. **Immutable types?** `int`, `float`, `str`, `bytes`, `tuple`, `frozenset`, `None`.
5. **Why must dict keys be hashable?** Hashing locates the bucket; only immutables are safely hashable.
6. **`list` vs `tuple`?** List is mutable; tuple is immutable, hashable, lighter.
7. **Shallow vs deep copy?** Shallow shares inner objects; deep clones recursively.
8. **What is truthiness?** Empty containers, `0`, `""`, `None` are falsy.
9. **`del x` frees memory?** It drops a reference; freed only when refcount hits 0.
10. **`*args` / `**kwargs`?** Collect extra positional / keyword arguments.

## Functions & scope

11. **What is a closure?** A nested function that captures enclosing-scope variables.
12. **Late-binding closure fix?** Bind with a default arg: `lambda i=i: i`.
13. **What does a decorator do?** Wraps a function to add behavior without changing it.
14. **Why `functools.wraps`?** Preserves the wrapped function's name/docstring/signature.
15. **`lru_cache` requirement?** Arguments must be hashable.
16. **`@staticmethod` vs `@classmethod`?** No `self`/`cls` vs receives `cls` (alt constructor).
17. **LEGB rule?** Name lookup order: Local, Enclosing, Global, Built-in.
18. **What is a lambda?** A small anonymous single-expression function.
19. **First-class functions?** Functions can be passed, returned, and stored like values.
20. **Positional-only / keyword-only params?** Use `/` and `*` in the signature.

## Concurrency & async

21. **What is the GIL?** A mutex allowing one thread to run Python bytecode at a time.
22. **GIL and CPU-bound threads?** No speedup — use multiprocessing or native code.
23. **GIL and I/O-bound threads?** Fine — GIL is released while waiting on I/O.
24. **When is the GIL released?** During blocking I/O and inside GIL-releasing C extensions.
25. **Free-threaded Python status?** Experimental in 3.13, supported-but-optional in 3.14 (PEP 703/779).
26. **asyncio: parallelism or concurrency?** Concurrency on a single thread.
27. **What freezes the event loop?** Any blocking/CPU call (`time.sleep`, `requests`, heavy loops).
28. **Offload blocking work in async?** `await asyncio.to_thread(fn, ...)`.
29. **Run coroutines concurrently?** `asyncio.gather(...)` or a `TaskGroup`.
30. **Cap async concurrency?** `asyncio.Semaphore(n)`.
31. **Structured concurrency in Python?** `asyncio.TaskGroup` (3.11+).
32. **multiprocessing data transfer?** Pickled and sent over pipes (spawn re-imports module).

## Memory & internals

33. **Primary memory mechanism?** Reference counting.
34. **What does the GC add?** Collects reference cycles ref-counting can't free.
35. **How many GC generations?** Three (younger scanned more often).
36. **What is `__slots__` for?** Removes per-instance dict → less memory, faster attrs.
37. **What is a descriptor?** An object with `__get__/__set__`; powers `property`, methods.
38. **What is a metaclass?** A class whose instances are classes; customizes class creation.
39. **Why doesn't memory shrink after freeing?** pymalloc retains arenas/pools.

## Data & performance

40. **Vectorization?** Replace Python loops with array ops that run in C (NumPy).
41. **Broadcasting rule?** Align shapes from the right; each dim must match or be 1.
42. **Pandas hot-path no-no?** `iterrows` — vectorize instead.
43. **Polars advantage?** Rust engine, multi-threaded, lazy query optimization, low memory.
44. **Generators save memory how?** Produce one value at a time (lazy), not a full list.
45. **Optimization order?** Algorithm → vectorize → batch → cache → concurrency → native.
46. **Profile a live prod process?** `py-spy` (sampling, no code change).

## Tooling & production

47. **2025-2026 default packager?** `uv` (Rust, 10-100x faster, universal lockfile).
48. **Load a model in FastAPI where?** Once at startup via `lifespan`, kept in memory.
49. **Validate untrusted API input with?** Pydantic models at the boundary.
50. **Never unpickle what?** Untrusted data — `pickle.load` executes arbitrary code.

> Content synthesized from general domain knowledge and current (2025-2026) trends;
> rephrased for compliance with licensing restrictions.
