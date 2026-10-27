---
id: CONCEPT-taf-v1-005-01-the-preflight
status: draft
subproject: taf
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The preflight

## Definition

A declared gate before a run — `requires:` in the model (`mail-server
up`, `appium listening`) — checked once, failing the whole suite fast
and saying *why*. Its runtime form is the circuit breaker: the old
framework's `suiteStopReason` flag that, once set (the mail server
died), failed every subsequent test immediately rather than logging 40
identical red herrings.

## Why it exists

Forty tests all failing "connection refused" is noise that costs an
hour of triage before anyone asks whether the server was even up.
Refusing early — with a named reason — is the same honesty the model
loader applies statically, applied to a run's prerequisites. A suite
that knows its requirements stops spending test failures on
infrastructure facts.

## In this project

Partly landed — lane L-12. The static analogue exists: `taf check`'s
refusals list every reason instead of dying on the first. The report
form exists: `taf dry-run` names what a run lacks
([[CONCEPT-taf-v1-008-01-the-dry-run]]). Still planned: `requires:` —
the gate form, the run-time version of the same contract.

## Touch it

```bash
.venv/bin/python -m taf check suts/ikc3-tracker.sut.model.json
# refusals — the static form of the same idea
.venv/bin/python -m taf dry-run suts/ikc3-tracker.sut.model.json
# findings — the report form
```

## Neighbors

[[CONCEPT-taf-v1-008-01-the-dry-run]],
[[CONCEPT-taf-v1-002-01-the-result-sink]],
[[CONCEPT-testing-v1-004-01-the-rerun]] — a preflight failure shouldn't
file 40 reports, it should file one.
