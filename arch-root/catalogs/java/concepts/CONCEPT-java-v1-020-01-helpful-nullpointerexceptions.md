---
id: CONCEPT-java-v1-020-01-helpful-nullpointerexceptions
status: accepted
subproject: java
layer: L2-language
since: Java 14
standing: recommended
---

# Helpful NullPointerException Diagnostics

## Definition

Helpful `NullPointerException` diagnostics enable the JVM to analyze bytecode at the point of a `NullPointerException` and describe exactly which variable, method invocation, or array indexing evaluated to `null`.

```java
// In a chained expression:
user.getAddress().getCity().toLowerCase();

// If getAddress() returned null, the JVM exception message displays:
// Cannot invoke "Address.getCity()" because the return value of
// "User.getAddress()" is null
```

## Why it exists

Historically, a `NullPointerException` on a line with chained calls (e.g. `a.b().c().d()`) or multiple array indexing operations only reported the line number. Developers were forced to inspect bytecode or split single expressions into multiple lines with temporary variables to identify the null dereference. Helpful NPE diagnostics pinpoint the precise expression that yielded null, dramatically speeding up root-cause analysis in production logs without bytecode instrumentation or performance overhead. Enabled by default since Java 15.
