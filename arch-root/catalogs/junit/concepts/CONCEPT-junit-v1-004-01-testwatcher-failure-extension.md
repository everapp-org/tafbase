---
id: CONCEPT-junit-v1-004-01-testwatcher-failure-extension
status: accepted
subproject: junit
layer: L2-tool
since: JUnit 5.10
standing: recommended
realizes: CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts
---

# TestWatcher Extension for Failure Artifacts

## Definition

JUnit Jupiter's `TestWatcher` interface provides lifecycle callback hooks to monitor test execution outcomes without modifying test method logic. 

By implementing `TestWatcher` (or `AfterTestExecutionCallback`), an extension can intercept test completions:
- `testSuccessful(ExtensionContext context)`: Invoked when a test passes.
- `testFailed(ExtensionContext context, Throwable cause)`: Invoked when an assertion fails or an unexpected exception occurs.
- `testAborted(ExtensionContext context, Throwable cause)`: Invoked when an assumption fails (`Assumptions.assumeTrue`).
- `testDisabled(ExtensionContext context, Optional<String> reason)`: Invoked when a test is skipped.

In automated UI suites, `testFailed` extracts the active browser driver or context from the `ExtensionContext.Store` and dumps screenshots, page source, and network logs to the artifact directory.

```java
import java.io.File;
import org.junit.jupiter.api.extension.ExtensionContext;
import org.junit.jupiter.api.extension.TestWatcher;

public class FailureScreenshotExtension implements TestWatcher {

    @Override
    public void testFailed(ExtensionContext context, Throwable cause) {
        String testMethod = context.getRequiredTestMethod().getName();
        String testClass = context.getRequiredTestClass().getSimpleName();
        System.err.println("Test failed: " + testClass + "#" + testMethod + " -> Capturing diagnostics...");

        // Retrieve the driver or context stored in the Jupiter Store
        ExtensionContext.Store store = context.getStore(ExtensionContext.Namespace.create(getClass(), context));
        ArtifactCollector collector = store.get("collector", ArtifactCollector.class);
        if (collector != null) {
            collector.saveScreenshot("target/failures/" + testClass + "_" + testMethod + ".png");
        }
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts`. Wrapping every individual test method in `try-catch` blocks to capture failure screenshots pollutes test code and risks suppressing assertion exceptions.

Jupiter extensions decouple diagnostic infrastructure from test business logic. Registering `TestWatcher` via `@ExtendWith` or the ServiceLoader SPI guarantees that whenever any test method fails across the suite, rich diagnostic artifacts are automatically captured and routed to the failure funnel.
