---
id: CONCEPT-prog-v1-008-01-immutable-collection-literal
status: accepted
subproject: prog
layer: L1-archetype
---

# Immutable Collection Literal

## Definition

An immutable collection literal provides concise, first-class syntax or canonical factory methods to construct collections (lists, sets, maps) whose size and element references cannot be modified after instantiation. Any operation that attempts to add, remove, or replace elements is rejected at compile time or raises an immediate unmodifiable collection error at runtime.

```
val allowedRoles = setOf("admin", "operator", "viewer")
val configMap = mapOf("timeout" -> 5000, "retries" -> 3)
// allowedRoles.add("guest") -> rejected / illegal operation
```

## Why it exists

Mutable collections passed across service boundaries encourage hidden coupling. One component can alter a list or dictionary while another component is iterating over it or caching its previous contents, resulting in concurrent modification exceptions, corrupted internal states, and hard-to-trace bugs.

Immutable collection literals eliminate defensive copying:
1. **Safe sharing:** Components can expose their internal collection state directly as unmodifiable views without cloning overhead.
2. **Memory efficiency:** Immutable collections can share structural nodes or compact their internal representations since dynamic resizing overhead is unnecessary.
3. **Deterministic behavior:** Cache invalidation and change-detection logic become trivial because collection identity and contents remain constant over time.
