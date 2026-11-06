---
id: CONCEPT-python-v1-001-01-frozen-dataclass
status: accepted
subproject: python
layer: L2-language
since: Python 3.10
standing: recommended
realizes: CONCEPT-prog-v1-001-01-immutable-data-carrier
contrasts-with: CONCEPT-java-v1-002-01-records, CONCEPT-ts-v1-001-01-readonly-interface-and-type
---

# Frozen Dataclass

## Definition

A frozen dataclass in Python is an immutable data carrier declared using the `@dataclass(frozen=True, slots=True)` decorator. It automatically generates `__init__`, `__repr__`, `__eq__`, and `__hash__` methods while preventing field reassignment at runtime by intercepting `__setattr__`. Combining `frozen=True` with `slots=True` eliminates the per-instance `__dict__`, reducing memory footprint and preventing dynamic attribute injection.

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Coordinate:
    x: float
    y: float

origin = Coordinate(0.0, 0.0)
assert origin == Coordinate(0.0, 0.0)
assert hash(origin) == hash(Coordinate(0.0, 0.0))
```

## Why it exists

Prior to dataclasses, Python developers relied on plain classes (requiring manual `__init__`, `__repr__`, and `__eq__` implementations), `namedtuple` (which lacks type hinting integration and suffers from unexpected tuple index slicing semantics), or third-party libraries like `attrs`. Standard mutable classes easily cause bugs when instances are inadvertently modified after being stored in shared caches or passed between worker threads.

`@dataclass(frozen=True, slots=True)` realizes `CONCEPT-prog-v1-001-01-immutable-data-carrier` for Python:
1. **Hashability and immutability:** Providing a deterministic `__hash__` allows frozen dataclasses to be safely used as dictionary keys and set elements.
2. **Memory efficiency:** The addition of `slots=True` in Python 3.10 makes instances lightweight and comparable in memory performance to C structs.
3. **Contrast with Java and TypeScript:** Unlike Java records (`CONCEPT-java-v1-002-01-records`), immutability is enforced at the Python bytecode/runtime level rather than JVM final field semantics; and unlike TypeScript readonly interfaces (`CONCEPT-ts-v1-001-01-readonly-interface-and-type`), frozen dataclasses enforce protection at runtime as well as static type checks.
