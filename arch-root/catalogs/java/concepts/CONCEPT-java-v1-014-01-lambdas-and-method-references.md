---
id: CONCEPT-java-v1-014-01-lambdas-and-method-references
status: accepted
subproject: java
layer: L2-language
since: Java 8
standing: recommended
realizes: CONCEPT-prog-v1-009-01-higher-order-function
---

# Lambdas, Method References, and Functional Interfaces

## Definition

Functional interfaces (`@FunctionalInterface`, containing a single abstract method) allow behavior to be passed as first-class citizens using lambda expressions (`(...) -> ...`) and method references (`Class::method` or `instance::method`).

```java
Function<String, Integer> parser = Integer::parseInt;
Predicate<String> isValid = s -> s != null && !s.isBlank();
Consumer<UserAccount> notifier = auditService::recordAccess;

List<Integer> parsedNumbers = rawStrings.stream()
    .filter(isValid)
    .map(parser)
    .sorted(Comparator.naturalOrder())
    .toList();
```

## Why it exists

Prior to Java 8, passing behavior required anonymous inner classes with heavy ceremony (e.g. `new Runnable() { public void run() { ... } }`), which allocated fresh heap objects on every evaluation, captured enclosing `this` references unintentionally, and cluttered control flow. Lambdas are compiled efficiently using `invokedynamic` (via `LambdaMetafactory`), deferring translation strategy to the JVM runtime and reusing call site handles without extraneous class loading. Method references provide clear, concise symbol references to existing methods.
