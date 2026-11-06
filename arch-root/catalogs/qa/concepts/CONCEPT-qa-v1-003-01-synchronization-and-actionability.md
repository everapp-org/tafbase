---
id: CONCEPT-qa-v1-003-01-synchronization-and-actionability
status: accepted
subproject: qa
layer: L1-archetype
standing: recommended
realizes: CONCEPT-istqb-v1-006-01-static-vs-dynamic-testing
---

# UI Synchronization and Actionability Waiting

## Definition

UI Synchronization and Actionability Waiting is an automation architecture pattern that synchronizes test actions with dynamic, asynchronous browser execution without using arbitrary static sleep intervals (`time.sleep()` or `Thread.sleep()`).

Before interacting with an element (e.g., clicking, typing, selecting), an automation engine must verify that the target element has reached an **Actionable State**:
1. **Attached**: The element is present in the Document Object Model (DOM).
2. **Visible**: The element has non-empty bounding box dimensions and lacks styles such as `display: none` or `visibility: hidden`.
3. **Stable**: The element has finished CSS transitions and animations and its coordinates are stationary.
4. **Enabled**: The element does not have the `disabled` attribute and is not blocked by a form fieldset.
5. **Editable**: For input fields, the element is not `readonly` or disabled.
6. **Receives Events**: The element is not obscured or occluded by overlaying modal backdrops, dialogs, or sticky banners.

Rather than pausing for fixed durations, actionability engines poll the DOM and layout engine automatically until all conditions are satisfied or an explicit timeout expires.

```text
Action Request: click(button)
      |
      v
+-------------------------------------------------------------+
| Check Actionability Predicates:                            |
| 1. Is attached to DOM?                   [Yes]              |
| 2. Is visible (bounding box > 0)?        [Yes]              |
| 3. Is stable (animations finished)?      [Waiting... Yes]   |
| 4. Is enabled (not disabled)?            [Yes]              |
| 5. Can receive pointer events (unmasked)?[Yes]              |
+-------------------------------------------------------------+
      |
      +---> Dispatch Click Event
```

```python
# Bad Anti-pattern: Hardcoded sleep produces brittle or painfully slow tests
import time
time.sleep(5)  # Guessing: 5 seconds might be too short on CI, too long locally
page.locator("#submit-btn").click()

# Good Archetype: Auto-waiting actionability synchronization
# The framework waits for attached, visible, stable, enabled, and unmasked state:
page.get_by_role("button", name="Submit").click(timeout=5000)
```

## Why it exists

Synchronization failures represent the leading source of intermittent flakiness in automated UI test suites:

1. **Eliminating Race Conditions**: Modern web applications render asynchronously via micro-tasks, client-side routing, and background HTTP fetches. A button may appear in the DOM milliseconds before its event handlers are wired or before its CSS animation finishes moving it under the cursor.
2. **Maximizing Pipeline Speed**: Hardcoded sleep statements accumulate across test suites. A suite of 500 tests with three 2-second sleeps each adds 50 minutes of dead waiting time to CI builds. Actionability checks proceed the exact millisecond the element is ready.
3. **Self-Documenting Failure Diagnostics**: When an actionability check times out, the framework reports the exact missing predicate (e.g., "Element is visible but covered by `<div class='modal-backdrop'>`"), instantly highlighting the root cause.
