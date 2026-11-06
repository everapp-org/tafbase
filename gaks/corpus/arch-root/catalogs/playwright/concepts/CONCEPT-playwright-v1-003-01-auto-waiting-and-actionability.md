---
id: CONCEPT-playwright-v1-003-01-auto-waiting-and-actionability
status: accepted
subproject: playwright
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-003-01-synchronization-and-actionability
contrasts-with: CONCEPT-selenium-v1-003-01-webdriverwait-and-expected-conditions
---

# Built-in Auto-Waiting and Actionability Checks

## Definition

Playwright performs comprehensive actionability checks automatically prior to executing any user interaction (such as `.click()`, `.fill()`, `.check()`, or `.hover()`). 

Before performing an action, Playwright verifies that the targeted element satisfies a strict set of prerequisites:
1. **Attached**: Present in the Document Object Model.
2. **Visible**: Non-empty bounding box, not hidden (`display: none`, `visibility: hidden`), and viewport-visible.
3. **Stable**: Not undergoing CSS transitions or geometric animations.
4. **Receives Events**: Not covered or occluded by modal overlays, backdrop scrims, or sticky banners.
5. **Enabled**: Form controls are not disabled (`disabled` attribute).
6. **Editable**: Form inputs are enabled and not marked `readOnly`.

If any check fails, Playwright retries continuously until all conditions pass or the configured action timeout expires.

```typescript
import { Page } from 'playwright';

export async function completeCheckout(page: Page) {
  // Automatically waits for #confirm-btn to be attached, visible,
  // stationary, enabled, and unoccluded by loading spinners
  await page.getByRole('button', { name: 'Confirm Purchase' }).click();

  // Automatically waits for input to be editable before typing
  await page.getByLabel('Cardholder Name').fill('Alex Morgan');
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-003-01-synchronization-and-actionability`. Modern web applications are fundamentally asynchronous, rendering components, animating layouts, and mounting client-side state dynamically. Manual timing coordination is the leading cause of test flakiness in end-to-end suites.

Contrasts with `CONCEPT-selenium-v1-003-01-webdriverwait-and-expected-conditions`. In Selenium WebDriver, invoking `element.click()` attempts an immediate dispatch against the element. If an animation is in flight or a modal backdrop has not fully dissolved, WebDriver throws `ElementClickInterceptedException` or `ElementNotInteractableException`. Test authors must manually interleave explicit `WebDriverWait` statements and expected conditions before every interaction. Playwright eliminates this boilerplate entirely by baking actionability verification into the runtime dispatch pipeline.
