---
id: CONCEPT-js-v1-003-01-switch-with-default-throw
status: accepted
subproject: js
layer: L2-language
since: ES2015
standing: recommended
realizes: CONCEPT-prog-v1-003-01-exhaustive-branching
---

# Switch on Discriminant with Default Guard

## Definition

In JavaScript, exhaustive branching over tagged objects is implemented using a `switch` statement on the discriminant tag (`obj.kind`) where the `default` branch throws an explicit error (such as a `TypeError` or `RangeError`) containing the unrecognized tag value. This ensures that any unhandled variant causes an immediate runtime failure rather than silently proceeding with undefined values.

```js
export function formatResult(result) {
  switch (result.kind) {
    case 'success':
      return `Loaded: ${result.payload}`;
    case 'failure':
      return `Failed (${result.error}): ${result.message}`;
    case 'pending':
      return 'Loading in progress...';
    default:
      throw new TypeError(`Unhandled result kind: ${result?.kind}`);
  }
}
```

## Why it exists

JavaScript runtimes do not perform compile-time exhaustiveness checking. Without an explicit guard in the `default` branch, unhandled variants silently fall through, causing functions to return `undefined`. Downstream code will later fail with confusing `TypeError: Cannot read properties of undefined` errors far from the source.

Switch on discriminant with a throwing default realizes `CONCEPT-prog-v1-003-01-exhaustive-branching`:
1. **Fail-fast behavior:** Any new variant or malformed object is caught immediately at runtime with a clear, descriptive message.
2. **Defensive robustness:** Protects systems against desynchronized API contracts or missed branch cases during progressive migrations.
3. **TypeScript compatibility:** Prepares code for static exhaustiveness checking when migrating to TypeScript or using `@ts-check` JSDoc annotations.
