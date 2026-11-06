---
id: CONCEPT-selenium-v1-002-01-by-locators-and-webelement
status: accepted
subproject: selenium
layer: L2-tool
since: Selenium 4.0
standing: recommended
realizes: CONCEPT-qa-v1-002-01-the-locator-ladder
contrasts-with: CONCEPT-playwright-v1-002-01-semantic-locators
---

# By Locators, WebElement, and Stale Element References

## Definition

Selenium identifies elements using `By` query strategies (`By.id`, `By.name`, `By.cssSelector`, `By.xpath`, `By.linkText`) passed to `driver.findElement(by)`. Selenium 4 also introduces `RelativeLocator` (`with(by).above(...)`, `.below(...)`, `.toLeftOf(...)`, `.toRightOf(...)`, `.near(...)`).

Calling `findElement` executes an eager DOM lookup and returns a `WebElement` containing an opaque node ID. If the DOM mutates, re-renders, or replaces the referenced node before an action is invoked on that `WebElement`, the reference becomes invalid, throwing `StaleElementReferenceException`.

```java
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.locators.RelativeLocator;

public class LocatorDemo {
    public static void submitForm(WebDriver driver) {
        // Eager DOM lookup returning a specific node reference
        WebElement emailInput = driver.findElement(By.id("user-email"));
        emailInput.sendKeys("user@example.com");

        // Selenium 4 Relative Locator relative to another element
        By submitBy = RelativeLocator.with(By.tagName("button")).below(emailInput);
        WebElement submitButton = driver.findElement(submitBy);
        
        // If the page dynamically re-rendered submitButton, this call throws StaleElementReferenceException
        submitButton.click();
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-002-01-the-locator-ladder`. Structural `By` mechanisms allow navigating document trees across any browser supporting the W3C WebDriver standard.

Contrasts with `CONCEPT-playwright-v1-002-01-semantic-locators`. In Selenium, `WebElement` represents an eager snapshot reference to a DOM node; it does not automatically re-query the DOM upon subsequent calls, necessitating manual retry logic or PageFactory proxies to recover from staleness. Furthermore, `driver.findElement` silently returns the first matching element if a locator matches multiple nodes, whereas Playwright's lazy locators enforce strict single-element resolution and re-evaluate dynamically at action dispatch time.
