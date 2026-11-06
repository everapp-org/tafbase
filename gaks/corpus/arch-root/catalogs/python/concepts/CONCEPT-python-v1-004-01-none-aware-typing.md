---
id: CONCEPT-python-v1-004-01-none-aware-typing
status: accepted
subproject: python
layer: L2-language
since: Python 3.10
standing: recommended
realizes: CONCEPT-prog-v1-004-01-null-safe-optionality
contrasts-with: CONCEPT-java-v1-019-01-jspecify-and-nullaway, CONCEPT-ts-v1-004-01-strict-null-checks
---

# None-Aware Strict Typing

## Definition

None-aware strict typing in Python uses the union syntax `T | None` (replacing `typing.Optional[T]`) under strict static analysis configurations (`mypy --strict` or `pyright`). Under strict checking, any type `T` is non-nullable by default. Attempting to access an attribute or invoke a method on a variable typed as `T | None` without first checking for `None` (via `if x is not None:`) triggers a static type analysis error.

```python
def format_greeting(user_name: str | None) -> str:
    # return user_name.strip()  # Rejected: Item "None" of "str | None" has no attribute "strip"
    if user_name is None:
        return "Hello, Guest!"
    return f"Hello, {user_name.strip()}!"
```

## Why it exists

`AttributeError: 'NoneType' object has no attribute '...'` is the Python runtime equivalent of the Java `NullPointerException`. Because Python is dynamically typed, passing `None` into functions expecting an active object often fails many stack frames away from the original invocation, complicating debugging and root-cause analysis.

None-aware typing realizes `CONCEPT-prog-v1-004-01-null-safe-optionality`:
1. **Explicit API contracts:** Functions explicitly signal whether `None` is acceptable as an input or possible as a return value.
2. **Static verification without runtime penalty:** Type checkers narrow the union within `if x is not None:` blocks (flow-sensitive typing) with zero runtime performance cost.
3. **Contrast with Java and TypeScript:** Java requires external checker plugins like NullAway with JSpecify annotations (`CONCEPT-java-v1-019-01-jspecify-and-nullaway`). TypeScript uses `strictNullChecks` (`CONCEPT-ts-v1-004-01-strict-null-checks`) separating `null` and `undefined`. Python unifies absent values under the singleton `None`.
