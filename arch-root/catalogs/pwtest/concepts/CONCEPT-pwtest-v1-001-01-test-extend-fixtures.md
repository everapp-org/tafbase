---
id: CONCEPT-pwtest-v1-001-01-test-extend-fixtures
status: accepted
subproject: pwtest
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-prog-v1-006-01-scoped-test-fixture, CONCEPT-qa-v1-004-01-session-and-context-isolation
contrasts-with: CONCEPT-junit-v1-001-01-per-method-test-instance-lifecycle, CONCEPT-pytest-v1-001-01-dependency-injected-fixtures
---

# Typed Fixtures via test.extend

## Definition

Playwright Test Runner (`@playwright/test`) structures test environments through typed, composable fixtures defined via `test.extend<T>()`. Fixtures can be scoped per test (default) or per worker process (`scope: 'worker'`).

A fixture function receives its prerequisite fixtures, performs asynchronous setup, hands control to the test via `await use(fixtureValue)`, and executes cleanup logic once the test (and any dependent fixtures) finishes.

Because fixtures are typed via TypeScript interfaces, test functions receive autocomplete, type-checking, and automatic parameter destructuring.

```typescript
import { test as base, Page } from '@playwright/test';

// Define custom fixture types
type CustomFixtures = {
  authenticatedPage: Page;
  userRole: string;
};

// Extend base test runner with custom scoped fixtures
export const test = base.extend<CustomFixtures>({
  userRole: ['editor', { option: true }],

  authenticatedPage: async ({ page, userRole }, use) => {
    // 1. Setup: Perform login or session seeding
    await page.goto('https://app.example.com/login');
    await page.getByLabel('Role').fill(userRole);
    await page.getByRole('button', { name: 'Sign In' }).click();

    // 2. Yield fixture to the test body
    await use(page);

    // 3. Teardown: Clean up remote session or log out
    await page.evaluate(() => window.localStorage.clear());
  },
});

// Test consumes typed fixture via argument destructuring
test('edits article as editor', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('https://app.example.com/articles/new');
  await authenticatedPage.getByLabel('Title').fill('Automated Test Article');
});
```

## Why it exists

Realizes `CONCEPT-prog-v1-006-01-scoped-test-fixture` and `CONCEPT-qa-v1-004-01-session-and-context-isolation`. Traditional before/after test hooks encourage sharing mutable variables across hook methods, leading to order dependencies and brittle setup flows.

Contrasts with `CONCEPT-junit-v1-001-01-per-method-test-instance-lifecycle` and `CONCEPT-pytest-v1-001-01-dependency-injected-fixtures`. JUnit uses class inheritance and `@BeforeEach` methods that mutate class instance fields. While pytest popularized dependency-injected fixtures in Python, it relies on runtime dynamic keyword argument resolution. Playwright Test brings fixture dependency injection to TypeScript with complete static type safety, worker-level caching, and explicit async lifecycle boundaries.
