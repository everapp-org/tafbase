---
id: CONCEPT-dsl-v1-012-01-the-target
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The target

## Definition

`device:` and `env:` header clauses — `Pixel9ProXL_chrome`, `qa`,
`uat` — resolved at *emit time* into the capabilities block and base
URL the suite launches with. One token, everything derived.

## Why it exists

The old framework parsed a resolution string at runtime —
`w10_chrome`, `GalaxyS25Ultra_samsung`, `iPhone16Pro_safari` — through
~300 lines of factory dispatching on OS, browser, device, local CDP
emulation or BrowserStack. It was already a mini-DSL with a runtime
interpreter. Generated code does better: the vocabulary is validated
at emit time, the emitted suite carries the exact capabilities object,
and the tag-to-environment mapping (`@qa_env` -> suite + URL + locator
version) bakes in the same way. The layered property files it replaced
— root defaults, module config, user overrides — become inputs to
codegen, resolved once and printed into the suite header.

## In this project

Planned — lane K-11. Today the only retarget is `TAF_BASE_URL`
([[CONCEPT-taf-v1-003-01-the-environment]]).

## Touch it

Not yet runnable — see lane K-11 in `PLAN-taf-v1-001-01`.

## Neighbors

[[CONCEPT-dsl-v1-005-01-the-versioned-locator]] — target version picks
locator variants; [[CONCEPT-taf-v1-003-01-the-environment]].
