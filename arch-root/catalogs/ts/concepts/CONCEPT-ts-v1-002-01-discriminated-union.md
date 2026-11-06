---
id: CONCEPT-ts-v1-002-01-discriminated-union
status: accepted
subproject: ts
layer: L2-language
since: TypeScript 2.0
standing: recommended
realizes: CONCEPT-prog-v1-002-01-closed-type-union
contrasts-with: CONCEPT-java-v1-004-01-sealed-classes, CONCEPT-python-v1-002-01-union-type
---

# Discriminated Union Type

## Definition

A discriminated union (or tagged union) in TypeScript is a union type where each member type shares a common singleton discriminant property (such as `kind: 'circle'` or `type: 'success'`). When code checks the value of this discriminant property via `if` or `switch`, TypeScript automatically narrows the union to the specific variant type, granting access to variant-specific fields without casting.

```ts
export interface SuccessResult {
  readonly kind: 'success';
  readonly data: string;
}

export interface FailureResult {
  readonly kind: 'failure';
  readonly errorCode: number;
  readonly message: string;
}

export type AsyncResult = SuccessResult | FailureResult;
```

## Why it exists

Modeling mutually exclusive domain states with optional fields on a single interface (`{ isSuccess?: boolean; data?: string; error?: string }`) results in invalid intermediate states (such as an object containing both `data` and `error`, or neither). It also forces developers to perform unsafe non-null assertions (`result.data!`).

Discriminated unions realize `CONCEPT-prog-v1-002-01-closed-type-union`:
1. **Impossible states made unrepresentable:** Each variant contains only the fields valid for that state, preventing malformed combinations.
2. **Automatic type narrowing:** Checking `result.kind === 'success'` narrows `result` to `SuccessResult`, making `result.data` immediately accessible.
3. **Contrast with Java and Python:** Java sealed classes (`CONCEPT-java-v1-004-01-sealed-classes`) use nominal class inheritance permits, while Python (`CONCEPT-python-v1-002-01-union-type`) uses nominal union types or structural match patterns. TypeScript's discriminated unions operate entirely structurally based on literal field values.
