---
id: CONCEPT-ts-v1-003-01-exhaustive-switch-never
status: accepted
subproject: ts
layer: L2-language
since: TypeScript 2.0
standing: recommended
realizes: CONCEPT-prog-v1-003-01-exhaustive-branching
requires: CONCEPT-ts-v1-002-01-discriminated-union
---

# Exhaustive Switch Narrowing with Never Check

## Definition

In TypeScript, exhaustive branching over a discriminated union is statically enforced using the bottom type `never`. Inside the `default` branch of a `switch` statement, assigning the discriminant variable to a type annotated as `never` (or passing it to a helper function `function assertNever(x: never): never`) forces the TypeScript compiler to confirm that all variants were handled in earlier cases. If an unhandled variant reaches `default`, TypeScript emits a compile error.

```ts
export function assertNever(x: never): never {
  throw new Error(`Unexpected object: ${JSON.stringify(x)}`);
}

export function handleResult(res: AsyncResult): string {
  switch (res.kind) {
    case 'success':
      return `Loaded: ${res.data}`;
    case 'failure':
      return `Failed (${res.errorCode}): ${res.message}`;
    default:
      return assertNever(res); // Compiler error if any variant of AsyncResult is omitted above
  }
}
```

## Why it exists

Without the `never` check, omitting a case in a `switch` statement causes TypeScript to fall through silently to `default`, often resulting in returning `undefined`. When new variants are added to a discriminated union, developers would have to manually find every switch statement across the codebase without compiler guidance.

The `never` exhaustiveness check realizes `CONCEPT-prog-v1-003-01-exhaustive-branching`:
1. **Refactoring safety:** Adding a new variant (e.g. `PendingResult`) to `AsyncResult` immediately causes compile errors in all functions that do not handle `PendingResult`.
2. **Elimination of dead code:** If all cases are handled, the variable in `default` has type `never`, proving dead code elimination mathematically.
3. **Dual compile-time and runtime protection:** Statically caught by TypeScript during build, and throws an informative runtime error if non-typechecked JavaScript passes an invalid object.
