---
id: CONCEPT-python-v1-008-01-tuple-and-frozenset
status: accepted
subproject: python
layer: L2-language
since: Python 3.3
standing: recommended
realizes: CONCEPT-prog-v1-008-01-immutable-collection-literal
---

# Built-in Immutable Collections

## Definition

Python provides first-class unmodifiable collections through built-in types and standard library utilities: `tuple` for ordered sequences, `frozenset` for unique unordered elements, and `types.MappingProxyType` for creating read-only proxy views over dictionaries. Once constructed, instances cannot have elements added, removed, or reassigned.

```python
from types import MappingProxyType

COORDINATES: tuple[int, ...] = (10, 20, 30)
ALLOWED_ACTIONS: frozenset[str] = frozenset({"read", "write", "execute"})

_raw_config = {"env": "prod", "port": 8080}
APP_CONFIG: MappingProxyType[str, object] = MappingProxyType(_raw_config)
```

## Why it exists

In Python, passing mutable lists or dictionaries (`list`, `dict`, `set`) between functions frequently leads to unintended side effects when a downstream function mutates an argument in place. Module-level mutable variables (`ROUTES = []`) are also prone to race conditions and test pollution.

Immutable built-in collections realize `CONCEPT-prog-v1-008-01-immutable-collection-literal`:
1. **Hashable composites:** Tuples and frozensets are hashable (provided their contained elements are hashable), allowing them to serve as cache keys and dictionary indexes.
2. **Read-only encapsulation:** `MappingProxyType` allows internal state to be exposed to external callers without copying the underlying dictionary.
3. **Memory optimization:** CPython optimizes tuples and frozensets with fixed memory layouts and smaller memory footprints compared to dynamic lists and sets.
