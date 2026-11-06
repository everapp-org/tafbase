---
id: CONCEPT-prog-v1-003-01-exhaustive-branching
status: accepted
subproject: prog
layer: L1-archetype
requires: CONCEPT-prog-v1-002-01-closed-type-union
---

# Exhaustive Pattern Branching

## Definition

Exhaustive pattern branching is a language or static-analysis mechanism that verifies whether a conditional dispatch covers every variant of a closed type union. If any variant is omitted, the compiler or checker rejects the program before execution. Catch-all `default` branches are intentionally avoided or restricted so that future additions to the union trigger immediate compile-time errors.

```
function renderStatus(result: AsyncResult<Data>): String {
    return match (result) {
        Success(data)  => "Loaded: " + data.summary(),
        Failure(err, m) => "Failed with " + err + ": " + m,
        Pending        => "Loading..."
    }
}
```

## Why it exists

In traditional dispatch mechanisms (like cascading `if/else` ladders or switches with arbitrary `default` clauses), adding a new variant to a domain model silently falls into the default handler. This causes subtle defects to escape into production environments when new features are partially implemented.

Exhaustive pattern branching turns domain evolution into a compiler-assisted refactoring workflow:
1. **Refactoring safety:** Adding a new variant to a closed union flags every unhandled call site across the codebase as a compile failure.
2. **Defensive elimination:** Eliminates runtime `throw new IllegalStateException("Unexpected type")` guards in business logic.
3. **Data extraction synergy:** Works together with destructuring patterns to unpack payload fields directly into typed lexical variables within the branch scope.
