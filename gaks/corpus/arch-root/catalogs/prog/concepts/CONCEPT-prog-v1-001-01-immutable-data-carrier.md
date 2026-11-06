---
id: CONCEPT-prog-v1-001-01-immutable-data-carrier
status: accepted
subproject: prog
layer: L1-archetype
---

# Immutable Data Carrier

## Definition

An immutable data carrier is a transparent, shallowly unmodifiable value aggregate whose identity is entirely determined by its constituent components. Once constructed, its member fields cannot be reassigned. Instances provide structural equality (`equals` and `hashCode` derived directly from component values) and canonical component extraction (destructuring or accessor functions).

```
carrier GeoPoint(latitude: Float64, longitude: Float64)

val origin = GeoPoint(0.0, 0.0)
val copy = GeoPoint(0.0, 0.0)
assert origin == copy
```

## Why it exists

Traditional object-oriented classes conflate data representation with encapsulated mutating behavior. When mutable data structures are shared across boundaries (threads, asynchronous tasks, or distinct subsystems), unintended mutations cause aliasing bugs, race conditions, and defensive copying overhead.

The immutable data carrier archetype solves this by decoupling pure data transmission from behavioral state machines:
1. **Thread safety:** Being immutable, instances can be freely shared across concurrent execution contexts without synchronization locks.
2. **Predictable equality:** Value-based semantics allow carriers to safely serve as hash map keys or set members.
3. **Intent clarity:** Eliminates boilerplate setters, ensures constructor invariants cannot be bypassed post-construction, and forms the fundamental leaf node for algebraic data types.
