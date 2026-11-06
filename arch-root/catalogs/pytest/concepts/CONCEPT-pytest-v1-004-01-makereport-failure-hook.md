---
id: CONCEPT-pytest-v1-004-01-makereport-failure-hook
status: accepted
subproject: pytest
layer: L2-tool
since: pytest 8.0
standing: recommended
realizes: CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts
---

# Failure Reporting Hook via makereport

## Definition

Pytest's plugin architecture exposes `pytest_runtest_makereport`, a generator hook called during each phase of test execution: `setup`, `call`, and `teardown`.

By wrapping the hook execution with `outcome = yield`, an implementation receives the generated `TestReport` object. If `report.when == "call"` and `report.failed` evaluates to true, the hook can inspect the failed test item, extract active browser driver or page fixtures, capture screenshots, trace files, or DOM dumps, and attach them directly to HTML reports or test artifact stores.

```python
"""Fixture and hook definitions in conftest.py."""
import pytest
from pathlib import Path

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Execute all other hooks to obtain the report object
    outcome = yield
    report = outcome.get_result()

    # Capture diagnostic artifacts only when the test execution phase fails
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            artifact_dir = Path("reports/artifacts")
            artifact_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = artifact_dir / f"{item.name}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[FAILURE ARTIFACT] Saved screenshot to {screenshot_path}")
```

## Why it exists

Realizes `CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts`. When running tests in headless CI pipelines, diagnosing failures requires capturing visual and network context precisely when an assertion fails. 

Hardcoding screenshot capture in individual test functions creates duplication and obscures core test logic. The `pytest_runtest_makereport` hook cleanly isolates diagnostic capture logic into the test harness, guaranteeing that every failure across the test suite is captured consistently without modifying test authoring patterns.
