---
id: CONCEPT-java-v1-002-01-records
status: accepted
subproject: java
layer: L2-language
since: Java 16
standing: recommended
realizes: CONCEPT-prog-v1-001-01-immutable-data-carrier
contrasts-with: CONCEPT-python-v1-001-01-frozen-dataclass, CONCEPT-ts-v1-001-01-readonly-interface-and-type
---

# Java Records

## Definition

Records are transparent, shallowly immutable carrier classes for nominal data tuples. Declaring a record automatically produces a `final` class with `final` fields, a canonical constructor, accessors matching component names, `equals()`, `hashCode()`, and `toString()`. Records support compact constructors for validation and normalization without field assignment boilerplate.

```java
public record UserAccount(String id, String email, int score) {
    public UserAccount {
        Objects.requireNonNull(id, "id must not be null");
        Objects.requireNonNull(email, "email must not be null");
        if (score < 0) {
            throw new IllegalArgumentException("score cannot be negative: " + score);
        }
        email = email.trim().toLowerCase();
    }

    public boolean isTopTier() {
        return score >= 1000;
    }
}
```

## Why it exists

Replaces verbose JavaBean and POJO ceremony (private fields, getters, `equals()`, `hashCode()`, `toString()`) and external annotation processors like Lombok `@Value` for data carriers. Unlike traditional classes, the compiler enforces semantic transparency: the state vector is the header. The compact constructor executes prior to instance initialization without re-assigning `this.field = field`. Use records for DTOs, domain value objects, map keys, and intermediate pipeline carriers. Avoid records when mutable identity, entity tracking, or class inheritance is required, as records cannot extend other classes.
