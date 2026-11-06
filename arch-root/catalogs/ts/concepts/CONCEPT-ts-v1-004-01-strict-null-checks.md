---
id: CONCEPT-ts-v1-004-01-strict-null-checks
status: accepted
subproject: ts
layer: L2-language
since: TypeScript 2.0
standing: recommended
realizes: CONCEPT-prog-v1-004-01-null-safe-optionality
contrasts-with: CONCEPT-java-v1-019-01-jspecify-and-nullaway, CONCEPT-python-v1-004-01-none-aware-typing
---

# Strict Null Checks

## Definition

In TypeScript, enabling `"strictNullChecks": true` (or `"strict": true`) in `tsconfig.json` fundamentally alters the type system so that `null` and `undefined` are distinct types, not members of every domain type. A variable typed as `string` can never hold `null` or `undefined`. Optionality must be explicitly declared as a union (`string | null | undefined` or `string?`). Accessing properties on nullable types is prohibited until narrowed.

```ts
export function formatEmail(email: string | null | undefined): string {
  // return email.toLowerCase(); // Error: 'email' is possibly 'null' or 'undefined'.
  if (email == null) {
    return 'no-reply@example.com';
  }
  return email.toLowerCase(); // Type narrowed to string
}
```

## Why it exists

In unstrict TypeScript (and early versions), `null` and `undefined` were valid values for every type (`let s: string = null;` was permitted). This allowed runtime `TypeError: Cannot read properties of undefined` to bypass compiler checks, defeating a primary reason for using a static type system.

Strict null checks realize `CONCEPT-prog-v1-004-01-null-safe-optionality`:
1. **Absence is explicit:** Function signatures explicitly document whether parameters or return values can be omitted or empty.
2. **Flow-sensitive type guards:** The compiler tracks conditions like `if (val != null)` to narrow types within branch scopes automatically.
3. **Contrast with Java and Python:** Unlike Java which requires bytecode annotation processors (`CONCEPT-java-v1-019-01-jspecify-and-nullaway`), or Python which unifies absence under `None` (`CONCEPT-python-v1-004-01-none-aware-typing`), TypeScript distinguishes between unassigned values (`undefined`) and intentional blank values (`null`) within its type algebra.
