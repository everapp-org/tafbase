---
id: CONCEPT-playwright-v1-006-01-trace-viewer-and-artifacts
status: accepted
subproject: playwright
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts
contrasts-with: CONCEPT-selenium-v1-006-01-takes-screenshot-and-logs
---

# Trace Viewer and Execution Artifacts

## Definition

Playwright's tracing subsystem records an exhaustive, holistic log of a test execution into a single portable zip archive. Rather than recording just a video stream or post-mortem screenshot, a Playwright Trace captures:
- Full DOM snapshots recorded before and after every action.
- Complete network activity, including HTTP request/response payloads, timing waterfalls, and headers.
- Browser console output (`console.log`, `console.error`) and uncaught page exceptions.
- Action timeline metadata indicating exact locator resolution times, auto-wait duration, and call parameters.

The generated trace file can be inspected locally or in a web browser using the Playwright Trace Viewer GUI.

```typescript
import { BrowserContext, Page } from 'playwright';

export async function runTracedScenario(context: BrowserContext, page: Page) {
  // Start recording trace with screenshots, DOM snapshots, and network
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });

  try {
    await page.goto('https://app.example.com/checkout');
    await page.getByRole('button', { name: 'Submit' }).click();
  } finally {
    // Stop tracing and export bundle to disk for diagnosis
    await context.tracing.stop({ path: 'artifacts/trace-checkout-failure.zip' });
  }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts`. When automated tests fail in headless continuous integration runners, reproducing and root-causing failures without comprehensive temporal telemetry is costly and frustrating.

Contrasts with `CONCEPT-selenium-v1-006-01-takes-screenshot-and-logs`. In traditional Selenium environments, diagnosing failures relies on `TakesScreenshot` and static `driver.getPageSource()`. These artifacts provide only a static post-failure snapshot: by the time the failure handler runs, toast messages may have vanished, error banners may have closed, and underlying network failures are lost. Playwright's trace provides an interactive time-travel timeline where engineers can inspect live DOM snapshots, network payloads, and console output at every discrete step of the test.
