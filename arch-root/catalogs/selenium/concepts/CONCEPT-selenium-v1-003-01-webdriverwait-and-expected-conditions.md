---
id: CONCEPT-selenium-v1-003-01-webdriverwait-and-expected-conditions
status: accepted
subproject: selenium
layer: L2-tool
since: Selenium 4.0
standing: recommended
realizes: CONCEPT-qa-v1-003-01-synchronization-and-actionability
contrasts-with: CONCEPT-playwright-v1-003-01-auto-waiting-and-actionability
---

# Explicit WebDriverWait and ExpectedConditions

## Definition

Synchronization in Selenium WebDriver relies on explicit polling via `WebDriverWait` and predefined `ExpectedConditions` (or lambda predicates). 

`WebDriverWait` repeatedly evaluates an expected condition over a configured timeout (e.g., 10 seconds) with a defined polling frequency (typically 500ms), ignoring specific exceptions such as `NoSuchElementException` until the condition evaluates to a truthy value or the timeout is exceeded.

Mixing implicit waits (`driver.manage().timeouts().implicitlyWait(...)`) with explicit waits is an established anti-pattern in Selenium: because both mechanisms poll the browser driver, the W3C specification does not define an order of precedence, causing unpredictable and compounded timeout delays.

```java
import java.time.Duration;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public class SyncDemo {
    public static void submitOrder(WebDriver driver) {
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        // Explicitly wait until the button is both visible and enabled for interaction
        By submitLocator = By.cssSelector("button#confirm-checkout");
        WebElement submitButton = wait.until(ExpectedConditions.elementToBeClickable(submitLocator));
        submitButton.click();

        // Wait until success banner appears in the DOM and becomes visible
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.className("success-message")));
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-003-01-synchronization-and-actionability`. Web browsers render asynchronously; attempting to interact with elements before they are attached, visible, or enabled causes immediate runtime errors.

Contrasts with `CONCEPT-playwright-v1-003-01-auto-waiting-and-actionability`. In Selenium, actions (`click()`, `sendKeys()`) do not auto-wait for interactability checks; if an element is animating or obscured, `click()` immediately fails with `ElementClickInterceptedException`. Consequently, Selenium test authors must explicitly write `wait.until(...)` calls before interacting with elements. In contrast, Playwright automatically performs actionability checks prior to every action, eliminating manual synchronization boilerplate.
