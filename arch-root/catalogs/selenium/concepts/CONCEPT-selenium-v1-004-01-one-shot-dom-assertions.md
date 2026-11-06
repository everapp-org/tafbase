---
id: CONCEPT-selenium-v1-004-01-one-shot-dom-assertions
status: accepted
subproject: selenium
layer: L2-tool
since: Selenium 4.0
standing: recommended
realizes: CONCEPT-qa-v1-007-01-hard-vs-soft-assertions
contrasts-with: CONCEPT-playwright-v1-004-01-web-first-assertions
---

# One-Shot DOM Assertions

## Definition

Selenium WebDriver does not include a native assertion framework. Instead, test suites pair Selenium with test runners (such as JUnit or TestNG) or assertion libraries (such as AssertJ). 

In this pattern, assertions are "one-shot": they inspect a snapshot of DOM state at a single moment in time. To avoid race conditions, test authors must first explicitly synchronize the browser state via `WebDriverWait` before evaluating the one-shot assertion.

```java
import java.time.Duration;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class AssertionDemo {
    public static void verifyHeader(WebDriver driver) {
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(5));

        // 1. Explicit wait pre-synchronizes until expected text is populated
        By headerLocator = By.tagName("h1");
        wait.until(ExpectedConditions.textToBePresentInElementLocated(headerLocator, "Dashboard"));

        // 2. One-shot runner assertion evaluates static string snapshot
        WebElement header = driver.findElement(headerLocator);
        assertEquals("Dashboard", header.getText());
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-007-01-hard-vs-soft-assertions`. Clear separation of concerns between browser automation driver and test runner assertions has historically allowed WebDriver to remain language- and framework-agnostic.

Contrasts with `CONCEPT-playwright-v1-004-01-web-first-assertions`. One-shot assertions evaluate immediately without polling. If an assertion runs before client-side hydration or rendering completes, it fails immediately even if the state settles milliseconds later. In Selenium, avoiding this flakiness requires manually combining `wait.until(...)` conditions with separate assertion lines. Playwright resolves this duality by embedding retrying polling logic directly into web-first assertions (`expect(locator).toHaveText(...)`).
