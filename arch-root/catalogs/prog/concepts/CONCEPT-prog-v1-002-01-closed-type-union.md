---
id: CONCEPT-prog-v1-002-01-closed-type-union
status: accepted
subproject: prog
layer: L1-archetype
requires: CONCEPT-prog-v1-001-01-immutable-data-carrier
---

# Closed Type Union

## Definition

A closed type union (or algebraic sum type) defines a type whose valid instances belong to a finite, declared set of distinct variants. Unlike open class hierarchies where arbitrary subclasses can be introduced anywhere in a codebase, a closed type union establishes a sealed boundary that prohibits unauthorized extension.

```
union AsyncResult<T> =
    | Success(value: T)
    | Failure(error: ErrorCode, message: String)
    | Pending
```

## Why it exists

Open inheritance models make it impossible for a compiler or static analyzer to verify whether all possible cases of a domain model are handled. When domain states evolve, developers must rely on runtime fallback clauses or defensive default branches that mask unhandled states until runtime.

Closed type unions enforce domain boundaries at design time:
1. **Accurate domain modeling:** Real-world entities frequently exist in mutually exclusive states (such as payment statuses, command outcomes, or AST node kinds) where open subclassing is semantically invalid.
2. **Prerequisite for exhaustive branching:** By declaring the complete set of valid variants, the closed union provides compilers and linters with the information needed to verify exhaustiveness without default catch-all clauses.
3. **Type safety across boundaries:** Eliminates error-prone sentinel values (such as returning `null` or negative integers on failure) in favor of explicit, strongly typed variant payloads.
