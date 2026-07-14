# Python for AI Engineering — Basic Interview Questions

> Foundational questions you should answer instantly and clearly. Even senior interviews
> often open here to check that your fundamentals are solid. Answers are in plain language
> with code and the "why".

## Quick Coverage Map

| # | Question | Theme |
|---|---|---|
| 1 | Mutable vs immutable types | Data model |
| 2 | `is` vs `==` | Identity vs value |
| 3 | `list` vs `tuple` | Collections |
| 4 | Shallow vs deep copy | Memory/copying |
| 5 | `*args` and `**kwargs` | Functions |
| 6 | List/dict/set comprehensions | Idioms |
| 7 | How generators save memory | Lazy eval |
| 8 | Decorators | Functions |
| 9 | `@staticmethod` vs `@classmethod` vs instance | OOP |
| 10 | Mutable default argument trap | Pitfalls |
| 11 | Exception handling / `finally` | Robustness |
| 12 | Virtual environments & packaging | Tooling |

---

### 1. What is the difference between mutable and immutable types?

**Answer.** Immutable objects can't change after creation (`int`, `float`, `str`, `bytes`,
`tuple`, `frozenset`); mutable ones can (`list`, `dict`, `set`, most custom objects).

Immutability makes objects **hashable** (usable as dict keys / set members) and safe to share
across threads or requests without locks. Mutating an "immutable" value actually creates a new
object:

```python
s = "hi"
print(id(s))
s += "!"          # new string object; the original was not modified
print(id(s))      # different id

x = (1, 2)        # tuple is immutable -> hashable
d = {x: "ok"}     # valid key
```

**Why it matters:** In AI services, sharing an immutable config across requests is safe;
sharing a mutable one invites subtle race-condition bugs.

---

### 2. What is the difference between `is` and `==`?

**Answer.** `==` compares **values** (calls `__eq__`); `is` compares **identity** (same object
in memory). Use `is` only for singletons like `None`.

```python
a = [1, 2, 3]
b = [1, 2, 3]
a == b      # True  (same contents)
a is b      # False (different objects)

x = None
x is None   # correct idiom
```

**Gotcha:** small integers (−5..256) and some short strings are cached/interned, so `is` may
*accidentally* return `True`. Never rely on that — always use `==` for value comparisons.

---

### 3. `list` vs `tuple` — when do you use each?

**Answer.** Both are ordered sequences. A **list** is mutable and used for homogeneous,
changing collections. A **tuple** is immutable, slightly lighter/faster, hashable, and signals
"fixed record."

```python
scores = [0.1, 0.5, 0.9]     # will grow/change -> list
point = (12.3, 45.6)         # fixed pair -> tuple, can be a dict key
```

**Why it matters:** returning a tuple communicates "don't mutate this," and tuples can key
caches (e.g., `lru_cache` arguments must be hashable).

---

### 4. Shallow copy vs deep copy?

**Answer.** A shallow copy duplicates the outer container but shares the inner objects; a deep
copy recursively clones everything.

```python
import copy
data = {"weights": [1, 2, 3]}
s = copy.copy(data)          # inner list is SHARED
d = copy.deepcopy(data)      # fully independent
s["weights"].append(4)       # also changes data["weights"]  -> [1,2,3,4]
d["weights"].append(9)       # data is untouched
```

**Why it matters:** accidentally sharing a mutable buffer (feature vector, config) between
requests causes bugs that only appear under concurrency.

---

### 5. What are `*args` and `**kwargs`?

**Answer.** `*args` collects extra **positional** arguments into a tuple; `**kwargs` collects
extra **keyword** arguments into a dict. They let functions accept variable arguments and
forward them.

```python
def log_call(fn, *args, **kwargs):
    print(f"calling {fn.__name__} with {args} {kwargs}")
    return fn(*args, **kwargs)      # unpacking forwards them along

def embed(text, model="small"): ...
log_call(embed, "hello", model="large")
```

**Why it matters:** decorators and wrappers (timing, retries, auth) rely on `*args/**kwargs`
to wrap any function transparently.

---

### 6. Explain comprehensions.

**Answer.** Comprehensions build collections concisely and are usually faster than equivalent
`for`-loops because the work happens in optimized C.

```python
squares = [x*x for x in range(10)]                 # list
even = {x for x in range(10) if x % 2 == 0}        # set
lookup = {w: i for i, w in enumerate(vocab)}       # dict
lazy = (x*x for x in range(10))                    # generator (lazy, memory-light)
```

**Why it matters:** the dict comprehension above builds a token→id vocabulary — a daily task
in NLP pipelines. Prefer a **generator expression** when you only iterate once over big data.

---

### 7. How do generators save memory? Give a streaming example.

**Answer.** A generator (`yield`) produces values **one at a time on demand** instead of
building the whole list in memory. It holds only the current item, so it can process data far
larger than RAM.

```python
def stream_lines(path):
    with open(path) as f:
        for line in f:
            yield line.strip()      # one line in memory at a time

total_chars = sum(len(line) for line in stream_lines("50GB.log"))
```

**Why it matters:** streaming training data, embeddings, or LLM tokens to a client all rely on
lazy generation. A list of 50 GB would crash; a generator sips memory.

---

### 8. What is a decorator?

**Answer.** A decorator is a function that takes a function and returns a wrapped version,
adding behavior (logging, timing, caching, auth) without editing the original.

```python
import functools, time
def timed(fn):
    @functools.wraps(fn)                 # keep name/docstring
    def wrapper(*args, **kwargs):
        t = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            print(f"{fn.__name__}: {time.perf_counter()-t:.3f}s")
    return wrapper

@timed
def infer(x): ...
```

**Why it matters:** FastAPI routes (`@app.post`), caching (`@lru_cache`), and retry logic are
all decorators. Always use `functools.wraps` so introspection/docs still work.

---

### 9. `@staticmethod` vs `@classmethod` vs instance method?

**Answer.**
- **Instance method** (`self`) — operates on an instance's data.
- **Classmethod** (`cls`) — operates on the class; common for **alternative constructors**.
- **Staticmethod** — a plain function grouped under the class; no `self`/`cls`.

```python
class Model:
    def __init__(self, name): self.name = name
    def predict(self, x): ...                     # instance
    @classmethod
    def from_config(cls, cfg):                    # alt constructor
        return cls(cfg["name"])
    @staticmethod
    def normalize(v):                             # utility
        return v / sum(v)
```

**Why it matters:** `from_config`/`from_pretrained`-style factory methods are ubiquitous in ML
libraries and are classmethods.

---

### 10. What is the mutable default argument trap?

**Answer.** A default argument is evaluated **once**, at function-definition time. A mutable
default (like `[]`) is then shared across all calls.

```python
def add(x, bucket=[]):    # BUG: same list every call
    bucket.append(x); return bucket
add(1)   # [1]
add(2)   # [1, 2]  <- shared!

def add(x, bucket=None):  # FIX
    if bucket is None:
        bucket = []
    bucket.append(x); return bucket
```

**Why it matters:** this is one of the most common Python bugs and a favorite interview
"gotcha." Recognizing it signals real fluency.

---

### 11. How do you handle exceptions well? What does `finally` do?

**Answer.** Catch **specific** exceptions, keep `try` blocks small, and use `finally` (or a
context manager) for cleanup that must always run.

```python
try:
    resp = call_model(prompt)
except TimeoutError:
    resp = fallback()                 # handle a known failure
except ValueError as e:
    log.warning("bad input: %s", e); raise
finally:
    release_resources()              # always runs, even on exception
```

Avoid bare `except:` (it swallows `KeyboardInterrupt`/`SystemExit` and hides bugs).
**Why it matters:** production AI services must degrade gracefully when a model API times out
or returns garbage.

---

### 12. What is a virtual environment and how do you manage dependencies?

**Answer.** A virtual environment isolates a project's packages so versions don't collide
across projects. You pin dependencies in a lockfile for reproducibility.

```bash
# Classic
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Modern (2025-2026): uv is fast (Rust) and manages venvs + Python versions
uv init && uv add fastapi numpy pydantic
uv sync        # reproduce the exact locked environment
```

**Why it matters:** "works on my machine" bugs come from unpinned deps. In 2025-2026 many
teams default to **uv** for speed in CI/CD and Docker builds; **poetry** remains popular for
libraries; **conda** shines when you need native/CUDA deps.

---

## Further Reading

- Python tutorial (official): https://docs.python.org/3/tutorial/
- Real Python — generators: https://realpython.com/introduction-to-python-generators/
- Real Python — decorators: https://realpython.com/primer-on-python-decorators/
- uv docs: https://docs.astral.sh/uv/
- Fluent Python, 2nd ed. (Luciano Ramalho)

> Content synthesized from general domain knowledge and current (2025-2026) interview trends;
> rephrased for compliance with licensing restrictions.
