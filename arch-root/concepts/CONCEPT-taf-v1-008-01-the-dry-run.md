---
id: CONCEPT-taf-v1-008-01-the-dry-run
status: draft
subproject: taf
authored: 2026-10-27
authors:
  - George Petrov
  - Devin
---

# The dry run

## Definition

`taf dry-run` reports a run without executing one. It prints three
things: the tests a run would execute (the manifest's truth), the
`TAF_*` contract as this shell sets it, and findings — `missing`,
`off`, `note`, `ok`. Video unset is `off`: the run leaves no
recording. A `compare-screen` step with no golden file is `missing`:
the run fails on it. `--suite <dir>` adds the emitted suite to the
check — a stale manifest names itself. `--probe` touches the network:
the SUT answers or it does not.

## Why it exists

A run that fails for a reason a person could have read beforehand
spends a test cycle on a fact. The model loader's rule — report every
reason, never die on the first — applies to a run's context too. The
dry run is the report form of that rule; `requires:` (the preflight,
[[CONCEPT-taf-v1-005-01-the-preflight]]) is the gate form. A report
says "video is off"; a gate refuses to start.

## In this project

`taf/dryrun.py` builds the report; `taf/__main__.py` wires the
subcommand. Exit code is 0 always — the person decides, not the tool.
Opt-in variables (`TAF_VIDEO`, `TAF_IKC3_WS`, `TAF_DEBUG`) report
`off` when unset, not `missing` — an opt-in feature is not a defect.
What the model *needs* reports `missing`: goldens, a stale suite, an
unreachable SUT under `--probe`.

## Touch it

```bash
.venv/bin/python -m taf dry-run suts/ikc3-tracker.sut.model.json
.venv/bin/python -m taf dry-run suts/ikc3-tracker.sut.model.json \
    --suite generated/python/ikc3-tracker --probe
.venv/bin/python -m taf dry-run suts/ikc3-tracker.sut.model.json --json
```

## Neighbors

[[CONCEPT-taf-v1-005-01-the-preflight]],
[[CONCEPT-taf-v1-003-01-the-environment]],
[[CONCEPT-taf-v1-004-01-the-artifacts]]
