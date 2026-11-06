---
id: CONCEPT-playwright-v1-009-01-frame-and-shadow-dom-piercing
status: accepted
subproject: playwright
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-002-01-the-locator-ladder
contrasts-with: CONCEPT-selenium-v1-008-01-switchto-frame-and-shadow-root
---

# Automatic Shadow DOM Piercing and Frame Locators

## Definition

Playwright provides native transparency across encapsulation boundaries in modern web architectures:
- **Automatic Shadow DOM Piercing**: All standard CSS and role locators pierce open Shadow DOM boundaries automatically by default. Locating an element inside nested Web Components requires no custom traversal logic or shadow root piercing syntax.
- **FrameLocator API**: The `page.frameLocator(selector)` interface provides lazy, declarative locator chaining into `<iframe>` elements without stateful context switching.

```typescript
import { Page } from 'playwright';

export async function interactWithEncapsulatedComponents(page: Page) {
  // 1. Transparent Shadow DOM traversal:
  // Automatically pierces through open web component shadow roots
  await page.getByRole('button', { name: 'Save Settings' }).click();

  // 2. Declarative FrameLocator chaining:
  // Locates payment form inside a secure hosted iframe without stateful switching
  const paymentFrame = page.frameLocator('iframe#stripe-payment-frame');
  await paymentFrame.getByLabel('Card Number').fill('4242424242424242');
  await paymentFrame.getByRole('button', { name: 'Authorize' }).click();

  // Subsequent actions immediately target the main frame without resetting context
  await page.getByRole('heading', { name: 'Order Summary' }).waitFor();
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-002-01-the-locator-ladder`. Encapsulation features like Shadow DOM and embedded `<iframe>` elements are common in modern web design, micro-frontends, and third-party payment widgets. Automation engines that treat these boundaries as impenetrable walls introduce fragile, stateful workarounds.

Contrasts with `CONCEPT-selenium-v1-008-01-switchto-frame-and-shadow-root`. In Selenium WebDriver, frames require stateful global switches (`driver.switchTo().frame(...)`). Once switched, all subsequent calls target that frame until explicitly restored via `driver.switchTo().defaultContent()`. An unhandled exception inside a frame leaves the driver in an inconsistent state. For Shadow DOM, Selenium 4 requires invoking `element.getShadowRoot()` and querying within that root. Playwright's declarative locators handle both boundaries seamlessly while keeping test definitions stateless and robust.
