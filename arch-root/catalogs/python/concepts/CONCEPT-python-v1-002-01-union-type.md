---
id: CONCEPT-python-v1-002-01-union-type
status: accepted
subproject: python
layer: L2-language
since: Python 3.10
standing: recommended
realizes: CONCEPT-prog-v1-002-01-closed-type-union
contrasts-with: CONCEPT-java-v1-004-01-sealed-classes, CONCEPT-ts-v1-002-01-discriminated-union
---

# Python Type Union

## Definition

In Python 3.10+, union types are expressed natively using the pipe operator (`X | Y`, PEP 604) in place of `typing.Union[X, Y]`. A type union indicates that a variable or return value can hold an instance of any of the specified member types. When combined with type aliases and distinct class variants, it forms Python's idiomatic realization of a closed type union.

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Success:
    payload: str

@dataclass(frozen=True, slots=True)
class Failure:
    error_code: int
    message: str

type CommandResult = Success | Failure
```

## Why it exists

Before PEP 604, writing union types required importing `typing.Union` and wrapping types in verbose subscript notation, hindering adoption of type annotations across Python codebases. Additionally, runtime introspection of unions was awkward and incompatible with `isinstance` checks.

The native `X | Y` syntax realizes `CONCEPT-prog-v1-002-01-closed-type-union` in Python:
1. **Readable algebraic composition:** Defining sum types is lightweight and requires no external metaclass or base library.
2. **Runtime `isinstance` support:** `isinstance(val, int | str)` is valid at runtime in Python 3.10+, aligning static type syntax with runtime validation.
3. **Contrast with Java and TypeScript:** Java sealed classes (`CONCEPT-java-v1-004-01-sealed-classes`) enforce a nominal closed hierarchy through inheritance permits. TypeScript discriminated unions (`CONCEPT-ts-v1-002-01-discriminated-union`) use structural discriminant fields. Python's union types can operate either nominally across separate dataclass types or structurally via pattern matching.
