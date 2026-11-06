---
id: CONCEPT-java-v1-004-01-sealed-classes
status: accepted
subproject: java
layer: L2-language
since: Java 17
standing: recommended
realizes: CONCEPT-prog-v1-002-01-closed-type-union
requires: CONCEPT-java-v1-002-01-records
contrasts-with: CONCEPT-python-v1-002-01-union-type, CONCEPT-ts-v1-002-01-discriminated-union
---

# Sealed Classes and Interfaces

## Definition

Sealed classes and interfaces restrict which other classes or interfaces may extend or implement them. The `permits` clause declares the exhaustive set of allowed direct subtypes, which must be declared in the same module or package. Subtypes must be declared `final`, `sealed`, or `non-sealed`.

```java
public sealed interface PaymentResult
    permits PaymentResult.Success, PaymentResult.Declined, PaymentResult.Error {

    record Success(String transactionId, long amountCents) implements PaymentResult {}
    record Declined(String reasonCode) implements PaymentResult {}
    record Error(String message, Throwable cause) implements PaymentResult {}
}
```

## Why it exists

Before sealed types, inheritance had only two extremes: completely open (`public class`) or completely closed (`final class` or private constructors). Domain modeling often requires algebraic sum types (closed type unions) where the set of variants is finite and well-known. Sealed hierarchies provide compiler-enforced exhaustiveness checks in `switch` expressions without requiring a defensive, unreachable `default` clause. If a new permitted subtype is added, the compiler flags every unhandled switch site across the codebase. Use sealed hierarchies combined with records to model domain events, commands, AST nodes, and workflow states.
