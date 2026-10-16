---
id: CONCEPT-testing-v1-005-01-the-debug-run
status: draft
subproject: testing
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The debug run

## Definition

A mode where a failing test *stays*: `breakpoint()` / `PWDEBUG` lands
at the failing step, the browser is not torn down, and the runner lets
you poke the live page. The old framework had `breakPoint()` (an empty
method to hang an IDE breakpoint on), `testIsUnderTest` and
`keepBrowserOpen` — all the affordances for interrogating a failure
instead of reading it.

## Why it exists

A failure you can inspect beats a failure you read. Most flaky-bug
hunting is not "does it fail" but "what did it look like the moment it
did" — and that question is only answerable if the run doesn't close
the window on the way out.

## In this project

Lane L-12 — `--debug` keeps the browser open and breaks on failure.
Today: `PWDEBUG=1` opens Playwright's inspector, `TAF_HEADLESS` unset +
`TAF_SLOWMO` makes the run watchable, and
[[CONCEPT-dsl-v1-003-01-the-dwell]] holds a step long enough to see.

## Touch it

```bash
PWDEBUG=1 .venv/bin/python -m pytest generated/python/ikc3-tracker -q
```

## Neighbors

[[CONCEPT-testing-v1-002-01-the-failure-funnel]],
[[CONCEPT-taf-v1-003-01-the-environment]].
