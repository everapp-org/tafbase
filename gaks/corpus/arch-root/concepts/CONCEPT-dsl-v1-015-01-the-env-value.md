---
id: CONCEPT-dsl-v1-015-01-the-env-value
status: draft
subproject: dsl
authored: 2026-10-27
authors:
  - George Petrov
  - Devin
---

# The env: value

## Definition

A `fill` value of the form `env:NAME` is a need, not a literal: the
emitted code reads the variable `NAME` at run time. The model carries
the name; the environment carries the value. Python spells it
`os.environ["NAME"]`, Java
`Objects.requireNonNull(System.getenv("NAME"), …)` — same clause,
each language's own reading.

```json
{"fill": {"element": "secret", "value": "env:TAF_SUT_SECRET"}}
```

## Why it exists

A credential in a model is a credential in the repository — the model
is committed, diffed, and emitted twice. `env:` is how the model
declares *that* a run needs a value without holding *what* it is.
`taf model.env_needs` collects every need, so `taf dry-run` reports an
unset one as `missing`, `taf run` refuses on it before a browser
opens, and `taf env` prints it as a fill-in line — the need surfaces
everywhere a run is prepared, while the secret stays in the shell.

## In this project

`model.env_needs(m)` in `taf/model.py` is the single scan the
emitters, the dry run, and the gate all use — one definition of
"needed", many readers. The tracker's sign-in uses it:
`suts/ikc3-tracker.sut.model.json` fills `handle` and `secret` from
`env:TAF_SUT_HANDLE` / `env:TAF_SUT_SECRET`.

## Touch it

```bash
export TAF_SUT_HANDLE=ada TAF_SUT_SECRET=…
taf suts/ikc3-tracker.sut.model.json          # env needs → ok
taf env suts/ikc3-tracker.sut.model.json      # needs → fill-in lines
```

## Neighbors

[[CONCEPT-taf-v1-003-01-the-environment]] — the contract the value
travels in. [[CONCEPT-dsl-v1-014-01-the-two-inputs]] — env: is a third
voice in the same choir: neither declared data nor derived, but
needed. [[CONCEPT-taf-v1-005-01-the-preflight]] — a need unset is a
gate's first finding.
