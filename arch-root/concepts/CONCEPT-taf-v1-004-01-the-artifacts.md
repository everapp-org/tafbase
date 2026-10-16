---
id: CONCEPT-taf-v1-004-01-the-artifacts
status: draft
subproject: taf
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The artifacts

## Definition

Everything a run leaves behind, under a stable layout —
`results/<date>/<runId>/<testId>/` carrying the video, the `.srt`
subtitle sidecar, the DOM and screenshot on failure, the log slice.
The old framework's `CiTestsRunner` established the contract: dated
folders, `suiteName.txt`/`publicURL.txt` sidecars the report generator
consumed.

## Why it exists

Evidence outlives the run. A suite without artifacts answers only
"did it pass"; with them it answers "what happened" — the difference
between a test framework and a test *observatory*. The layout being
declared and stable is what lets separate tooling (the HTML matrix
report, a fault report, a human browsing) read it without asking the
runner anything.

## In this project

Today: the IKC3 sink ships DOM+URL into a fault report
([[CONCEPT-taf-v1-002-01-the-result-sink]]); pytest's own `.pytest_cache`
holds the rerun ledger. The `results/<runId>/` layout, video, and the
golden-file naming grammar are lanes J-10 and L-12.

## Touch it

```bash
ls generated/python/ikc3-tracker/.pytest_cache/v/cache/lastfailed 2>/dev/null
```

## Neighbors

[[CONCEPT-testing-v1-003-01-the-golden-file]],
[[CONCEPT-taf-v1-006-01-the-subtitle-track]],
[[CONCEPT-testing-v1-004-01-the-rerun]].
