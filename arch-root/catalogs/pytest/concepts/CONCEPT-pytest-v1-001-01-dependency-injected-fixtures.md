---
id: CONCEPT-pytest-v1-001-01-dependency-injected-fixtures
status: accepted
subproject: pytest
layer: L2-tool
since: pytest 8.0
standing: recommended
realizes: CONCEPT-prog-v1-006-01-scoped-test-fixture, CONCEPT-qa-v1-004-01-session-and-context-isolation
contrasts-with: CONCEPT-junit-v1-001-01-per-method-test-instance-lifecycle, CONCEPT-pwtest-v1-001-01-test-extend-fixtures
---

# Dependency-Injected Fixtures and Scoped Lifecycles

## Definition

Pytest fixtures are modular, composable dependency injection providers declared via `@pytest.fixture`. Test functions and higher-level fixtures request dependencies explicitly by listing fixture names as function arguments.

Fixtures support distinct lifecycle scopes:
- `function` (default): Created and torn down for each individual test function.
- `class`: Shared across methods in a test class.
- `module`: Created once per test file.
- `package`: Shared across tests within a subpackage directory.
- `session`: Created once per entire test invocation.

Teardown logic is expressed using Python generators: code prior to `yield` runs during setup, the yielded value is injected into the test, and code following `yield` executes during teardown even if test execution raises an exception.

```python
import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

@pytest.fixture(scope="session")
def browser():
    """Heavyweight browser launched once per test run."""
    with sync_playwright() as p:
        browser_instance = p.chromium.launch()
        yield browser_instance
        browser_instance.close()

@pytest.fixture(scope="function")
def page(browser: Browser) -> Page:
    """Lightweight isolated context and page per test function."""
    context: BrowserContext = browser.new_context()
    page_instance: Page = context.new_page()
    yield page_instance
    context.close()

def test_user_dashboard(page: Page):
    page.goto("https://app.example.com/dashboard")
    assert page.is_visible("header#dashboard-header")
```

## Why it exists

Realizes `CONCEPT-prog-v1-006-01-scoped-test-fixture` and `CONCEPT-qa-v1-004-01-session-and-context-isolation`. Reusable test state requires granular lifecycle control without tight coupling or rigid class inheritance trees.

Contrasts with `CONCEPT-junit-v1-001-01-per-method-test-instance-lifecycle` and `CONCEPT-pwtest-v1-001-01-test-extend-fixtures`. JUnit relies on class inheritance and `@BeforeEach`/`@AfterEach` annotations that bind state to class fields. Pytest uses functional dependency injection with automatic resolution of directed acyclic graph (DAG) fixture dependencies, automatic caching per scope, and centralized discovery via `conftest.py`. Playwright Test adopts a similar philosophy in TypeScript via `test.extend()`.
