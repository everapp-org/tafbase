---
id: CONCEPT-ts-v1-009-01-generic-function-signature
status: accepted
subproject: ts
layer: L2-language
since: TypeScript 1.6
standing: recommended
realizes: CONCEPT-prog-v1-009-01-higher-order-function
---

# Generic Function Signatures and Type Predicates

## Definition

In TypeScript, first-class callables and higher-order functions are typed using generic function signatures (`<T, R>(item: T) => R`) and user-defined type predicates (`x is SubType`). Generic signatures preserve input and output type relationships across functional transformations, while type predicate signatures allow higher-order filtering functions to narrow collection element types statically.

```ts
export function isNonNullable<T>(value: T): value is NonNullable<T> {
  return value !== null && value !== undefined;
}

export function compactList<T>(items: readonly (T | null | undefined)[]): T[] {
  // Array.filter with type predicate narrows result type from (T | null | undefined)[] to T[]
  return items.filter(isNonNullable);
}

export function memoize<Args extends readonly unknown[], Result>(
  fn: (...args: Args) => Result
): (...args: Args) => Result {
  const cache = new Map<string, Result>();
  return (...args: Args): Result => {
    const key = JSON.stringify(args);
    if (!cache.has(key)) {
      cache.set(key, fn(...args));
    }
    return cache.get(key)!;
  };
}
```

## Why it exists

Without generic signatures, higher-order functions must resort to `any` or loose base types, erasing specific argument and return types. Furthermore, standard filtering operations like removing `null` values from a list (`list.filter(x => x !== null)`) previously retained the nullable type, requiring unsafe casts (`as string[]`).

Generic signatures and type predicates realize `CONCEPT-prog-v1-009-01-higher-order-function`:
1. **Type propagation:** The precise return type of a passed function flows seamlessly into the return type of the enclosing higher-order wrapper.
2. **Static filtering narrowing:** Type predicates (`x is T`) instruct the compiler that returning `true` guarantees the refined type for subsequent operations.
3. **Flexible composition:** Enables utility decorators, retry handlers, and memoization helpers without losing original parameter typings.
