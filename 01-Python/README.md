# 01 — Python for AI Engineering

Python is the foundational language for AI/ML engineering. Master both the language internals and the data/ML ecosystem.

## Learning Objectives
- Write clean, idiomatic, production-grade Python.
- Understand async, concurrency, memory model, and performance.
- Be fluent with the data & AI ecosystem (NumPy, Pandas, Pydantic, FastAPI).

## Core Topics
### Language Fundamentals
- Data types, mutability, and object model (everything is an object).
- Comprehensions, generators, iterators, and lazy evaluation.
- Decorators, closures, and context managers (`with`).
- Type hints, `typing`, and static checking with `mypy`/`pyright`.
- Dataclasses vs `pydantic` models.

### Advanced Python
- `asyncio`, coroutines, event loop, `async`/`await`.
- Threading vs multiprocessing vs asyncio — and the GIL.
- Memory management, reference counting, and garbage collection.
- Context managers and the descriptor protocol.
- Metaclasses and `__slots__` (know when NOT to use them).

### AI/Data Ecosystem
- **NumPy**: vectorization, broadcasting, `ndarray` internals.
- **Pandas / Polars**: dataframes, groupby, joins, performance.
- **Pydantic**: schema validation, settings management.
- **FastAPI**: async APIs for serving models.
- **Packaging**: `uv`, `poetry`, `pip`, virtual environments.

## Interview Questions
1. Explain the GIL. How does it affect CPU-bound vs I/O-bound workloads?
2. Difference between `deepcopy` and `copy`?
3. How do generators save memory? Give a streaming example.
4. What is the difference between `@staticmethod`, `@classmethod`, and instance methods?
5. How does `asyncio` achieve concurrency without threads?
6. Explain broadcasting in NumPy with an example.
7. When would you choose multiprocessing over asyncio?
8. What are `*args` and `**kwargs`, and how does argument unpacking work?

## Hands-On
- [ ] Build a rate-limited async web scraper using `asyncio` + `httpx`.
- [ ] Implement an LRU cache from scratch, then compare with `functools.lru_cache`.
- [ ] Create a FastAPI service that streams tokens (SSE) from a mock LLM.

## Resources
- Official docs: https://docs.python.org/3/
- Fluent Python (Luciano Ramalho)
- Real Python: https://realpython.com/
