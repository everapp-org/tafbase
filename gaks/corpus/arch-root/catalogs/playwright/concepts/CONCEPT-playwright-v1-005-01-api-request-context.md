---
id: CONCEPT-playwright-v1-005-01-api-request-context
status: accepted
subproject: playwright
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-006-01-api-fixture-seeding
contrasts-with: CONCEPT-selenium-v1-005-01-external-http-seeding
---

# API Request Context for State Seeding

## Definition

Playwright provides `APIRequestContext` for executing out-of-band HTTP requests directly from the test runner. It allows tests to seed test fixtures, authenticate users, reset server state, or query backend databases via REST or GraphQL APIs prior to or during browser-driven UI steps.

An `APIRequestContext` can either exist independently (`playwright.request.newContext()`) or inherit cookie and authentication headers directly from a `BrowserContext` via `context.request`.

```typescript
import { test, expect } from '@playwright/test';

test('creates and edits resource via seeded state', async ({ request, page }) => {
  // 1. Seed backend entity out-of-band via fast HTTP POST
  const response = await request.post('https://api.example.com/items', {
    data: { name: 'Seed Product', price: 99.00 },
    headers: { 'Authorization': 'Bearer test-token' }
  });
  expect(response.ok()).toBeTruthy();
  const item = await response.json();

  // 2. Open browser UI directly to the seeded entity page
  await page.goto(`https://app.example.com/items/${item.id}`);
  await expect(page.getByRole('heading', { name: 'Seed Product' })).toBeVisible();
});
```

## Why it exists

Realizes `CONCEPT-qa-v1-006-01-api-fixture-seeding`. Navigating multi-step web forms solely through the browser UI to set up test prerequisites is slow and prone to cascading flakiness. Fast, reliable end-to-end tests seed preconditions out-of-band over HTTP and drive only the specific feature under test through the graphical user interface.

Contrasts with `CONCEPT-selenium-v1-005-01-external-http-seeding`. In Selenium setups, executing API requests requires pulling in an external third-party HTTP client (such as Apache HttpClient, OkHttp, or python-requests). Synchronizing authentication session cookies between the external HTTP client and the Selenium `WebDriver` instance requires tedious manual cookie extraction and `driver.manage().addCookie(...)` calls. Playwright's `APIRequestContext` is unified with the browser engine and handles session and network primitives natively.
