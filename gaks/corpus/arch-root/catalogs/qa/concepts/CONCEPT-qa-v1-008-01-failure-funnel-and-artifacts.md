---
id: CONCEPT-qa-v1-008-01-failure-funnel-and-artifacts
status: accepted
subproject: qa
layer: L1-archetype
standing: recommended
realizes: CONCEPT-istqb-v1-001-01-error-defect-failure, CONCEPT-istqb-v1-015-01-defect-lifecycle
---

# The Failure Funnel: Diagnostic Artifacts

## Definition

The Failure Funnel is an automated test infrastructure pattern that progressively captures multi-tiered diagnostic artifacts upon any test failure or timeout, assembling a complete forensic record without requiring manual re-runs.

The forensic tiers captured in the funnel include:
1. **Console & Runner Logs**: Standard out, standard error, browser console messages (`console.error`, unhandled exceptions), and test framework step logs.
2. **Failure Screenshot**: A visual raster image (PNG) of the exact viewport state at the instant of failure, revealing modal overlays, clipping, or visual errors.
3. **DOM Snapshot**: The complete serialized HTML tree at the failure point, enabling inspection of hidden attributes, CSS classes, and aria roles.
4. **Network Archive (HAR)**: A full recording of all HTTP requests, responses, status codes, response payloads, headers, and timing metrics sent or received by the browser.
5. **Execution Trace (Timeline Archive)**: A bundled zip containing millisecond-by-millisecond screencasts, DOM snapshots before and after every action, network events, and call stacks, viewable interactively in a trace viewer.

```text
[ Test Execution Passes ] --------> Discard heavy artifacts (keep minimal logs)
           |
           +---> [ TEST FAILS ]
                       |
                       v
         +-----------------------------+
         |     The Failure Funnel      |
         +-----------------------------+
         | 1. Capture Console Logs     |
         | 2. Capture Viewport PNG     |
         | 3. Dump Serialized DOM      |
         | 4. Export Network HAR       |
         | 5. Finalize Execution Trace |
         +-----------------------------+
                       |
                       v
         [ Attached to CI Run / Defect ]
```

```python
# Fixture capturing forensic artifacts only on test failure
import pytest

@pytest.fixture
def page_with_failure_funnel(browser_context, request):
    # Start tracing with screenshots and DOM snapshots
    browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = browser_context.new_page()
    
    yield page
    
    # Teardown: inspect test execution result
    if request.node.rep_call.failed:
        test_id = request.node.name
        page.screenshot(path=f"artifacts/{test_id}_failure.png")
        browser_context.tracing.stop(path=f"artifacts/{test_id}_trace.zip")
    else:
        # Discard trace on success to conserve storage and bandwidth
        browser_context.tracing.stop()
```

## Why it exists

The Failure Funnel eliminates the ambiguity and lost time associated with headless CI test failures:

1. **Root-Cause Analysis Without Reproduction**: In headless CI environments, developers cannot watch tests execute. Having full network logs, DOM state, and timeline traces allows engineers to diagnose the defect immediately without attempting tricky local reproductions.
2. **Distinguishing App Bugs from Infrastructure Drops**: A network HAR immediately clarifies whether an assertion failed because of a front-end bug or because an internal microservice returned a 504 Gateway Timeout.
3. **Storage Efficiency**: Heavy artifacts (video recordings and full traces) are captured conditionally only when tests fail, keeping CI storage and artifact upload bandwidth lean.
