---
id: CONCEPT-dsl-v1-009-01-the-test-id
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The test id

## Definition

A short, stable identifier a test carries — the old framework's
`ASM011`, extracted from the scenario name to drive golden filenames,
result folders, and report groups.

## Why it exists

Names are prose; ids are handles. Every artifact a run leaves —
`ASM011_run42_desktop_step3_Expected.PNG`, a rerun manifest entry, a
fault report's subject — joins on the id. Parsing it out of a name was
the workaround; declaring it (`test ASM011 "..."`) makes it a
first-class token the model owns and the manifest exports.

## In this project

Planned — today the journey name is the de facto id
(`taf.manifest.json` keys on it). Declared test ids arrive with the
artifact grammar of lane J-10 and the rerun manifest of lane L-12.

## Touch it

Read `generated/python/ikc3-tracker/taf.manifest.json` — the `test`
fields are the ids a declared token will replace.

## Neighbors

[[CONCEPT-testing-v1-003-01-the-golden-file]],
[[CONCEPT-taf-v1-004-01-the-artifacts]],
[[CONCEPT-testing-v1-004-01-the-rerun]].
