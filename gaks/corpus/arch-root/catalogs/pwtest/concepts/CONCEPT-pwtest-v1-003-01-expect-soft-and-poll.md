---
id: CONCEPT-pwtest-v1-003-01-expect-soft-and-poll
status: accepted
subproject: pwtest
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-007-01-hard-vs-soft-assertions
contrasts-with: CONCEPT-junit-v1-003-01-assertall-grouped-assertions
---

# Soft and Polling Assertions

## Definition

Playwright Test Runner provides advanced assertion primitives that extend beyond standard terminating assertions:
- **`expect.soft(locator).<matcher>()`**: Soft assertions evaluate conditions without immediately throwing an error or aborting test execution. If a soft assertion fails, the runner records the failure details and continues running the remaining test steps. At the completion of the test, any accumulated soft failures are reported together.
- **`expect.poll(asyncFn, options).<matcher>()`**: Polling assertions repeatedly invoke an asynchronous callback function until the returned value satisfies the target matcher or a timeout expires.

```typescript
import { test, expect } from '@playwright/test';

test('validates full user card without aborting on first mismatch', async ({ page }) => {
  await page.goto('https://app.example.com/users/42');

  const name = page.getByTestId('user-name');
  const role = page.getByTestId('user-role');
  const email = page.getByTestId('user-email');

  // Soft assertions: All checks run even if name or role fails
  await expect.soft(name).toHaveText('Jordan Lee');
  await expect.soft(role).toHaveText('Admin');
  await expect.soft(email).toHaveText('jordan@example.com');

  // Polling assertion: Polls an asynchronous backend API until status becomes 'ready'
  await expect.poll(async () => {
    const res = await page.request.get('https://api.example.com/sync-status');
    const data = await res.json();
    return data.status;
  }, { intervals: [500, 1000], timeout: 10_000 }).toBe('ready');
});
```

## Why it exists

Realizes `CONCEPT-qa-v1-007-01-hard-vs-soft-assertions`. Complex UI screens display multiple interrelated pieces of data (e.g. dashboards, summaries, or reports). Using standard hard assertions aborts the test on the first mismatch, hiding information about whether the remaining 10 fields on the screen are valid or broken.

Contrasts with `CONCEPT-junit-v1-003-01-assertall-grouped-assertions`. In JUnit Jupiter, soft assertions are constrained within a localized closure block (`Assertions.assertAll(...)`). In Playwright Test, `expect.soft()` can be interleaved linearly anywhere within natural test workflows, allowing tests to navigate across pages and perform multi-step interactions while accumulating validation findings throughout the entire scenario.
