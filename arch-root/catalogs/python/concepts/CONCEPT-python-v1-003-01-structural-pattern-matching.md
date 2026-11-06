---
id: CONCEPT-python-v1-003-01-structural-pattern-matching
status: accepted
subproject: python
layer: L2-language
since: Python 3.10
standing: recommended
realizes: CONCEPT-prog-v1-003-01-exhaustive-branching
requires: CONCEPT-python-v1-002-01-union-type
---

# Structural Pattern Matching

## Definition

Structural pattern matching in Python (introduced in PEP 634 / Python 3.10) provides `match` and `case` statements capable of inspecting the shape, type, and contents of objects. When combined with typing utilities like `typing.assert_never`, static type checkers (`mypy`, `pyright`) verify that all possible variants of a union type are covered, achieving compile-time exhaustiveness guarantees in Python.

```python
from typing import assert_never

def handle_result(res: CommandResult) -> str:
    match res:
        case Success(payload=text):
            return f"Processed: {text}"
        case Failure(error_code=code, message=msg):
            return f"Failed ({code}): {msg}"
        case _ as unreachable:
            assert_never(unreachable)
```

## Why it exists

Before Python 3.10, multi-way branch logic relied on chained `if isinstance(x, A): ... elif isinstance(x, B): ... else: ...` ladders. This approach lacked structural extraction and had no mechanism to verify whether all cases were handled. Adding a new variant to a data model would often pass silently into a default branch or fall through to `None`.

Structural pattern matching realizes `CONCEPT-prog-v1-003-01-exhaustive-branching`:
1. **Simultaneous check and extraction:** A single `case Success(payload=text)` statement asserts the instance type and binds its internal fields into local variables.
2. **Static exhaustiveness via `assert_never`:** If a developer adds a third variant to `CommandResult` without adding a corresponding `case`, static type checkers flag the `assert_never` call as a type error because the unreachable branch received an unhandled variant.
3. **Guard clauses:** Allows fine-grained pattern guards (`case Point(x=x, y=y) if x == y:`) without messy nested conditionals.
