---
id: CONCEPT-qa-v1-007-01-hard-vs-soft-assertions
status: accepted
subproject: qa
layer: L1-archetype
standing: recommended
realizes: CONCEPT-istqb-v1-012-01-test-oracle
---

# Hard Assertions, Soft Assertions, and Auto-Retrying Assertions

## Definition

Automated test frameworks utilize three distinct assertion paradigms depending on execution context, criticality, and timing:

1. **Hard Assertions**: Standard assertions that throw an exception immediately upon the first condition failure, halting test execution instantly. Subsequent lines in the test case are never executed. Ideal for prerequisite validations where proceeding would be futile or cause cascading misleading errors.
2. **Soft Assertions (Collected Assertions)**: Assertions that record validation failures in a collector without aborting test execution immediately. The test continues executing subsequent assertions, and all accumulated discrepancies are reported together at the end of the test. Ideal for verifying complex multi-field forms, tables, or dashboards.
3. **Auto-Retrying Web-First Assertions**: Dynamic assertions designed for asynchronous user interfaces. Instead of checking a condition once at a fixed instant, they repeatedly re-evaluate the expectation against the live DOM until it passes or a configurable timeout expires (e.g., `expect(locator).to_have_text(...)`).

```python
# 1. Hard Assertion: Stop immediately if login failed
assert page.get_by_role("heading", name="Dashboard").is_visible(), "Dashboard failed to load"

# 2. Soft Assertion: Verify all user profile fields in one pass
def test_user_profile_fields(page, soft_assert):
    soft_assert.equal(page.get_by_test_id("first-name").input_value(), "Jane")
    soft_assert.equal(page.get_by_test_id("last-name").input_value(), "Doe")
    soft_assert.equal(page.get_by_test_id("email").input_value(), "jane@example.com")
    soft_assert.assert_all()  # Reports all mismatches at once

# 3. Auto-Retrying Web-First Assertion: Polls DOM until async API response renders
from playwright.sync_api import expect
expect(page.get_by_test_id("notification-toast")).to_have_text("Profile Saved", timeout=5000)
```

## Why it exists

Matching the appropriate assertion paradigm to the verification task avoids common automation traps:

1. **Avoiding the 1-Bug-Per-Run Feedback Loop**: With hard assertions alone, verifying a form with 10 fields requires 10 full test runs if multiple fields are broken, because the test aborts on the first error. Soft assertions capture all 10 discrepancies in a single execution.
2. **Eliminating Race Conditions in UI Tests**: Checking `assert element.is_visible()` synchronously will fail if the front-end takes 50 milliseconds to finish rendering. Auto-retrying assertions eliminate timing race conditions by polling smoothly until the expected condition is met.
3. **Failing Fast on Fatal Preconditions**: Hard assertions remain essential when a failure renders further test steps meaningless (e.g., if navigating to the page resulted in a 500 Internal Server Error).
