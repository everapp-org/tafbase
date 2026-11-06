---
id: CONCEPT-java-v1-019-01-jspecify-and-nullaway
status: accepted
subproject: java
layer: L3-tooling
since: JSpecify 1.0.0
standing: recommended
realizes: CONCEPT-prog-v1-004-01-null-safe-optionality
contrasts-with: CONCEPT-python-v1-004-01-none-aware-typing, CONCEPT-ts-v1-004-01-strict-null-checks
---

# Compile-Time Null Safety with JSpecify and NullAway

## Definition

JSpecify (`org.jspecify.annotations`) standardizes nullability annotations (`@NullMarked`, `@Nullable`, `@NonNull`) across the Java ecosystem. When paired with compiler plugins such as Uber NullAway via Error Prone, it enforces compile-time null safety with zero runtime performance cost.

```java
package com.example.service;

import org.jspecify.annotations.NullMarked;
import org.jspecify.annotations.Nullable;

@NullMarked
public class UserService {

    public UserAccount getActiveUser(String id, @Nullable String fallbackGroup) {
        // Compile error under NullAway if id is passed as null,
        // or if fallbackGroup is dereferenced without a null check:
        int groupLen = fallbackGroup != null ? fallbackGroup.length() : 0;
        return new UserAccount(id, groupLen);
    }
}
```

## Why it exists

Java historically suffered from annotation fragmentation: `@Nullable` and `@NotNull` existed across multiple competing libraries, each with subtle semantic differences and uneven tooling support. JSpecify delivers a unified, cross-tool standard backed by major industry vendors. Tools like Uber NullAway analyze bytecode and abstract syntax trees during compilation, catching potential `NullPointerException` bugs before tests run while maintaining fast compilation speeds.
