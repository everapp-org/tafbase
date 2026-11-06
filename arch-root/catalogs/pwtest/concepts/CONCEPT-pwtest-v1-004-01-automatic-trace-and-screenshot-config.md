---
id: CONCEPT-pwtest-v1-004-01-automatic-trace-and-screenshot-config
status: accepted
subproject: pwtest
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts
---

# Automatic Trace and Artifact Configuration

## Definition

Playwright Test Runner (`@playwright/test`) provides declarative configuration in `playwright.config.ts` for automated diagnostic artifact collection upon failure:
- `trace: 'retain-on-failure'`: In-memory recording of complete execution traces (DOM snapshots, network waterfall, console logs) that are persisted to disk only when a test fails. On passing tests, trace buffers are discarded, incurring zero disk I/O overhead.
- `screenshot: 'only-on-failure'`: Automatically captures a full-page or viewport screenshot at the instant an assertion fails or an unexpected exception occurs.
- `video: 'retain-on-failure'`: Records screen video in the background and saves the video file only for failed runs.

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  outputDir: 'test-results', // Destination for failure artifacts
  use: {
    baseURL: 'https://app.example.com',
    // Zero-overhead passing tests, rich diagnostics on failure
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
```

## Why it exists

Realizes `CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts`. Collecting screenshots, full execution traces, and video recordings for every passing test wastes gigabytes of CI artifact storage and degrades test execution speeds due to continuous file compression and disk writes.

Declarative conditional capture (`retain-on-failure`) solves the trade-off between execution speed and diagnostic depth. Passing tests complete with minimal overhead, while failed tests automatically emit full-fidelity trace packages directly into CI reports without requiring any manual `try/catch` or screenshot code in test files.
