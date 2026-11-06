---
id: CONCEPT-ts-v1-006-01-typed-test-fixture-extension
status: accepted
subproject: ts
layer: L2-language
since: TypeScript 4.5
standing: recommended
realizes: CONCEPT-prog-v1-006-01-scoped-test-fixture
---

# Typed Test Fixture Extension

## Definition

In TypeScript test runners (such as `@playwright/test` and Vitest), test fixtures are strongly typed and extended using `test.extend<MyFixtures>()`. Each fixture definition provides setup and teardown by destructuring dependencies, performing setup actions, awaiting `use(fixtureValue)`, and executing teardown logic. The runner automatically infers fixture types and validates dependency graphs at compile time.

```ts
// Playwright Test / Modern TS fixture extension
export interface TestContext {
  tempDir: string;
}

// Extends base test runner with strongly typed fixtures:
// export const test = baseTest.extend<TestContext>({
//   tempDir: async ({}, use) => {
//     const dir = await fs.promises.mkdtemp('/tmp/ts-');
//     await use(dir);
//     await fs.promises.rm(dir, { recursive: true, force: true });
//   },
// });
```

```ts
export type FixtureFunction<T> = (use: (value: T) => Promise<void>) => Promise<void>;

export async function withIsolatedContext<T>(resource: T, runTest: (ctx: T) => Promise<void>): Promise<void> {
  console.log("Setting up typed test fixture");
  try {
    await runTest(resource);
  } finally {
    console.log("Tearing down typed test fixture");
  }
}
```

## Why it exists

In JavaScript test frameworks, passing mock objects or test state through `this` context or global hooks lacks type safety. Developers frequently misspell fixture property names or access uninitialized fixtures without the compiler catching the defect.

Typed fixture extension realizes `CONCEPT-prog-v1-006-01-scoped-test-fixture`:
1. **Compile-time auto-completion:** Tests declare fixtures as destructured arguments, and TypeScript validates that every requested fixture exists and matches its expected type.
2. **Deterministic execution graph:** The runner resolves dependencies between fixtures automatically, setting up and tearing down resources in the correct dependency order.
3. **Strict test isolation:** Eliminates mutable test suite instances by injecting pristine, typed fixture instances into each test.
