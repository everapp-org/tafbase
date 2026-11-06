---
id: CONCEPT-java-v1-015-01-unnamed-variables-and-patterns
status: accepted
subproject: java
layer: L2-language
since: Java 22
standing: recommended
---

# Unnamed Variables and Patterns

## Definition

The underscore identifier `_` denotes unnamed variables and patterns in local variable declarations, catch blocks, lambda parameters, and pattern matching. It signifies that the value or component is intentionally ignored and cannot be referenced.

```java
// Unused exception in catch block
try {
    return Integer.parseInt(input);
} catch (NumberFormatException _) {
    return defaultValue;
}

// Unused lambda parameter
registry.forEach((_, handler) -> handler.warmUp());

// Unused record pattern components
if (obj instanceof Order(String id, _, double total, _)) {
    System.out.printf("Order %s: $%.2f%n", id, total);
}
```

## Why it exists

Developers previously had to invent dummy names (such as `ignored`, `unused`, `e1`) for variables required by grammar but unused by logic. This confused code reviewers, triggered compiler warnings (`unused variable`), and interfered with static analysis. Unnamed variables with `_` explicitly communicate intent to compilers, linters, and human readers, suppress unused-variable warnings, and allow multiple unnamed variables in the same scope without variable name collisions.
