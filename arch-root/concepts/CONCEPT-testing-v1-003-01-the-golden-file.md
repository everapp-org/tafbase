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

Planned — lane J-10. The
[[CONCEPT-dsl-v1-009-01-the-test-id]] and
[[CONCEPT-taf-v1-004-01-the-artifacts]] layout land first, because the
filename grammar needs both.

## Touch it

Not yet — the nearest live analogue is the marker assertion in every
state (`expect_arrived`).

## Neighbors

[[CONCEPT-dsl-v1-008-01-the-image-step]],
[[CONCEPT-taf-v1-006-01-the-subtitle-track]] (the step's caption is the
same step's name).
