---
id: CONCEPT-java-v1-030-01-double-brace-initialization-antipattern
status: accepted
subproject: java
layer: L3-idiom
since: Java 9
standing: discouraged
contrasts-with: CONCEPT-java-v1-011-01-immutable-collection-factories
---

# Double-Brace Initialization Anti-Pattern

## Definition

Double-brace initialization (`new HashMap<String, String>() {{ put("k", "v"); }}`) creates an anonymous inner subclass with an instance initializer block. It is a dangerous anti-pattern that must be avoided in favor of modern unmodifiable factory methods.

```java
// ANTI-PATTERN: DO NOT USE
Map<String, String> badMap = new HashMap<>() {{
    put("env", "production");
    put("tier", "frontend");
}};

// MODERN IDIOMATIC REPLACEMENT:
Map<String, String> goodMap = Map.of(
    "env", "production",
    "tier", "frontend"
);
```

## Why it exists

Prior to modern unmodifiable collection factories like `Map.of()` and `List.of()`, developers used double-brace initialization as a pseudo-literal syntax. However, each double-brace expression creates a new `.class` file on disk, retains a hidden reference to the enclosing `this` instance (preventing garbage collection of the outer object and causing severe memory leaks), breaks `equals()` contract comparisons against normal collection instances, and causes serialization issues. It is completely obsolete and strongly discouraged.
