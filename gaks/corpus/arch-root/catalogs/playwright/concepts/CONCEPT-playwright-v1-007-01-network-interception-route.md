---
id: CONCEPT-playwright-v1-007-01-network-interception-route
status: accepted
subproject: playwright
layer: L2-tool
since: Playwright 1.40
standing: recommended
realizes: CONCEPT-qa-v1-009-01-deterministic-replay-and-flakiness
contrasts-with: CONCEPT-selenium-v1-007-01-bidi-network-interception
---

# Network Interception and Route Mocking

## Definition

Playwright's routing subsystem enables in-process interception, inspection, modification, and mocking of network requests issued by the browser. 

Through `page.route(urlPattern, handler)` or `context.route(...)`, test scripts intercept HTTP traffic at the browser protocol level without external proxy daemons:
- `route.fulfill()`: Returns mock responses with custom status codes, headers, and JSON or string bodies.
- `route.continue()`: Allows the request to proceed to the real network, optionally modifying request headers or payload.
- `route.abort()`: Simulates network disconnects, failed DNS lookups, or SSL errors.
- `page.waitForResponse()`: Awaits specific network responses matching predicate filters.

```typescript
import { Page } from 'playwright';

export async function testPaymentFailureHandling(page: Page) {
  // Intercept payment gateway API call and stub 500 error
  await page.route('**/api/v1/charge', async (route) => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Gateway timeout', code: 'GATEWAY_ERROR' })
    });
  });

  await page.goto('https://app.example.com/billing');
  await page.getByRole('button', { name: 'Pay Now' }).click();

  // Verify that UI gracefully handles the stubbed server error
  await page.getByText('Payment gateway unavailable. Please retry.').waitFor();
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-009-01-deterministic-replay-and-flakiness`. E2E tests often flake when relying on volatile third-party services (such as payment gateways, SMS verifications, or analytics beacons). Mocking or controlling network responses allows isolating the frontend under test and deterministically evaluating rare edge cases and error states.

Contrasts with `CONCEPT-selenium-v1-007-01-bidi-network-interception`. In Selenium, network interception historically required spinning up separate external HTTP proxy servers (like BrowserMob Proxy), modifying browser proxy settings, and decrypting HTTPS traffic with custom certificates. While Selenium 4 introduced CDP and BiDi network support, it requires managing low-level WebSocket listeners and event handlers. Playwright provides a declarative, synchronous routing API integrated natively across all supported browser engines.
