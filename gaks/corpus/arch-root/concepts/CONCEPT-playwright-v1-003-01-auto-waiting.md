---
id: CONCEPT-playwright-v1-003-01-auto-waiting
status: draft
subproject: playwright
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# Auto-waiting assertions

## Definition

`expect(locator).to_be_visible()` does not check once — it retries until
the page catches up or the timeout fails the test. Playwright's locators
and assertions wait for the condition instead of racing the browser.

## Why it exists

The classic cause of flaky tests is the race between the test and the
app: `click()` before the button renders, `assert` before the page
settles. Explicit `sleep()` calls are how suites rot. Auto-waiting makes
the honest default also the fast one — the test proceeds the moment the
SUT is actually ready.

## In this repo

`generated/*/pages.py` — `expect_arrived()` is an auto-waiting marker
check; every state transition in a journey waits on the SUT's proof,
never on a timer.
