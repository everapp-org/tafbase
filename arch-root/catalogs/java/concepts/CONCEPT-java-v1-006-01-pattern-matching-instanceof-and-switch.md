---
id: CONCEPT-java-v1-006-01-pattern-matching-instanceof-and-switch
status: accepted
subproject: java
layer: L2-language
since: Java 21
standing: recommended
realizes: CONCEPT-prog-v1-003-01-exhaustive-branching
requires: CONCEPT-java-v1-004-01-sealed-classes, CONCEPT-java-v1-005-01-switch-expressions
---

# Pattern Matching for instanceof and switch

## Definition

Pattern matching extends `instanceof` and `switch` to test against types, bind scoped pattern variables, guard conditions with `when` clauses, and handle `null` explicitly without boilerplate type casting.

```java
public String formatValue(Object obj) {
    return switch (obj) {
        case null -> "null";
        case Integer i -> "int: " + i;
        case Long l -> "long: " + l;
        case String s when !s.isBlank() -> "non-empty string: " + s.trim();
        case String _ -> "blank string";
        default -> "unknown: " + obj.toString();
    };
}

public void handle(Object obj) {
    if (obj instanceof String s && s.length() > 5) {
        System.out.println("Long string: " + s.toUpperCase());
    }
}
```

## Why it exists

Legacy code forced repetitive ceremony: an `if (obj instanceof Target)` followed immediately by an explicit cast `Target t = (Target) obj;`. In multi-branch type dispatch, developers relied on chains of `if-else` or visitor patterns that obscured logic. Pattern matching binds strongly-typed variables safely, scopes them to the matching branch, supports boolean pattern refinement via `when`, and allows explicit `case null` instead of throwing unexpected `NullPointerException` before switch evaluation begins.
