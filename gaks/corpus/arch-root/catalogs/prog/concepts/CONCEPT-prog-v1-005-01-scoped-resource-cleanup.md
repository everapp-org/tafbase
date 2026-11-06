---
id: CONCEPT-prog-v1-005-01-scoped-resource-cleanup
status: accepted
subproject: prog
layer: L1-archetype
---

# Scoped Deterministic Resource Cleanup

## Definition

Scoped deterministic resource cleanup binds the lifecycle of an external system handle (such as an open file descriptor, network socket, database transaction, or browser session) directly to the boundary of a lexical scope. When execution exits the scope—whether through normal completion, an early `return`, or an uncaught exception—the resource's registered disposal routine is guaranteed to execute immediately without relying on garbage collection.

```
scoped (val conn = DatabasePool.acquire()) {
    conn.execute("UPDATE accounts SET active = true")
} // conn.release() invoked deterministically upon leaving this block
```

## Why it exists

Garbage collectors manage memory allocations effectively, but they provide no timely guarantees for operating system handles, file locks, or network connections. Waiting for a finalizer or GC cycle to close a connection pool or socket leads to file descriptor exhaustion, deadlocks, and corrupted state under load.

Deterministic scope cleanup resolves resource contention:
1. **Guaranteed release under errors:** Exceptions thrown during intermediate operations cannot leak acquired resources.
2. **Predictable release timing:** Resources are freed the moment they are no longer needed, minimizing lock durations and memory footprints.
3. **Composability:** Scopes can be nested or chained, ensuring cleanup occurs in reverse order of acquisition.
