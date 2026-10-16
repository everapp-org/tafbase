---
id: CONCEPT-testing-v1-004-01-the-rerun
status: draft
subproject: testing
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The rerun

## Definition

A manifest of what failed, written at run end; the next run replays
only those. Cucumber's `rerun` plugin wrote `target/rerun.txt` and a
dedicated runner consumed it — red suite, fix, rerun the reds only.

## Why it exists

A suite of any size makes "run everything again" the expensive answer
to "did the fix work". The rerun manifest closes the fix→verify loop
in minutes instead of re-running the world. It also records what *did*
fail — the ledger a repair proves against (the full E-5 criterion:
fail → report → fix → repaired).

## In this project

Python already has it for free — pytest's `--lf`/`--last-failed`
reads its own cache. Lane L-12 makes it a *framework* feature: a
generated rerun manifest keyed on
[[CONCEPT-dsl-v1-009-01-the-test-id]] so Java gets the same replay and
a repair walk can rerun exactly the journey that failed.

## Touch it

```bash
.venv/bin/python -m pytest generated/python/ikc3-tracker --lf -q
```

## Neighbors

[[CONCEPT-testing-v1-002-01-the-failure-funnel]],
[[CONCEPT-taf-v1-005-01-the-preflight]].
