---
id: CONCEPT-selenium-v1-006-01-takes-screenshot-and-logs
status: accepted
subproject: selenium
layer: L2-tool
since: Selenium 4.0
standing: recommended
realizes: CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts
contrasts-with: CONCEPT-playwright-v1-006-01-trace-viewer-and-artifacts
---

# Failure Diagnostics via TakesScreenshot and BiDi Logs

## Definition

In Selenium WebDriver, diagnosing test failures relies on extracting point-in-time runtime artifacts upon test failure:
- **Screenshots**: Cast the `WebDriver` instance to `TakesScreenshot` and call `getScreenshotAs(OutputType.FILE)` to capture a PNG image of the current viewport.
- **DOM Snapshot**: Call `driver.getPageSource()` to extract the raw HTML string as rendered at the instant of failure.
- **BiDi / CDP Console Logs**: In Selenium 4, register listeners via `driver.manage().logs()` or BiDi log listeners (`LogInspector.onConsoleEntry(...)`) to capture JavaScript console warnings and uncaught exceptions.

```java
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;

public class DiagnosticArtifactsDemo {
    public static void captureFailureState(WebDriver driver, String testName) {
        try {
            // 1. Capture viewport screenshot as PNG
            File screenshotFile = ((TakesScreenshot) driver).getScreenshotAs(OutputType.FILE);
            Files.copy(screenshotFile.toPath(), Paths.get("target/artifacts/" + testName + ".png"));

            // 2. Dump raw DOM source
            String domHtml = driver.getPageSource();
            Files.writeString(Paths.get("target/artifacts/" + testName + ".html"), domHtml);
        } catch (Exception e) {
            System.err.println("Failed to capture diagnostics: " + e.getMessage());
        }
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts`. When automated tests fail on unattended CI runners, static stack traces alone are often insufficient to discern whether a failure stemmed from an unexpected modal dialog, a 500 server error page, or an unrendered UI component.

Contrasts with `CONCEPT-playwright-v1-006-01-trace-viewer-and-artifacts`. Selenium artifacts are strictly post-mortem and disjointed: a static screenshot and text HTML dump captured after the failure already occurred. They do not retain the temporal history of interactions, DOM mutations, or network requests leading up to the failure. In contrast, Playwright's Trace Viewer records a comprehensive step-by-step interactive timeline with full DOM states before and after each action, complete network waterfalls, and console outputs in a single trace package.
