---
id: CONCEPT-dsl-v1-004-01-the-wait
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The wait

## Definition

Step forms that say *how long to look*. Implemented today:
`{"wait-for": {"element": x}}` or `{"state": y}` — an auto-waiting
assertion that must hold. Planned (lane H-8): `{"check": ...}`, the
soft twin that collects a failure and continues, and `{"wait-any":
[...]}` for UIs with alternating states.

## Why it exists

Most flakiness is timing that was never declared. A junior reaches for
`sleep`; a named wait says the intent — *hold hard until the marker
appears* versus *log and continue*. The old framework kept the whole
vocabulary: `waitUntilVisibilityOfElement`, `waitInvisibilityOfElement`,
`waitUntilVisibilityOfEitherElements`, with soft variants that logged,
saved DOM and screenshot, and went on. Hard fails the step; soft
records it. A suite needs both — "the SUT must be here" and "the SUT
might offer this".

## In this project

`wait-for` is a step form in `taf/model.py` and both emitters (state →
`expect_arrived`, element → `to_be_visible`). `check` and `wait-any`
are lane H-8, drafted in `PLAN-taf-v1-001-01`.

## Touch it

Add `{"wait-for": {"state": "tot"}}` to a `do` list and run
`python -m taf check` — the loader validates it like any step.

## Neighbors

[[CONCEPT-playwright-v1-003-01-auto-waiting]] (the mechanism),
[[CONCEPT-dsl-v1-003-01-the-dwell]] (observation, not correctness).
