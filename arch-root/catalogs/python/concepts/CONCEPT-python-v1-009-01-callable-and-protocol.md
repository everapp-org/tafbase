---
id: CONCEPT-python-v1-009-01-callable-and-protocol
status: accepted
subproject: python
layer: L2-language
since: Python 3.8
standing: recommended
realizes: CONCEPT-prog-v1-009-01-higher-order-function
---

# Callable and Protocol Interfaces

## Definition

In Python, first-class functions and callables are statically typed using `collections.abc.Callable` and structural `typing.Protocol` interfaces. Functions can be passed as arguments, assigned to variables, returned from closures, or represented by objects implementing the `__call__` dunder method. `Protocol` enables structural subtyping (static duck typing), allowing higher-order functions to accept any callable or class matching a signature without explicit inheritance.

```python
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

def retry(attempts: int, operation: Callable[..., T]) -> T:
    last_err: Exception | None = None
    for _ in range(attempts):
        try:
            return operation()
        except Exception as e:
            last_err = e
    if last_err is not None:
        raise last_err
    raise RuntimeError("Unreachable")
```

## Why it exists

Historically, Python relied entirely on dynamic runtime duck typing, meaning type mismatches in function arguments or callbacks were only detected when an invalid call was executed at runtime. Additionally, implementing interfaces required formal ABC inheritance, which introduced unwanted coupling and metaclass conflicts.

`Callable` and `Protocol` realize `CONCEPT-prog-v1-009-01-higher-order-function`:
1. **Accurate signature verification:** Static type checkers verify argument and return types of callbacks and decorators without running code.
2. **Structural decoupling:** A callable or service object does not need to inherit from a shared base class; conforming to the protocol method signature is sufficient.
3. **First-class composability:** Enables decorators, middleware pipelines, and functional transformers with complete type safety.
