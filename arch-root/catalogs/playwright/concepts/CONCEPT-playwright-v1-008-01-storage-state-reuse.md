---
id: CONCEPT-playwright-v1-008-01-storage-state-reuse
status: accepted
subproject: playwright
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-004-01-session-and-context-isolation
---

# Authenticated Storage State Snapshot and Reuse

## Definition

Playwright's `storageState` mechanism serializes all authentication artifacts—including HTTP cookies, HTML5 local storage keys, and session storage entries—into a structured JSON file on disk.

Subsequent `BrowserContext` instances can be initialized with this pre-populated storage state, allowing tests to launch directly into an authenticated session without traversing the application's login UI or re-authenticating over the network.

```typescript
import { Browser, BrowserContext, Page, chromium } from 'playwright';

// Setup phase: Authenticate once and persist session state
export async function authenticateAndSaveState(browser: Browser, statePath: string) {
  const context: BrowserContext = await browser.newContext();
  const page: Page = await context.newPage();

  await page.goto('https://app.example.com/login');
  await page.getByLabel('Username').fill('admin');
  await page.getByLabel('Password').fill('secret');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/dashboard');

  // Dump cookies and localStorage to disk
  await context.storageState({ path: statePath });
  await context.close();
}

// Test phase: Initialize a clean context pre-loaded with authenticated state
export async function launchAuthenticatedSession(browser: Browser, statePath: string): Promise<Page> {
  const context = await browser.newContext({ storageState: statePath });
  const page = await context.newPage();
  await page.goto('https://app.example.com/dashboard');
  return page;
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-004-01-session-and-context-isolation`. Standard UI login workflows typically take 2 to 5 seconds per test to load forms, perform cryptographic key exchanges, set session tokens, and redirect. In a suite of hundreds of tests, repeating UI logins adds tens of minutes of execution time and introduces substantial flakiness risk.

By executing the authentication procedure once during setup (or creating the storage file directly via API), dozens of parallel test workers can instantiate isolated authenticated browser contexts instantly. Because each context receives a distinct clone of the storage state, tests remain completely isolated from one another while enjoying fast startup times.
