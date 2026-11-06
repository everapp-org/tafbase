---
id: CONCEPT-pwtest-v1-002-01-data-driven-test-loop
status: accepted
subproject: pwtest
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-istqb-v1-007-01-equivalence-partitioning, CONCEPT-istqb-v1-008-01-boundary-value-analysis
contrasts-with: CONCEPT-junit-v1-002-01-parameterized-test-and-sources, CONCEPT-pytest-v1-002-01-mark-parametrize
---

# Data-Driven Parameterized Test Loops

## Definition

In Playwright Test Runner (`@playwright/test`), parameterized or data-driven tests are defined using standard JavaScript iteration constructs (`for...of`, `.forEach()`) at top-level module evaluation time. 

Rather than relying on proprietary annotations or runner decorators, each iteration dynamically registers a distinct `test(title, testFn)` invocation with interpolated test case names. Each iteration runs as an independent test with isolated fixture allocations, individual retry policies, and granular reporting entries.

```typescript
import { test, expect } from '@playwright/test';

interface TestCase {
  tier: string;
  quantity: number;
  expectedDiscount: number;
}

const discountTestCases: TestCase[] = [
  { tier: 'STANDARD', quantity: 1, expectedDiscount: 0.00 },
  { tier: 'STANDARD', quantity: 10, expectedDiscount: 0.05 },
  { tier: 'VIP',      quantity: 1, expectedDiscount: 0.10 },
  { tier: 'VIP',      quantity: 5, expectedDiscount: 0.15 },
];

for (const { tier, quantity, expectedDiscount } of discountTestCases) {
  test(`calculates discount for ${tier} with quantity ${quantity}`, async ({ page }) => {
    await page.goto('https://app.example.com/pricing');
    await page.getByLabel('Customer Tier').selectOption(tier);
    await page.getByLabel('Item Quantity').fill(String(quantity));
    await page.getByRole('button', { name: 'Calculate' }).click();

    const result = page.getByTestId('discount-display');
    await expect(result).toHaveText(`${(expectedDiscount * 100).toFixed(0)}%`);
  });
}
```

## Why it exists

Realizes `CONCEPT-istqb-v1-007-01-equivalence-partitioning` and `CONCEPT-istqb-v1-008-01-boundary-value-analysis`. Testing equivalence classes and boundary values requires executing the same test logic across multiple input vectors while generating distinct, identifiable test results for each vector.

Contrasts with `CONCEPT-junit-v1-002-01-parameterized-test-and-sources` and `CONCEPT-pytest-v1-002-01-mark-parametrize`. In JUnit 5 and pytest, test runners require specialized framework annotations (`@ParameterizedTest`, `@pytest.mark.parametrize`) and reflection to supply data matrices to functions. Playwright Test treats test registration as standard JavaScript runtime execution: because `test()` is a regular function call, standard loops, arrays, JSON imports, and generator functions naturally generate test suites without framework-specific DSLs.
