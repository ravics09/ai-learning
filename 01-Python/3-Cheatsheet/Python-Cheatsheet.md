# Python for AI Engineering — Cheatsheet

> Dense, one-page quick reference. Skim before an interview or while coding.

---

## Data types & mutability

| Immutable | Mutable |
|---|---|
| `int, float, complex, bool` | `list` |
| `str, bytes` | `dict` |
| `tuple, frozenset` | `set` |
| `None` | most custom objects |

- `==` compares value; `is` compares identity (use `is` only for `None`).
- Immutable → hashable → usable as dict key / set member.

## Idioms

```python
# swap
a, b = b, a
# unpacking
first, *rest = [1, 2, 3, 4]           # first=1, rest=[2,3,4]
# ternary
x = a if cond else b
# walrus (assign + use)
while (line := f.readline()):
    ...
# enumerate / zip
for i, v in enumerate(seq): ...
for a, b in zip(xs, ys): ...
# dict merge (3.9+)
merged = d1 | d2
# f-strings
f"{value:.3f}"  f"{name=}"  f"{n:,}"
# comprehensions
[x*x for x in xs if x > 0]
{k: v for k, v in pairs}
(x for x in xs)                        # lazy generator
# default dict get
count = d.get(key, 0) + 1
```

## Collections & itertools

```python
from collections import defaultdict, Counter, deque, namedtuple
defaultdict(list)                      # auto-init missing keys
Counter(words).most_common(5)          # frequency counts
deque(maxlen=100)                       # O(1) append/pop both ends; ring buffer
from itertools import islice, chain, groupby, batched  # batched: 3.12+
list(batched(range(10), 3))            # [(0,1,2),(3,4,5),(6,7,8),(9,)]
```

## Functions

```python
def f(a, b=2, *args, key=None, **kwargs): ...
f(*list_args, **dict_kwargs)           # unpacking
lambda x: x + 1
from functools import lru_cache, cache, partial, reduce, wraps
@lru_cache(maxsize=1024)               # memoize (args must be hashable)
```

## Async (asyncio)

```python
import asyncio
async def main():
    async with asyncio.TaskGroup() as tg:      # structured concurrency (3.11+)
        tg.create_task(work())
    await asyncio.gather(a(), b())             # run concurrently
    async with asyncio.timeout(2):             # timeout a block (3.11+)
        await slow()
    await asyncio.to_thread(blocking_fn)       # offload blocking work
    sem = asyncio.Semaphore(10)                # cap concurrency
asyncio.run(main())
```

- Concurrency, **not** parallelism (one thread). Never block the loop
  (`time.sleep`, `requests`, heavy CPU loops) — offload with `to_thread`.

## Concurrency decision

| Bottleneck | Use |
|---|---|
| I/O, thousands | `asyncio` |
| I/O, few / blocking libs | `ThreadPoolExecutor` |
| CPU-bound pure Python | `ProcessPoolExecutor` |
| CPU-bound numeric | NumPy / native |

- **GIL**: one thread runs bytecode at a time. Free-threaded build (PEP 703/779):
  experimental in 3.13, officially supported-but-optional in 3.14 (ABI tag `t`).

## Typing

```python
x: int = 5
def f(a: list[float], b: int | None = None) -> dict[str, int]: ...
from typing import Optional, Callable, Any, TypeVar, Protocol, Literal
Handler = Callable[[str], str]
T = TypeVar("T")
# tools: mypy, pyright. Hints are NOT enforced at runtime (Pydantic/FastAPI do enforce).
```

## Pydantic v2 & dataclasses

```python
from pydantic import BaseModel, Field, field_validator
class Req(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    temperature: float = Field(0.7, ge=0, le=2)
req = Req.model_validate(json_data)    # validate untrusted input at the edge
req.model_dump()                        # -> dict

from dataclasses import dataclass, field
@dataclass(slots=True, frozen=True)     # fast, low-mem, hashable
class Cfg: name: str; stop: list[str] = field(default_factory=list)
```

## Generators / streaming

```python
def stream(path):
    with open(path) as f:
        for line in f:
            yield line.strip()          # O(1) memory over huge files
yield from sub_gen()                     # delegate
```

## Decorators / context managers

```python
import functools, time
def timed(fn):
    @functools.wraps(fn)
    def w(*a, **k):
        t = time.perf_counter()
        try: return fn(*a, **k)
        finally: print(time.perf_counter() - t)
    return w

from contextlib import contextmanager
@contextmanager
def res():
    x = acquire()
    try: yield x
    finally: release(x)
```

## Performance & profiling

| Tool | For |
|---|---|
| `time.perf_counter` | quick timing |
| `timeit` | micro-benchmarks |
| `cProfile` + snakeviz | function hotspots |
| `py-spy` | live/prod sampling |
| `line_profiler` | per-line |
| `tracemalloc` / `memray` | memory |

Ladder: **algorithm → vectorize → batch → cache → concurrency → native (Cython/numba/Rust)**.
Use `set`/`dict` for O(1) lookups. Profile first; optimize the top 20%.

## NumPy

```python
import numpy as np
a = np.arange(1e6)
a ** 2                                   # vectorized (runs in C)
X - X.mean(axis=0)                       # broadcasting
X @ q                                    # matmul / dot
np.linalg.norm(X, axis=1)               # row norms
# Broadcasting: align shapes from the right; dims equal or 1.
```

## Pandas vs Polars

```python
df.groupby("k")["v"].mean()             # vectorized; never iterrows on hot path
import polars as pl
pl.scan_parquet("f.parquet").filter(pl.col("x") > 0).group_by("k").agg(pl.len()).collect()
```

| | Pandas | Polars |
|---|---|---|
| Engine | Python/C, single-thread core | Rust, multi-threaded |
| Lazy opt | No | Yes (`scan_*`/`collect`) |
| Memory | Higher | Lower (Arrow) |

## Packaging (uv — 2025-2026 default)

```bash
uv init && uv add fastapi numpy pydantic
uv sync              # reproduce locked env
uv run pytest        # run in managed venv
# poetry: libraries; conda/mamba: native/CUDA deps; pip+venv: baseline
```

## Testing (pytest)

```python
@pytest.fixture
def client(): ...
@pytest.mark.parametrize("a,b", [(1,2),(3,4)])
def test_x(a, b): assert f(a) == pytest.approx(b)
with pytest.raises(ValueError): f(bad)
# pytest-asyncio for coroutines; monkeypatch/mock for external APIs
```

## FastAPI serving

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
@asynccontextmanager
async def lifespan(app):
    app.state.model = load_model()       # load ONCE at startup
    yield
app = FastAPI(lifespan=lifespan)
@app.post("/predict")
async def predict(req: Req):
    return await asyncio.to_thread(app.state.model.run, req.prompt)  # don't block loop
```

## Pitfalls (fast list)

- Mutable default arg `def f(x=[])` → shared state.
- Blocking the event loop; threads for CPU-bound work.
- `is` for value comparison; float `==` (use `math.isclose`).
- Late binding: `lambda i=i: i` to capture now.
- Model loaded per request; row loops over arrays/DataFrames.
- Bare `except:`; leaking handles (use `with`).

> Content synthesized from general domain knowledge and current (2025-2026) trends;
> rephrased for compliance with licensing restrictions.
