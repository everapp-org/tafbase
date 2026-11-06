---
id: CONCEPT-js-v1-002-01-tagged-object-discriminant
status: accepted
subproject: js
layer: L2-language
since: ES2015
standing: recommended
realizes: CONCEPT-prog-v1-002-01-closed-type-union
---

# Tagged Object Discriminant

## Definition

A tagged object discriminant is a JavaScript design pattern for modeling closed union variants. Each variant object includes a dedicated, constant property (conventionally named `kind`, `type`, or `status`) with a unique string literal value. Factory functions ensure each instance receives its correct tag alongside variant-specific payload fields.

```js
export function createSuccess(payload) {
  return Object.freeze({ kind: 'success', payload });
}

export function createFailure(error, message) {
  return Object.freeze({ kind: 'failure', error, message });
}

export function createPending() {
  return Object.freeze({ kind: 'pending' });
}
```

## Why it exists

In dynamically typed JavaScript, functions often return ambiguous results (such as `false`, `null`, or an error object) to indicate failure. Inspecting return values via `typeof`, checking for the existence of arbitrary keys (`if (res.error)`), or using `instanceof` across different execution realms (like iframes or worker threads) is notoriously brittle and error-prone.

The tagged discriminant realizes `CONCEPT-prog-v1-002-01-closed-type-union` in JavaScript:
1. **Explicit variant distinction:** Inspecting `obj.kind` provides unambiguous, uniform routing without checking for arbitrary properties.
2. **Realm-independent:** Unlike `instanceof`, string tag comparison works reliably across VM contexts, web workers, and serialization boundaries (JSON).
3. **Foundation for exhaustiveness:** Acts as the primary discriminant key for `switch` dispatch statements and TypeScript discriminated unions.
