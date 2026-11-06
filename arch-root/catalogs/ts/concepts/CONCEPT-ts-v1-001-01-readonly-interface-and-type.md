---
id: CONCEPT-ts-v1-001-01-readonly-interface-and-type
status: accepted
subproject: ts
layer: L2-language
since: TypeScript 3.4
standing: recommended
realizes: CONCEPT-prog-v1-001-01-immutable-data-carrier
contrasts-with: CONCEPT-java-v1-002-01-records, CONCEPT-python-v1-001-01-frozen-dataclass
---

# Readonly Interface and Const Assertion Carrier

## Definition

In TypeScript, immutable data carriers are declared using the `readonly` property modifier, the `Readonly<T>` utility type, and `as const` type assertions (introduced in TypeScript 3.4). Marked properties cannot be reassigned after initialization. When applied to object literals, `as const` recursively marks all properties as `readonly` and narrows primitive types to literal types.

```ts
export interface UserProfile {
  readonly id: string;
  readonly email: string;
  readonly loginCount: number;
}

export function createOrigin() {
  return { x: 0, y: 0 } as const; // Type: { readonly x: 0; readonly y: 0 }
}

const user: UserProfile = { id: "u-101", email: "dev@example.com", loginCount: 3 };
// user.loginCount = 4; // Compile error: Cannot assign to 'loginCount' because it is a read-only property.
```

## Why it exists

In JavaScript and unannotated TypeScript, object properties are mutable by default. Mutating object instances across asynchronous tasks or function pipelines introduces race conditions and aliasing bugs that are difficult to locate.

Readonly interfaces and `as const` realize `CONCEPT-prog-v1-001-01-immutable-data-carrier`:
1. **Compile-time enforcement with zero runtime cost:** Immutability is verified statically by the TypeScript compiler; no runtime wrapper code or performance overhead is emitted into the JavaScript output.
2. **Deep const assertions:** Appending `as const` automatically applies deep readonly constraints and preserves exact literal types without declaring explicit types for every nested field.
3. **Contrast with Java and Python:** Unlike Java records (`CONCEPT-java-v1-002-01-records`) which enforce final fields in JVM bytecode, or Python frozen dataclasses (`CONCEPT-python-v1-001-01-frozen-dataclass`) which raise `FrozenInstanceError` at runtime, TypeScript's readonly checks are erased at compile time, providing compile-time type safety while emitting lightweight JavaScript objects.
