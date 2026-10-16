---
id: CONCEPT-testing-v1-006-01-the-living-spec
status: draft
subproject: testing
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The living spec

## Definition

A specification whose examples *execute* — the old framework's
Concordion fixtures returned display strings from action methods so the
rendered spec embedded the actual outcome beside the expected one; its
StoryboardExtension drew a per-step screenshot strip inside the spec
document.

## Why it exists

A spec that runs cannot drift silently — the document is the test, so
an outdated claim *is* a red test. It's the same instinct as our
release-note-first discipline (write the note before the work) taken
one step further: the document doesn't just precede the work, it
proves it on every run.

## In this project

Deferred — the nearest live practice is the release-note-as-acceptance
in `PLAN-taf-v1-001-01` and `taf.manifest.json` as traceability.
A living-spec emitter would render a document whose expected/actual
cells fill at run time; it belongs with J-10's report work.

## Touch it

Read the manifest: `generated/python/ikc3-tracker/taf.manifest.json`
is the machine-readable ancestor of the idea — declared vs run.

## Neighbors

[[CONCEPT-testing-v1-001-01-arrange-act-assert]],
[[CONCEPT-testing-v1-003-01-the-golden-file]].
