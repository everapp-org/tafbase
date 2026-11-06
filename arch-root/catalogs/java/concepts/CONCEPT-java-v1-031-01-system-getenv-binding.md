---
id: CONCEPT-java-v1-031-01-system-getenv-binding
status: accepted
subproject: java
layer: L2-language
since: Java 11
standing: recommended
realizes: CONCEPT-prog-v1-010-01-external-environment-binding
---

# Environment Variable Binding via System.getenv

## Definition

Binding configuration from process environment variables via `System.getenv(String)` with explicit `Optional` mapping and sensible fallback defaults guarantees twelve-factor application compatibility and robust container startup.

```java
public record DatabaseConfig(String host, int port, String database) {
    public static DatabaseConfig fromEnvironment() {
        String host = Optional.ofNullable(System.getenv("DB_HOST"))
            .filter(s -> !s.isBlank())
            .orElse("localhost");

        int port = Optional.ofNullable(System.getenv("DB_PORT"))
            .filter(s -> !s.isBlank())
            .map(Integer::parseInt)
            .orElse(5432);

        String database = Optional.ofNullable(System.getenv("DB_NAME"))
            .filter(s -> !s.isBlank())
            .orElse("app_db");

        return new DatabaseConfig(host, port, database);
    }
}
```

## Why it exists

Hardcoding configuration in code or static property files inside deployment archives violates cloud-native twelve-factor principles. `System.getenv()` allows deployment manifests to inject configuration per environment. Combining `System.getenv` with `Optional.ofNullable` and `.filter(!String::isBlank)` prevents silent empty-string bugs, provides clear default fallbacks, and produces immutable configuration records without external framework overhead.
