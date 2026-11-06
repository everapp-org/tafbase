---
id: CONCEPT-playwright-v1-002-01-semantic-locators
status: accepted
subproject: playwright
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-002-01-the-locator-ladder
contrasts-with: CONCEPT-selenium-v1-002-01-by-locators-and-webelement
---

# Semantic Locators and Strict Element Resolution

## Definition

Playwright `Locator` objects represent lazy search definitions over the live DOM rather than static node references. They prioritize accessible, user-facing semantics over DOM structural implementation details:

- `page.getByRole(role, options)`: Matches elements by WAI-ARIA role and accessible name.
- `page.getByLabel(text)`: Matches form inputs associated with a `<label>`.
- `page.getByText(text)`: Matches visible text contents.
- `page.getByTestId(id)`: Matches dedicated test identifiers (configured via `testIdAttribute`).

Locators enforce strict single-element resolution: executing an action like `.click()` against a locator that resolves to multiple elements throws an ambiguity error immediately rather than picking an element arbitrarily.

```typescript
import { Page, Locator } from 'playwright';

export async function submitOrder(page: Page) {
  // Lazy locator definitions targeting accessible semantics
  const submitButton: Locator = page.getByRole('button', { name: 'Place Order' });
  const emailInput: Locator = page.getByLabel('Billing Email');
  const termsCheckbox: Locator = page.getByRole('checkbox', { name: 'I accept terms' });

  // Evaluation occurs strictly at action time
  await emailInput.fill('customer@example.com');
  await termsCheckbox.check();
  await submitButton.click();
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-002-01-the-locator-ladder`. Reliable automated UI tests interact with applications through the same affordances that end users and assistive technologies perceive, insulating test suites from benign CSS refactoring or wrapper element churn.

Contrasts with `CONCEPT-selenium-v1-002-01-by-locators-and-webelement`. In Selenium, calling `driver.findElement(By.cssSelector(...))` immediately executes an eager DOM query and returns a `WebElement` reference pointing to a single DOM node. If the page re-renders, subsequent operations throw `StaleElementReferenceException`. Furthermore, Selenium's `findElement` silently returns the first matching element if a locator resolves to multiple nodes, masking locator ambiguity defects that Playwright's strictness mode catches instantly.
