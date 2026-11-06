---
id: CONCEPT-playwright-v1-010-01-clock-and-deterministic-time
status: accepted
subproject: playwright
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-009-01-deterministic-replay-and-flakiness
---

# Deterministic Browser Clock Control

## Definition

Playwright's `Clock` API enables complete programmatic control over time inside the browser page. By virtualizing the browser's internal timer subsystem, tests can manipulate `Date.now()`, `setTimeout`, `setInterval`, `requestAnimationFrame`, and `performance.now()` deterministically.

Key operations include:
- `page.clock.install({ time: new Date(...) })`: Initializes mock clock mode with an optional fixed timestamp.
- `page.clock.fastForward(millis)`: Advances time instantaneously, firing all registered timer callbacks in chronological order without real-world waiting.
- `page.clock.pauseAt(date)`: Freezes execution time at an exact date or moment.
- `page.clock.resume()`: Resumes standard wall-clock progression.

```typescript
import { Page, expect } from '@playwright/test';

export async function testDebouncedSearch(page: Page) {
  // Install deterministic clock before navigating
  await page.clock.install();

  await page.goto('https://app.example.com/search');
  const searchInput = page.getByRole('searchbox', { name: 'Search' });
  await searchInput.fill('playwright');

  // Input uses a 500ms debounce; verify no network query dispatched yet
  await expect(page.getByTestId('search-spinner')).not.toBeVisible();

  // Instantly fast-forward 600ms without sleeping or wall-clock delay
  await page.clock.fastForward(600);

  // Debounced callback has fired instantaneously
  await expect(page.getByTestId('search-results')).toBeVisible();
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-009-01-deterministic-replay-and-flakiness`. Real-world time is one of the most persistent sources of flakiness and performance degradation in test suites. Verifying time-dependent behaviors—such as input debouncing, countdown timers, session timeouts, toast auto-dismissal, or polling intervals—traditionally required sleep delays (`Thread.sleep`, `setTimeout`).

Sleeping inflates suite runtime and still causes race conditions under varying CI system load. Deterministic clock control eliminates sleep calls, enabling instantaneous validation of complex temporal flows while guaranteeing byte-for-byte reproducibility across runs.
