---
id: CONCEPT-playwright-v1-001-01-browser-context-page-hierarchy
status: accepted
subproject: playwright
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-004-01-session-and-context-isolation
contrasts-with: CONCEPT-selenium-v1-001-01-webdriver-session-lifecycle
---

# Browser, BrowserContext, and Page Isolation Hierarchy

## Definition

Playwright structures browser automation into a three-tier execution hierarchy: `Browser` -> `BrowserContext` -> `Page`:

- **Browser**: A single OS-level browser process (Chromium, Firefox, or WebKit) launched once by the test runner. Starting a browser process carries significant CPU and memory overhead.
- **BrowserContext**: An isolated incognito-equivalent session inside a running browser instance. Each context maintains completely isolated cookies, local storage, indexedDB, session cache, and HTTP credentials. Creating a context takes negligible time (typically under 20 milliseconds).
- **Page**: A single browser tab or window within a `BrowserContext`. Multiple pages within the same context share session storage and cookies, modeling multi-tab user journeys.

```typescript
import { chromium, Browser, BrowserContext, Page } from 'playwright';

// 1. Launch a single heavyweight browser process
const browser: Browser = await chromium.launch();

// 2. Spawn two completely isolated sessions with distinct storage
const adminContext: BrowserContext = await browser.newContext();
const userContext: BrowserContext = await browser.newContext();

// 3. Open pages in each context without session leakage
const adminPage: Page = await adminContext.newPage();
await adminPage.goto('https://app.example.com/admin');

const userPage: Page = await userContext.newPage();
await userPage.goto('https://app.example.com/dashboard');

// 4. Teardown contexts independently in milliseconds
await adminContext.close();
await userContext.close();
await browser.close();
```

## Why it exists

Realizes `CONCEPT-qa-v1-004-01-session-and-context-isolation`. In automated end-to-end testing, tests must execute with zero state leakage while maximizing execution throughput.

Contrasts with `CONCEPT-selenium-v1-001-01-webdriver-session-lifecycle`. In traditional WebDriver architectures, isolating tests requires launching an entirely new browser process per test (`new ChromeDriver()`), incurring seconds of process spin-up latency, or attempting manual state purges (`driver.manage().deleteAllCookies()`) which fail to clear indexedDB, local storage, or worker caches reliably. Playwright's hierarchy allows test runners to keep a warm browser process pool running while provisioning fresh, fully sandboxed contexts per test in single-digit milliseconds.
