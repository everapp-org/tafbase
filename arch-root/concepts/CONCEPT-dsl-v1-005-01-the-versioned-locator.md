---
id: CONCEPT-dsl-v1-005-01-the-versioned-locator
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The versioned locator

## Definition

One element, several declarations, keyed by the SUT's version (and,
where needed, language): the locator that fits is chosen by *nearest
declared version at or below the target*, with a plain fallback.

## Why it exists

Suites rot fastest at locators, and an app's UI differs between
releases. The old framework's `VersionedLocator` was a version x
language matrix — `addLocator(515, SPANISH, "xpath", ...)` — resolved
by `getBestGuessLocator`: largest version <= requested, English
fallback. It decoupled the suite from app-version churn; a suite could
run QA build 480 and UAT build 515 from one declaration.

## In this project

Planned — lane I-9. Today's `elements` map one name to one rung of
[[CONCEPT-playwright-v1-001-01-the-locator-ladder]]; the versioned form
adds variants (`v515+`, `es`) that the emitter resolves at codegen —
the lookup table becomes generated data, or per-version generated
suites, not a runtime map.

## Touch it

Not yet runnable — see lane I-9 in `PLAN-taf-v1-001-01`.

## Neighbors

[[CONCEPT-dsl-v1-011-01-the-locale]] (the language dimension);
[[CONCEPT-dsl-v1-012-01-the-target]] (which version a run aims at).
