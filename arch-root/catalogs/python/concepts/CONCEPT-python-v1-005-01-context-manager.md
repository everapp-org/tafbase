---
id: CONCEPT-python-v1-005-01-context-manager
status: accepted
subproject: python
layer: L2-language
since: Python 2.5
standing: recommended
realizes: CONCEPT-prog-v1-005-01-scoped-resource-cleanup
contrasts-with: CONCEPT-java-v1-012-01-try-with-resources-and-cleaner
---

# Python Context Manager

## Definition

A context manager in Python manages runtime resource lifecycles through the `with` statement protocol. An object implementing `__enter__()` and `__exit__()` (or defined as a generator decorated with `@contextlib.contextmanager`) guarantees that its cleanup logic executes deterministically upon exiting the `with` code block, regardless of whether the block finishes normally or terminates via an exception.

```python
from contextlib import contextmanager
from typing import Generator

@contextmanager
def temporary_transaction() -> Generator[str, None, None]:
    tx_id = "tx-12345"
    print(f"Beginning transaction {tx_id}")
    try:
        yield tx_id
    finally:
        print(f"Rolling back / releasing transaction {tx_id}")

with temporary_transaction() as tx:
    print(f"Executing work within {tx}")
    # Cleanup is guaranteed upon exiting the with block
```

## Why it exists

Prior to PEP 343 and the `with` statement, resource management required manual `try ... finally` blocks. Missing or misordered `finally` statements led to resource leaks, file descriptor starvation, and unclosed network handles. Furthermore, CPython's reference-counting garbage collector often masked these leaks during local tests, only for them to emerge under alternative runtimes (PyPy, Jython) or cyclic reference structures.

Context managers realize `CONCEPT-prog-v1-005-01-scoped-resource-cleanup`:
1. **Guaranteed release:** Encapsulates the `try/finally` pattern into reusable, composable constructs.
2. **Exception interception:** `__exit__` receives any unhandled exception and can inspect, log, or suppress it if designed to do so.
3. **Contrast with Java:** While Java's `try`-with-resources (`CONCEPT-java-v1-012-01-try-with-resources-and-cleaner`) requires types to implement `AutoCloseable`, Python's protocol allows both object methods (`__enter__`/`__exit__`) and generator-based yields via `@contextmanager`, providing flexible inline lifecycle management.
