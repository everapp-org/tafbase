---
id: CONCEPT-selenium-v1-007-01-bidi-network-interception
status: accepted
subproject: selenium
layer: L2-tool
since: Selenium 4.0
standing: recommended
realizes: CONCEPT-qa-v1-009-01-deterministic-replay-and-flakiness
contrasts-with: CONCEPT-playwright-v1-007-01-network-interception-route
---

# W3C WebDriver BiDi Network Interception

## Definition

Selenium 4 introduces bidirectional communication via the emerging W3C WebDriver BiDi standard (and Chrome DevTools Protocol / CDP fallback). 

Through the `NetworkInterceptor` or `HasAuthentication` interfaces, tests can intercept HTTP traffic at the browser engine level, register route filters, authenticate via HTTP Basic Auth dialogs, and substitute canned mock responses for specific network requests.

```java
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.devtools.NetworkInterceptor;
import org.openqa.selenium.remote.http.HttpResponse;
import org.openqa.selenium.remote.http.Route;
import static org.openqa.selenium.remote.http.Contents.utf8String;

public class BiDiNetworkDemo {
    public static void interceptAndMock(WebDriver driver) {
        // Intercept network requests matching route and fulfill with mock JSON
        Route mockApiRoute = Route.matching(req -> req.getUri().contains("/api/user"))
                .to(() -> req -> new HttpResponse()
                        .setStatus(200)
                        .addHeader("Content-Type", "application/json")
                        .setContent(utf8String("{\"id\":1,\"name\":\"Mock User\"}")));

        try (NetworkInterceptor ignored = new NetworkInterceptor(driver, mockApiRoute)) {
            driver.get("https://app.example.com/profile");
            // The browser receives the mocked user profile data
        }
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-009-01-deterministic-replay-and-flakiness`. E2E tests often flake due to external services, transient network hiccups, or rate-limited APIs. Intercepting and stubbing network responses at the browser boundary isolates frontend testing from volatile external backend dependencies.

Contrasts with `CONCEPT-playwright-v1-007-01-network-interception-route`. In earlier Selenium versions (Selenium 2 and 3), network interception was impossible without heavy out-of-process reverse proxies (such as BrowserMob Proxy). Selenium 4's `NetworkInterceptor` introduces this capability via BiDi/CDP, but still operates as a specialized decorator wrapper around WebDriver. Playwright integrates network routing directly into the core `page.route` / `context.route` API as a first-class feature across all supported browsers.
