---
id: CONCEPT-java-v1-011-01-immutable-collection-factories
status: accepted
subproject: java
layer: L2-language
since: Java 16
standing: recommended
realizes: CONCEPT-prog-v1-008-01-immutable-collection-literal
---

# Unmodifiable Collection Factories

## Definition

Static factory methods on `List`, `Set`, and `Map` (`List.of(...)`, `Set.of(...)`, `Map.of(...)`, `Map.ofEntries(...)`) and `Stream.toList()` produce unmodifiable, compact, null-hostile collection instances.

```java
List<String> roles = List.of("ADMIN", "OPERATOR", "AUDITOR");
Set<Integer> allowedCodes = Set.of(200, 201, 204);
Map<String, String> headers = Map.of(
    "Accept", "application/json",
    "Content-Type", "application/json"
);

List<String> upper = roles.stream()
    .map(String::toLowerCase)
    .toList(); // returns unmodifiable list
```

## Why it exists

Replaces verbose patterns like `Collections.unmodifiableList(new ArrayList<>(Arrays.asList(...)))` or hazardous patterns like double-brace initialization. Collections produced by `.of()` methods are memory-optimized (storing elements in internal fields rather than array-wrapped nodes for small sizes), reject `null` elements immediately at construction, randomize set and map iteration order to prevent code from depending on unspecified ordering, and throw `UnsupportedOperationException` on any mutation attempt.
