---
id: CONCEPT-taf-v1-003-01-the-locator-ladder
status: draft
subproject: taf
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# The locator ladder

## Definition

The ordered preference for how a test finds a UI element:

1. `role` + `name` — what the element *is* to a user (button "Save")
2. `label` / `text` / `placeholder` — what it *says*
3. `testid` (`data-testid`) — a deliberate marker the SUT provides
4. `css` / `xpath` — how it happens to be built; last resort, flagged
   `fragile`

## Why it exists

Tests that find elements by structure break when structure changes; tests
that find them by meaning break only when meaning changes. The ladder is
Playwright's own guidance made mechanical: in `sut.model.json` a locator
declares one of the rungs and `:bad-locator` refuses anything else, so
the preference is enforced by the model, not by habit.

## In this repo

SPEC-taf-v1-001-01, `elements` clause. The emitters translate each rung
to the platform's locator API (`get_by_role` → `getByRole`).
