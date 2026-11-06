---
id: CONCEPT-pwtest-v1-005-01-projects-matrix-and-sharding
status: accepted
subproject: pwtest
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-istqb-v1-013-01-confirmation-vs-regression-testing, CONCEPT-prog-v1-007-01-parallel-fan-out
---

# Multi-Project Matrix and Worker Sharding

## Definition

Playwright Test Runner (`@playwright/test`) provides matrix orchestration and distributed parallel execution primitives:
- **`projects` Matrix**: Configured in `playwright.config.ts`, projects define distinct test environments (e.g. Chromium, Firefox, WebKit, Mobile Safari) sharing the same test codebase, with specific browser options, viewports, or device emulations.
- **Tag Filtering**: Tests are tagged using `@tag` syntax in test titles or the `tag` option (`test('verifies order', { tag: '@smoke' }, ...)`), selectable via CLI `--grep "@smoke"`.
- **Sharding**: The `--shard=x/y` command splits the total test execution suite evenly across multiple independent CI worker nodes (e.g., `--shard=1/4`, `--shard=2/4`), providing horizontal linear scaling.

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  fullyParallel: true, // Run individual tests inside files concurrently
  workers: process.env.CI ? 4 : undefined,
  projects: [
    {
      name: 'desktop-chrome',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'desktop-firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 14'] },
    },
  ],
});
```

CLI commands:
```bash
npx playwright test --grep "@smoke" # Execute only smoke tagged tests across the project matrix
npx playwright test --shard=1/4     # Shard execution across 4 parallel CI machines (Worker 1 of 4)
```

## Why it exists

Realizes `CONCEPT-istqb-v1-013-01-confirmation-vs-regression-testing` and `CONCEPT-prog-v1-007-01-parallel-fan-out`. Large test suites running across multiple browser engines and device form factors quickly become too slow for single-machine sequential execution.

Multi-project configuration unifies cross-browser and cross-device testing within a single declarative configuration file. Native `--shard` support enables zero-configuration parallel horizontal scaling across distributed CI job matrices, cutting total pipeline execution time to minutes.
