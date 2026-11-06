---
id: CONCEPT-java-v1-027-01-selective-lombok-with-modern-java
status: accepted
subproject: java
layer: L3-tooling
since: Lombok 1.18.48
standing: situational
requires: CONCEPT-java-v1-002-01-records
---

# Selective Lombok Usage in Modern Java

## Definition

In modern Java, Project Lombok should be used selectively. Annotations like `@Data`, `@Value`, and `@Getter` are superseded by native records. Lombok remains situational for specific features like `@Builder(toBuilder = true)` on records and logger injection (`@Slf4j`).

```java
import lombok.Builder;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class OrderService {

    @Builder(toBuilder = true)
    public record OrderConfig(
        String endpoint,
        int timeoutMillis,
        int maxRetries,
        boolean debugMode
    ) {}

    public void run() {
        var config = OrderConfig.builder()
            .endpoint("https://api.gateway.internal")
            .timeoutMillis(5000)
            .maxRetries(3)
            .debugMode(false)
            .build();

        log.info("Initialized order config: {}", config);
    }
}
```

## Why it exists

Lombok was created when Java was verbose and lacked modern syntactic sugar. However, heavy Lombok usage relies on private compiler internal APIs, causing fragility during major JDK upgrades. With Java records, text blocks, and pattern matching natively supported, the necessity for `@Data` and `@Value` has vanished. Restricting Lombok to `@Builder` on records and `@Slf4j` preserves convenience while minimizing compiler coupling and IDE annotation processing conflicts.
