---
id: CONCEPT-dsl-v1-013-01-the-absorption-loop
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The absorption loop

## Definition

The loop that grows the DSL: the language cannot say it → a test is
authored by hand in `custom/` → the manual pattern recurs or
stabilizes → a model clause learns to say it (loader + both emitters +
spec + a named refusal) → regenerate, and generated code replaces the
manual code. `custom/` trends back toward empty.

## Why it exists

A fixed vocabulary eventually fails — the SUT does something the step
language never imagined. Two bad answers exist: freeze (the DSL rots)
or grow `custom/` forever (the DSL becomes a suggestion and the
manifest stops describing the suite). The loop is the third: hand-code
is *scaffolding*, the model *absorbs* it, and the language is the
residue of everything that ever needed saying twice. The old framework
ran the same metabolism informally — `waitUntilVisibilityOfEitherElements`
and the `ifPresent*` idioms were born as hand-rolled helpers that
recurred until they earned a name. Here it is deliberate: `wait-any`,
`maybe`, `soft expect`, `dwell` are the loop already running, fed by
the harvest rather than by custom code.

## In this project

`custom/` is the seam (planned — the emitter never writes there, the
manifest can mark `source: hand`). A growing `custom/` is the DSL
reporting which clause is missing — a diagnostic, not a failure.

## Touch it

The newest clauses are the proof:

```bash
grep -E 'wait-any|maybe|soft|dwell' suts/ikc3-tracker.sut.model.json
```

## Neighbors

[[CONCEPT-dsl-v1-007-01-the-step-language]] — the vocabulary the loop
grows; [[CONCEPT-taf-v1-007-01-the-three-levels]] — `custom/` is where
Use reaches back toward Model.
