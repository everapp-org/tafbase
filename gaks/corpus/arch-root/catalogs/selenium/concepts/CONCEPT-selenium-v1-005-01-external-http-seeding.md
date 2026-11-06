---
id: CONCEPT-selenium-v1-005-01-external-http-seeding
status: accepted
subproject: selenium
layer: L2-tool
since: Selenium 4.0
standing: recommended
realizes: CONCEPT-qa-v1-006-01-api-fixture-seeding
contrasts-with: CONCEPT-playwright-v1-005-01-api-request-context
---

# External HTTP Seeding and Cookie Injection

## Definition

Because Selenium WebDriver controls only browser interactions and provides no built-in HTTP client for raw network requests, state seeding requires pairing Selenium with an external HTTP library (such as Java 11's `HttpClient`, Apache HttpClient, or OkHttp).

The external HTTP client seeds test entities or authenticates user accounts over fast REST/GraphQL endpoints. To bridge the resulting authentication state to the browser, the driver navigates to the target domain, and cookies are injected into the active session via `driver.manage().addCookie(...)`.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.openqa.selenium.Cookie;
import org.openqa.selenium.WebDriver;

public class HttpSeedingDemo {
    public static void seedAndInject(WebDriver driver) throws Exception {
        // 1. External HTTP client authenticates out-of-band
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://app.example.com/api/login"))
                .POST(HttpRequest.BodyPublishers.ofString("{\"user\":\"test\",\"pass\":\"secret\"}"))
                .header("Content-Type", "application/json")
                .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        // 2. WebDriver must navigate to the domain before cookies can be added
        driver.get("https://app.example.com/404");

        // 3. Inject authenticated session token into the browser session
        driver.manage().addCookie(new Cookie("session_id", "auth-token-xyz", ".example.com", "/", null));

        // 4. Open authenticated page directly
        driver.get("https://app.example.com/dashboard");
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-006-01-api-fixture-seeding`. Setting up complex database records, user permissions, or multi-item carts via the browser UI is time-consuming and introduces unnecessary failure points. Seeding data via HTTP endpoints enables UI tests to focus purely on the core interaction under test.

Contrasts with `CONCEPT-playwright-v1-005-01-api-request-context`. In Selenium, bridging HTTP client state to the browser is a manual, multi-step process: the browser must first load a page on the domain (to avoid cross-domain cookie exceptions) before `addCookie` can succeed. Playwright provides unified `APIRequestContext` instances that can share storage state and cookie jars with browser contexts automatically without intermediate dummy navigations.
