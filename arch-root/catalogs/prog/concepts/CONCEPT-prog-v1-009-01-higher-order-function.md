---
id: CONCEPT-prog-v1-009-01-higher-order-function
status: accepted
subproject: prog
layer: L1-archetype
---

# First-Class Callable and Higher-Order Function

## Definition

A first-class callable is a function or lambda expression that is treated as a regular value: it possesses a distinct type signature, can be bound to identifiers, stored in data structures, passed as parameters into other routines, and returned from function invocations. A function that accepts or returns one or more callables is termed a higher-order function.

```
function retry<T>(attempts: Int, action: () -> T): T {
    var lastError: Error? = null
    for (i in 1..attempts) {
        try { return action() }
        catch (e: Error) { lastError = e }
    }
    throw lastError!
}
```

## Why it exists

Without first-class callables, parameterizing algorithms requires heavyweight design patterns (such as the Strategy, Command, or Template Method patterns) requiring dedicated classes and verbose boilerplate for simple behavioral tweaks.

Higher-order functions enable expressive and reusable abstractions:
1. **Separation of policy and mechanism:** Control structures (iteration, retry loops, authentication wrappers, transaction demarcations) can be written once and parameterized with arbitrary behavior.
2. **Concise data transformation:** Enables declarative processing pipelines (`map`, `filter`, `fold`) over streams and collections.
3. **Lexical closure capture:** Callables capture their enclosing environment variables cleanly without needing manual field-binding boilerplate.
