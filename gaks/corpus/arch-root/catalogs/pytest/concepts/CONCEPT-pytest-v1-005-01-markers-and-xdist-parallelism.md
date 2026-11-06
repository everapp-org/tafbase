---
id: CONCEPT-pytest-v1-005-01-markers-and-xdist-parallelism
status: accepted
subproject: pytest
layer: L2-tool
since: pytest 8.0
standing: recommended
realizes: CONCEPT-istqb-v1-013-01-confirmation-vs-regression-testing, CONCEPT-prog-v1-007-01-parallel-fan-out
---

# Markers and xdist Worker Parallelism

## Definition

Pytest provides custom test metadata tagging via `@pytest.mark.<name>`, combined with multi-process parallel distribution via the `pytest-xdist` plugin:
- **Test Selection via Markers**: Tests are decorated with custom marks (such as `@pytest.mark.smoke`, `@pytest.mark.regression`, `@pytest.mark.integration`). The CLI `-m` switch filters tests using boolean expressions (e.g. `pytest -m "smoke and not slow"`).
- **Process Parallelism via xdist**: Invoking `pytest -n auto` spawns independent Python worker subprocesses equal to available CPU cores. Tests are distributed across workers, each maintaining an isolated Python runtime and memory space.

```python
import pytest

@pytest.mark.smoke
def test_login_flow(page):
    page.goto("https://app.example.com/login")
    assert page.is_visible("button#login-submit")

@pytest.mark.regression
@pytest.mark.slow
def test_end_to_end_order_fulfillment(page):
    page.goto("https://app.example.com/orders")
    # Multi-step checkout verification
    assert page.is_visible("div#order-history")
```

Execution commands:
```bash
pytest -m "smoke"          # Run only fast smoke tests on pull request commits
pytest -n 4 -m "regression" # Execute full test suite in parallel across 4 worker processes
```

## Why it exists

Realizes `CONCEPT-istqb-v1-013-01-confirmation-vs-regression-testing` and `CONCEPT-prog-v1-007-01-parallel-fan-out`. Running comprehensive regression suites sequentially on single threads leads to unacceptably long CI feedback cycles. 

Markers enable selective execution based on testing intent (confirmation checks on hotfixes versus full regressions on integration branches). `pytest-xdist` achieves linear wall-clock speedups by distributing test workloads across isolated OS processes, preventing shared-memory state cross-contamination between parallel workers.
