---
id: CONCEPT-taf-v1-006-01-the-browser-context
status: draft
subproject: taf
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# The browser context

## Definition

Playwright's unit of isolation: a `browser.new_context()` is an
independent session — own cookies, storage, cache — inside one browser.
Each test gets a fresh context, so one test's login or localStorage can
never leak into the next.

## Why it exists

The honest alternative is a fresh browser per test, which is slow, or a
shared browser, which leaks state and makes failures order-dependent.
A context is fast *and* isolated — test independence by construction,
which is what makes generated suites safe to run in any order or in
parallel later.

## In this repo

`generated/*/conftest.py` — the `page` fixture creates and closes a
context around every test.
