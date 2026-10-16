---
id: CONCEPT-pom-v1-001-01-the-page-object
status: draft
subproject: pom
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# The page object

## Definition

A class that *is* a page or state of the SUT: it holds the page's
locators and its meaningful operations, so tests say
`board.expect_arrived()` instead of repeating selectors.

```python
class BoardPage:
    def __init__(self, page):
        self.marker = page.locator(".ikc-dock-theme")

    def expect_arrived(self):
        expect(self.marker).to_be_visible()
```

## Why it exists

Locators are the most-fragile line in a suite. When they live in one
class per state, a UI change is a one-place fix — and tests read as
intent ("arrive at the board"), not mechanics. In tafbase the pattern is
stricter: a page object's `marker` is the *proof of arrival* the model
declares, so the class also knows when its page is real.

## In this repo

`generated/*/pages.py` — one class per declared state, generated from
`states` in the model (SPEC-taf-v1-001-04).
