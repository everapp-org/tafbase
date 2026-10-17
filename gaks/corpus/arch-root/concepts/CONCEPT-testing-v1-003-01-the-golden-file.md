---
id: CONCEPT-testing-v1-003-01-the-golden-file
status: draft
subproject: testing
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The golden file

## Definition

An expected artifact — a baseline screenshot — that a `compare screen`
step diffs the actual against, plus the discipline around it: a
filename grammar (`TCID_run_res_step_{Expected,Actual,Diff}.PNG`),
tolerance and excluded regions per device, and *human approval*: a
person promotes `Actual` to `Expected` via a selection file, never by
auto-rebaselining.

## Why it exists

A picture asserts what fifty locators cannot. The old framework made
screenshots the *golden standard*, with `_ALT` baselines for legitimate
variants, exclusion masks for the iPhone notch, and a scanner that
rendered a report grouping diffs. The approval loop is the non-obvious
gem: goldens go stale because the SUT legitimately changed — a person
must bless the new truth, or the suite silently re-baselines its own
drift.

## In this project

The `{"compare-screen": "<name>"}` step emits Playwright's native
golden compare — `expect(page).to_have_screenshot` /
`assertThat(page).hasScreenshot()` — decided in ADR-taf-v1-003-01
(use the library's diff engine, keep our artifact layout). Promote
with `pytest --update-snapshots` (Python) /
`mvn test -DupdateSnapshots` (Java) — the approval loop's first form;
the selection-file promote of the old grammar is the richer later
shape.

## Touch it

```bash
.venv/bin/python -m pytest generated/python/ikc3-tracker --update-snapshots
```

## Neighbors

[[CONCEPT-dsl-v1-008-01-the-image-step]],
[[CONCEPT-taf-v1-006-01-the-subtitle-track]] (the step's caption is the
same step's name).
