---
id: CONCEPT-dsl-v1-011-01-the-locale
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The locale

## Definition

A language dimension on the model's data and locators — one data table
per language (`table[lang][key]`), locator variants per locale, and the
occasional behavioral flip (the old framework's Arabic runs reversed
slider direction).

## Why it exists

A localized SUT is not one SUT — "Log in" and "Ingresar" are different
locators for the same element. The old framework ran 18 languages off
xlsx columns and `transLabel`/`transValue` row overrides; without the
dimension declared, localization testing means a second, drifting copy
of the model.

## In this project

Deferred — pairs naturally with
[[CONCEPT-dsl-v1-005-01-the-versioned-locator]], whose matrix is
(version x language). It lands when a second-language SUT model needs
it; until then the model's `elements`/`data` are single-locale.

## Touch it

Not implemented — see RESEARCH-taf-v1-002-01, items 5 and 25.

## Neighbors

[[CONCEPT-dsl-v1-005-01-the-versioned-locator]],
[[CONCEPT-dsl-v1-012-01-the-target]].
