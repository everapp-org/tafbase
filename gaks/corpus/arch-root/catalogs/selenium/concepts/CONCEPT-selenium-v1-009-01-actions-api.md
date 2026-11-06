---
id: CONCEPT-selenium-v1-009-01-actions-api
status: accepted
subproject: selenium
layer: L2-tool
since: Selenium 4.0
standing: recommended
realizes: CONCEPT-qa-v1-003-01-synchronization-and-actionability
---

# Low-Level Actions API for Complex Interactions

## Definition

Selenium's `Actions` class provides an interface for synthesizing low-level W3C input events (pointer, keyboard, and wheel gestures). 

Unlike high-level convenience methods (`element.click()`, `element.sendKeys()`), `Actions` allows chaining precise discrete physical actions: moving the pointer to element coordinates, pressing and releasing specific mouse buttons, holding keyboard modifiers (`Keys.SHIFT`, `Keys.CONTROL`), dragging elements across coordinates, and scrolling scrollable containers. Calling `.perform()` compiles the sequence into W3C input action payloads and dispatches them across the wire protocol.

```java
import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.interactions.Actions;

public class ActionsApiDemo {
    public static void dragAndDropWithModifier(WebDriver driver) {
        WebElement sourceItem = driver.findElement(By.cssSelector(".draggable-card"));
        WebElement targetDropZone = driver.findElement(By.cssSelector(".kanban-column"));

        // Build a composite gesture sequence: hover, hold Ctrl, drag, and release
        new Actions(driver)
                .moveToElement(sourceItem)
                .keyDown(Keys.CONTROL)
                .clickAndHold(sourceItem)
                .moveToElement(targetDropZone)
                .release()
                .keyUp(Keys.CONTROL)
                .perform();
    }
}
```

## Why it exists

Realizes `CONCEPT-qa-v1-003-01-synchronization-and-actionability`. Rich client-side web interfaces frequently rely on complex gestures—such as drag-and-drop file upload zones, interactive canvas drawing, custom slider controls, and multi-select lists using modifier keys—that cannot be triggered by basic click or text-entry primitives.

The `Actions` API adheres to the W3C WebDriver Input specification, translating composite user interactions into faithful low-level OS-like input sequences across all conforming browser implementations.
