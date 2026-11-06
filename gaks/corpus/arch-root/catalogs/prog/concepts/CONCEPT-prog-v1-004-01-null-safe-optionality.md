---
id: CONCEPT-prog-v1-004-01-null-safe-optionality
status: accepted
subproject: prog
layer: L1-archetype
---

# Null-Safe Optionality

## Definition

Null-safe optionality is a type system discipline where references are non-nullable by default. The possibility of absence must be explicitly expressed in the type declaration (such as `T | Null` or `Optional<T>`). Dereferencing an optional value without checking for existence or using null-safe traversal (such as optional chaining and nullish coalescing) is treated as a static error.

```
function getHostPort(config: ServerConfig?): Int {
    val port = config?.network?.port ?? 8080
    return port
}
```

## Why it exists

Unchecked null references represent one of the most prolific causes of production outages. When any reference can invisibly be `null`, every layer of code either performs redundant defensive checks or risks unexpected null pointer dereferences deep within execution stacks.

Null-safe optionality brings structural predictability to absent data:
1. **Explicit API contracts:** Callers immediately recognize whether an operation can legitimately yield nothing, without relying on ambiguous docstrings.
2. **Elimination of defensive boilerplate:** Because non-optional references are guaranteed present by construction, intermediate domain services do not need repetitive validation checks.
3. **Safe composition:** Safe navigation operators (`?.`) and fallback coalescing (`??`) allow concise traversal of nested optional data without deep conditional nesting.
