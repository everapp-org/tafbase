---
id: CONCEPT-java-v1-005-01-switch-expressions
status: accepted
subproject: java
layer: L2-language
since: Java 14
standing: recommended
realizes: CONCEPT-prog-v1-003-01-exhaustive-branching
---

# Switch Expressions

## Definition

Switch expressions evaluate to a value and use arrow syntax (`case ->`) that prevents fall-through without requiring explicit `break` statements. In multi-statement branches, the `yield` statement produces the value. Switch expressions require exhaustiveness when used as expressions.

```java
DayType dayType = switch (day) {
    case MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY -> DayType.WEEKDAY;
    case SATURDAY, SUNDAY -> DayType.WEEKEND;
};

int score = switch (status) {
    case ACTIVE -> 100;
    case PENDING -> 50;
    case SUSPENDED -> {
        auditLogger.warn("Suspended account accessed: {}", accountId);
        yield 0;
    }
};
```

## Why it exists

Legacy switch statements were modeled on C: fall-through by default, error-prone `break` requirements, mutable accumulator variables declared outside the switch, and scoping leaking variables across cases. Switch expressions turn branching into pure, side-effect-free expressions, enforce exhaustiveness checking at compile time, eliminate accidental fall-through bugs, and allow declaring `final` variables directly initialized from switch branches.
