---
id: CONCEPT-playwright-v1-004-01-web-first-assertions
status: accepted
subproject: playwright
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-007-01-hard-vs-soft-assertions
contrasts-with: CONCEPT-selenium-v1-004-01-one-shot-dom-assertions
---

# Auto-Retrying Web-First Assertions

## Definition

Web-first assertions are asynchronous verification matchers designed specifically for the dynamic nature of web applications. Instead of checking DOM state once at an arbitrary instant, web-first assertions poll the targeted locator repeatedly until the expected condition is satisfied or a timeout is reached.

Standard web-first assertions include:
- `expect(locator).toBeVisible()`
- `expect(locator).toHaveText(expected)`
- `expect(locator).toBeEnabled()`
- `expect(locator).toHaveValue(value)`
- `expect(page).toHaveURL(urlOrRegex)`

```typescript
import { Page, expect } from '@playwright/test';

export async function verifyOrderProcessed(page: Page, expectedOrderNumber: string) {
  const confirmationBanner = page.getByRole('alert');
  const orderNumberDisplay = page.getByTestId('order-confirmation-id');

  // Retries continuously until the alert appears or timeout expires (e.g., 5000ms)
  await expect(confirmationBanner).toBeVisible();

  // Retries until client-side hydration or API response updates the text content
  await expect(orderNumberDisplay).toHaveText(expectedOrderNumber);
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-007-01-hard-vs-soft-assertions`. Web verification requires oracles that understand the eventual consistency of user interfaces. Assertions that evaluate too early produce false-negative test failures.

Contrasts with `CONCEPT-selenium-v1-004-01-one-shot-dom-assertions`. In Selenium frameworks, standard testing assertions (such as JUnit's `assertEquals` or TestNG's `assertTrue`) are one-shot synchronous checks. They extract a string or boolean from a `WebElement` at a single instant in time and immediately fail if the state has not settled. To make one-shot assertions reliable, test authors are forced to write verbose explicit wait loops prior to each assert statement. Playwright integrates retrying verification directly into the assertion syntax, drastically simplifying test structure.
