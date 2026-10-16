---
id: CONCEPT-dsl-v1-007-01-the-step-language
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The step language

## Definition

The closed verb vocabulary inside `do:` and `steps:` — act (`click`,
`fill`, `check`, `select`), move (`navigate`), observe (`wait-for`,
`expect`), call the API (`api`, `save`), pace (`dwell`). A step is one
key with its argument; anything else is refused, named.

## Why it exists

A small closed vocabulary is a grammar a person learns in one sitting —
and it is not new. The old framework's TSV interpreter ran the same
shape as columns: step, action, field name, label, value, screenshot
control, locale overrides, ticket. It was field-proven on juniors;
generating code from the same grammar is its compile-time heir — what
was a runtime interpreter becomes emitted statements a reader can step
through.

Planned siblings from the same harvest: `maybe` (the `ifPresent*`
idiom — click only if present, never fail), `check`/`wait-any` (see
[[CONCEPT-dsl-v1-004-01-the-wait]]), `click-image` (see
[[CONCEPT-dsl-v1-008-01-the-image-step]]).

## In this project

`STEP_FORMS` in `taf/model.py` is the whole grammar; SPEC-taf-v1-001-04
TAF-3 is the contract; each form renders in both emitters — parity is
asserted by `tests/test_parity.py`.

## Touch it

```bash
.venv/bin/python -m taf check suts/ikc3-tracker.sut.model.json
```

## Neighbors

[[CONCEPT-dsl-v1-001-01-the-sut-model]],
[[CONCEPT-dsl-v1-003-01-the-dwell]].
