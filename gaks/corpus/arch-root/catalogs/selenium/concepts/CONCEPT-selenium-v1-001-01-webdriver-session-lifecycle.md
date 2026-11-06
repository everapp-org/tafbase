---
id: CONCEPT-selenium-v1-001-01-webdriver-session-lifecycle
status: accepted
subproject: selenium
layer: L2-tool
since: Selenium 4.0
standing: recommended
realizes: CONCEPT-qa-v1-004-01-session-and-context-isolation
contrasts-with: CONCEPT-playwright-v1-001-01-browser-context-page-hierarchy
---

# WebDriver Session Lifecycle and Selenium Manager

## Definition

In the W3C WebDriver specification implemented by Selenium, a browser session corresponds to an independent browser instance controlled over HTTP via the W3C WebDriver wire protocol. 

Starting in Selenium 4.6+, `SeleniumManager` automatically resolves, downloads, and configures matching browser driver binaries (such as `chromedriver`, `geckodriver`, or `msedgedriver`) at runtime, removing the need for manual driver path setup or external managers.

A session lifecycle follows three explicit phases:
1. **Creation**: `new ChromeDriver(options)` negotiates capabilities with the browser driver process and launches an OS browser process.
2. **Interaction**: Commands are dispatched as standard W3C HTTP wire protocol requests.
3. **Termination**: `driver.quit()` dispatches a `DELETE /session/{session_id}` command to kill the driver and close all associated browser windows and processes.

```java
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

public class SessionLifecycleDemo {
    public static void runTest() {
        // SeleniumManager automatically locates and launches the matching driver binary
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless=new");
        
        WebDriver driver = new ChromeDriver(options);
        try {
            driver.get("https://app.example.com");
            System.out.println("Page title: " + driver.getTitle());
        } finally {
            // Explicitly terminates the W3C session and kills OS browser processes
            driver.quit();
        }
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-004-01-session-and-context-isolation`. Ensuring that test executions execute in pristine environments with isolated cookies and storage is essential for test independence.

Contrasts with `CONCEPT-playwright-v1-001-01-browser-context-page-hierarchy`. In Selenium, session isolation is tightly coupled to the OS process lifecycle: each `new ChromeDriver()` call spawns an entire browser process, which incurs significant CPU and memory overhead (often 1 to 3 seconds per test startup). In contrast, Playwright decouples the browser process from lightweight incognito `BrowserContext` instances, allowing fresh isolation in milliseconds without relaunching the host browser binary.
