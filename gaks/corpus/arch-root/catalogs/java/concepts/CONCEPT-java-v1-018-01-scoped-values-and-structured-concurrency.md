---
id: CONCEPT-java-v1-018-01-scoped-values-and-structured-concurrency
status: accepted
subproject: java
layer: L2-language
since: Java 25
standing: preview
realizes: CONCEPT-prog-v1-007-01-parallel-fan-out
requires: CONCEPT-java-v1-009-01-virtual-threads
---

# Scoped Values and Structured Concurrency

## Definition

Scoped values (`ScopedValue<T>`) provide safe, immutable, bounded data sharing across threads and child tasks without `ThreadLocal` overhead. Structured concurrency (`StructuredTaskScope`) treats split concurrent subtasks as a single unit of work, guaranteeing that all forks complete or cancel before the enclosing scope closes.

```java
public final static ScopedValue<SecurityContext> CURRENT_USER = ScopedValue.newInstance();

public OrderResponse handleOrder(OrderRequest request) throws Exception {
    return ScopedValue.where(CURRENT_USER, request.securityContext()).call(() -> {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            StructuredTaskScope.Subtask<Inventory> inv = scope.fork(() -> checkInventory(request));
            StructuredTaskScope.Subtask<Pricing> price = scope.fork(() -> calculatePrice(request));

            scope.join();           // join forks
            scope.throwIfFailed();  // propagate error if any task failed

            return new OrderResponse(inv.get(), price.get());
        }
    });
}
```

## Why it exists

`ThreadLocal` has severe flaws: it is unbounded in lifetime (causing memory leaks in thread pools), mutable from any call site, and incurs costly memory duplication when inherited across thousands of virtual threads. `ScopedValue` is strictly bounded by a lexical execution scope and is immutable. Unstructured concurrency (`CompletableFuture`, unmanaged threads) leads to thread leaks, orphaned tasks continuing after caller cancellation, and fragmented diagnostics. `StructuredTaskScope` ensures that when a subtask fails or times out, sibling subtasks are automatically canceled, restoring clean hierarchical task lifetimes.
