---
id: CONCEPT-js-v1-004-01-nullish-coalescing-and-optional-chaining
status: accepted
subproject: js
layer: L2-language
since: ES2020
standing: recommended
realizes: CONCEPT-prog-v1-004-01-null-safe-optionality
---

# Nullish Coalescing and Optional Chaining

## Definition

Introduced in ES2020, optional chaining (`?.`) and nullish coalescing (`??`) provide syntax for safely navigating and providing fallbacks for potentially absent values (`null` or `undefined`). Optional chaining short-circuits property access, method calls, or array indexing to `undefined` if the target is nullish. The nullish coalescing operator returns the right-hand operand only if the left-hand operand evaluates to `null` or `undefined` (unlike the logical OR operator `||` which coalesces all falsy values).

```js
export function resolvePort(config) {
  // config?.server?.port short-circuits to undefined if config or server is null/undefined
  // ?? 8080 assigns 8080 only if the resolved port is null or undefined (allowing port 0)
  return config?.server?.port ?? 8080;
}
```

## Why it exists

Before ES2020, inspecting deeply nested structures required repetitive guard expressions (`if (config && config.server && config.server.port)`) or utility libraries like Lodash `get`. Furthermore, relying on the logical OR operator `||` for defaults introduced bugs by unintentionally replacing valid falsy values (such as `0`, `""`, or `false`) with defaults.

These operators realize `CONCEPT-prog-v1-004-01-null-safe-optionality`:
1. **Falsy distinction:** Clearly differentiates intentional empty states (`0`, `""`, `false`) from uninitialized absence (`null`, `undefined`).
2. **Short-circuiting ergonomics:** Eliminates deeply nested ternary operators or verbose conditional checks.
3. **Safe function invocation:** Supports `callback?.(data)` to safely invoke optional hooks without manual `typeof callback === 'function'` checks.
