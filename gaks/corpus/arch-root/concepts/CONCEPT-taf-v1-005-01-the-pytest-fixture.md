---
id: CONCEPT-taf-v1-005-01-the-pytest-fixture
status: draft
subproject: taf
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# The pytest fixture

## Definition

A function pytest calls to *provide* something a test needs — a browser,
a page, a base URL — and to clean it up after. `yield` splits the two
halves: everything before it is setup, everything after is teardown that
runs even when the test fails.

```python
@pytest.fixture
def page(browser):
    pg = browser.new_page()   # setup
    yield pg                  # handed to the test
    pg.close()                # teardown, always
```

`scope=` says how often the fixture is made: `function` (every test —
the default), `class`, `module`, `session` (once for the whole run).

## Why it exists

Tests should not repeat their plumbing. Fixtures give each test a fresh,
named dependency — and the scope gives control over cost: a browser is
expensive (`session`), a clean page is cheap (`function`).

## In this repo

`generated/*/conftest.py` — the emitted suites get `base_url`, `browser`
and `page` fixtures for free.
