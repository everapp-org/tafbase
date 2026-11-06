---
id: CONCEPT-qa-v1-004-01-session-and-context-isolation
status: accepted
subproject: qa
layer: L1-archetype
standing: recommended
realizes: CONCEPT-istqb-v1-013-01-confirmation-vs-regression-testing, CONCEPT-prog-v1-006-01-scoped-test-fixture
---

# Session and Context Isolation

## Definition

Session and Context Isolation is an architectural discipline in test automation requiring every individual test case to execute inside a completely isolated, pristine runtime session without state leakage from preceding tests.

In browser automation, this means creating an independent **Browser Context** (an isolated multi-page environment with its own in-memory cookies, local storage, session storage, service workers, and cache) for each test. The heavy browser binary process is launched once per worker process, while lightweight browser contexts are created and destroyed in milliseconds for each test.

Isolation guarantees:
- **Zero Cross-Test Pollution**: Actions performed in Test A (e.g., logging in, setting cookies, populating indexedDB, filling cart) cannot contaminate or alter the initial state of Test B.
- **Order Independence**: Tests can execute in any permutation or order without changing pass/fail outcomes.
- **Parallel Safety**: Tests can run concurrently across dozens of worker threads and CPU cores against the same browser process without collision.

```text
[Browser Process] (Heavyweight OS process, launched once per worker)
       |
       +---> [Context 1] (Pristine Cookies, LocalStorage) ---> [Page 1] (Test A)
       |
       +---> [Context 2] (Pristine Cookies, LocalStorage) ---> [Page 2] (Test B)
       |
       +---> [Context 3] (Pristine Cookies, LocalStorage) ---> [Page 3] (Test C)
```

```python
import pytest

@pytest.fixture
def isolated_page(browser):
    # Create a brand new, isolated incognito browser context
    context = browser.new_context()
    page = context.new_page()
    yield page
    # Teardown: Instantly wipe all cookies, storage, and open tabs
    context.close()

def test_login_first_user(isolated_page):
    isolated_page.goto("/login")
    # ... executes with zero cached session

def test_guest_user_flow(isolated_page):
    isolated_page.goto("/dashboard")
    # ... guaranteed not logged in as first user
```

## Why it exists

Session isolation eliminates test pollution, which is the second most common cause of test suite flakiness:

1. **Eradicating Mystery Failures**: When tests share a browser session or user profile, a failure in Test 3 leaves the browser in an dirty state, causing Tests 4, 5, and 6 to fail as false positives ("cascading failures").
2. **Enabling High-Throughput Parallelism**: Independent contexts allow test runners to execute 16 or 32 browser tests simultaneously on a single multi-core CI node with zero cross-talk.
3. **Reproducibility**: When a test fails in CI, a developer can run that single isolated test locally in isolation and reproduce the exact same state without needing to run an entire preceding test suite.
