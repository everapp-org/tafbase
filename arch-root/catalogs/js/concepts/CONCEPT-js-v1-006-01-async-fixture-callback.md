---
id: CONCEPT-js-v1-006-01-async-fixture-callback
status: accepted
subproject: js
layer: L2-language
since: ES2017
standing: recommended
realizes: CONCEPT-prog-v1-006-01-scoped-test-fixture
---

# Async Fixture Callback Lifecycle

## Definition

The async fixture callback pattern (popularized by Playwright Test and modern test runners) manages fixture lifecycle through a higher-order function that receives an asynchronous callback (traditionally named `use`). The fixture performs setup, invokes `await use(resource)` to transfer control to the executing test, and subsequently executes teardown logic inside a `finally` block once the test completes.

```js
export async function withTempDirectory(callback) {
  const dir = await fs.promises.mkdtemp('/tmp/test-');
  try {
    await callback(dir);
  } finally {
    await fs.promises.rm(dir, { recursive: true, force: true });
  }
}

// In a test runner or custom suite:
await withTempDirectory(async (dir) => {
  await fs.promises.writeFile(`${dir}/spec.txt`, 'data');
  assert.ok(fs.existsSync(`${dir}/spec.txt`));
});
```

## Why it exists

Traditional JavaScript test frameworks (Mocha, Jasmine, early Jest) relied heavily on global mutable state shared between `beforeEach` and `afterEach` hooks (`let context; beforeEach(() => ...)`). When a test failed unexpectedly or an asynchronous timeout occurred, teardown hooks were frequently skipped, or failed while attempting to clean up partially initialized variables.

The async fixture callback realizes `CONCEPT-prog-v1-006-01-scoped-test-fixture`:
1. **Guaranteed teardown:** The `finally` block ensures that cleanup runs reliably even if the test assertion fails or an error is thrown inside `use()`.
2. **Local variable scope:** Test resources remain bound to local closure parameters rather than leaking into module or suite-level variables.
3. **Seamless async flow:** Eliminates race conditions by leveraging native `async/await` execution stacks.
