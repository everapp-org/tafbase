---
id: CONCEPT-python-v1-006-01-pytest-yield-fixture
status: accepted
subproject: python
layer: L2-language
since: pytest 3.0
standing: recommended
realizes: CONCEPT-prog-v1-006-01-scoped-test-fixture
requires: CONCEPT-python-v1-005-01-context-manager
---

# Pytest Yield Fixture

## Definition

A pytest yield fixture is a testing fixture function decorated with `@pytest.fixture` that yields a value or resource to the test. Code preceding the `yield` statement executes during test setup, while code following `yield` executes during test teardown. The teardown phase is guaranteed to run after the test function finishes, even if the test fails an assertion or raises an unexpected exception.

```python
import pytest
from pathlib import Path
import tempfile
import shutil
from typing import Generator

@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    path = Path(tempfile.mkdtemp(prefix="test_ws_"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)

def test_file_creation(temp_workspace: Path) -> None:
    target = temp_workspace / "demo.txt"
    target.write_text("sample content")
    assert target.exists()
```

## Why it exists

Traditional `unittest.TestCase` test suites decoupled setup (`setUp`) and teardown (`tearDown`) into disconnected class methods. This separation made it hard to track resource allocation, encouraged sharing mutable state across instance variables (`self.ws`), and caused teardown bugs if setup partially failed before initializing an instance attribute.

The yield fixture realizes `CONCEPT-prog-v1-006-01-scoped-test-fixture` using Python's context management protocol (`CONCEPT-python-v1-005-01-context-manager`):
1. **Colocated lifecycle:** Setup and teardown for a given resource reside within a single coherent generator function.
2. **Explicit parameter injection:** Tests declare dependencies as function parameters, eliminating hidden coupling and global variables.
3. **Flexible scoping:** Fixtures can be configured with scopes (`function`, `class`, `module`, `package`, `session`) and composed hierarchically.
