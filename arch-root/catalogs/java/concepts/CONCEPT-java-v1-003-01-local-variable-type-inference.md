---
id: CONCEPT-java-v1-003-01-local-variable-type-inference
status: accepted
subproject: java
layer: L2-language
since: Java 10
standing: recommended
---

# Local Variable Type Inference

## Definition

Local variable type inference (`var`) allows the compiler to infer the static type of a local variable from its initializer expression. Static type safety is fully preserved; `var` is not dynamic typing or `Object`.

```java
var usersById = new HashMap<UUID, UserAccount>();
var client = HttpClient.newHttpClient();

try (var lines = Files.lines(Path.of("config.txt"))) {
    var activeConfigs = lines
        .filter(line -> !line.isBlank())
        .map(String::strip)
        .toList();
}
```

## Why it exists

Eliminates redundant type declarations where the type is already explicit on the right-hand side, reducing visual clutter and emphasizing meaningful variable names over ceremonial type signatures. It also captures non-denotable intersection types from lambdas and anonymous classes. Use `var` when variable names clearly convey intent and the inferred type is self-evident from the constructor call or immaterial to local logic. Avoid `var` when the initializer is ambiguous, with primitive numeric literals requiring specific precision, or when assigning to interface types where concrete type implementation details should not be leaked.
