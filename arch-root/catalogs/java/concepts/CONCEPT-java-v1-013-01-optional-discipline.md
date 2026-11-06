---
id: CONCEPT-java-v1-013-01-optional-discipline
status: accepted
subproject: java
layer: L3-idiom
since: Java 11
standing: recommended
realizes: CONCEPT-prog-v1-004-01-null-safe-optionality
---

# Optional Return Discipline

## Definition

`Optional<T>` is a value-based container explicitly designed to represent the absence of a return value in public API methods. Idiomatic usage relies on functional transformations (`map`, `flatMap`, `filter`, `or`) and terminal extractors (`orElseThrow`, `orElseGet`), never bare `.get()` calls.

```java
public Optional<UserAccount> findById(UUID id) {
    return Optional.ofNullable(storage.get(id));
}

// Idiomatic call site:
String email = findById(userId)
    .filter(UserAccount::isActive)
    .map(UserAccount::email)
    .orElseThrow(() -> new NoSuchElementException("User not found: " + userId));
```

## Why it exists

Returning `null` leaves absence undeclared in method signatures, forcing callers to guess whether a check is required and inevitably leading to `NullPointerException`. `Optional` forces the caller to confront potential absence at compile time. However, misusing `Optional` causes performance and design regressions: `Optional` must never be used as a field type (it is not `Serializable` and adds object wrapper overhead), method parameter (forces callers to wrap arguments in `Optional.of()`), or inside collection elements.
