---
id: CONCEPT-selenium-v1-010-01-remote-webdriver-and-grid
status: accepted
subproject: selenium
layer: L2-tool
since: Selenium 4.0
standing: recommended
realizes: CONCEPT-qa-v1-004-01-session-and-context-isolation
---

# RemoteWebDriver and Distributed Selenium Grid

## Definition

Selenium's `RemoteWebDriver` decouples the test runner executing the automation code from the physical machine or container hosting the browser binary. 

By passing the URL of a Selenium Grid Hub (or cloud provider endpoint) alongside `Capabilities` or `ChromeOptions`, `RemoteWebDriver` serializes all W3C commands over HTTP to the grid router. Selenium Grid 4 distributes incoming session requests across registered worker nodes based on requested browser types, platform architectures, and version constraints.

```java
import java.net.URI;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.remote.RemoteWebDriver;

public class RemoteGridDemo {
    public static void executeOnGrid() throws Exception {
        ChromeOptions options = new ChromeOptions();
        options.setBrowserVersion("120");
        options.setPlatformName("Linux");

        // Connect to distributed Selenium Grid router endpoint
        WebDriver driver = new RemoteWebDriver(
                URI.create("http://selenium-grid.internal:4444").toURL(),
                options
        );

        try {
            driver.get("https://app.example.com");
            System.out.println("Title: " + driver.getTitle());
        } finally {
            driver.quit();
        }
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-004-01-session-and-context-isolation`. Enterprise test suites often require execution against heterogeneous environments—different operating systems (Windows, macOS, Linux), specific browser versions, or scaled ephemeral Docker clusters—that cannot all run locally on a developer workstation or single CI agent.

`RemoteWebDriver` establishes an open network protocol layer, allowing test suites to scale out horizontally across massive distributed server farms while maintaining identical client-side test code.
