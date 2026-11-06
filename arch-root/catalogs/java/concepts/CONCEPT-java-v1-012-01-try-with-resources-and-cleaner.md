---
id: CONCEPT-java-v1-012-01-try-with-resources-and-cleaner
status: accepted
subproject: java
layer: L2-language
since: Java 9
standing: recommended
realizes: CONCEPT-prog-v1-005-01-scoped-resource-cleanup
contrasts-with: CONCEPT-python-v1-005-01-context-manager, CONCEPT-ts-v1-005-01-using-disposable
---

# Deterministic try-with-resources, AutoCloseable, and Cleaner

## Definition

`try-with-resources` guarantees deterministic release of external resources managed by `AutoCloseable` types upon block exit, properly suppressing secondary exceptions. For low-level off-heap resources where explicit cleanup might be omitted, `java.lang.ref.Cleaner` provides a garbage-collection-triggered fallback without resurrection hazards.

```java
public void transferData(Path source, Path target) throws IOException {
    try (var in = Files.newInputStream(source);
         var out = Files.newOutputStream(target)) {
        in.transferTo(out);
    } // in and out closed deterministically in reverse acquisition order
}

public class NativeBufferHandle implements AutoCloseable {
    private static final Cleaner CLEANER = Cleaner.create();
    private final Cleaner.Cleanable cleanable;

    public NativeBufferHandle(long address) {
        this.cleanable = CLEANER.register(this, new Releaser(address));
    }

    @Override
    public void close() {
        cleanable.clean();
    }

    private static record Releaser(long address) implements Runnable {
        @Override
        public void run() {
            // Free off-heap buffer at address
        }
    }
}
```

## Why it exists

Replaces brittle `finally { if (res != null) res.close(); }` blocks where an exception thrown during `close()` would mask the primary exception that caused the block failure. `try-with-resources` suppresses secondary exceptions and attaches them via `Throwable.getSuppressed()`. Furthermore, it supersedes `Object.finalize()`, which was unpredictable, stalled GC sweeps, allowed object resurrection, and was deprecated for removal. Use `try-with-resources` for all deterministic scoping and `Cleaner` solely as a defensive safeguard for off-heap allocations.
