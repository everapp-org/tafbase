---
id: CONCEPT-java-v1-016-01-flexible-constructor-bodies
status: accepted
subproject: java
layer: L2-language
since: Java 25
standing: recommended
---

# Statements Before super() and Flexible Constructor Bodies

## Definition

Flexible constructor bodies allow statements to appear prior to an explicit constructor invocation (`super(...)` or `this(...)`). These statements execute in the pre-initialization context where instance state of the current class cannot yet be accessed.

```java
public class NormalizedSocketChannel extends SocketChannel {
    private final String sanitizedHost;

    public NormalizedSocketChannel(String host, int port) {
        if (host == null || host.isBlank()) {
            throw new IllegalArgumentException("Host cannot be blank");
        }
        if (port < 1 || port > 65535) {
            throw new IllegalArgumentException("Invalid port: " + port);
        }
        String normalized = host.trim().toLowerCase();
        super(normalized, port);
        this.sanitizedHost = normalized;
    }
}
```

## Why it exists

Java historically enforced the rule that `super(...)` or `this(...)` had to be the absolute first statement in any constructor body. This forced developers to contort validation and argument normalization into unreadable static helper methods or inline expressions (e.g. `super(validateAndNormalize(host), port)`). Flexible constructor bodies permit preparatory code, argument validation, and intermediate calculations before delegating to the superclass constructor, while maintaining safety by prohibiting reads or writes to instance fields before `super(...)` returns.
