---
id: CONCEPT-dsl-v1-003-01-the-dwell
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The dwell

## Definition

A `{"dwell": <ms>}` step — a declared pause, emitted as a literal
`page.wait_for_timeout(800)` / `page.waitForTimeout(800)` at exactly the
step where a watching human needs the screen to hold still.

## Why it exists

Automation that nobody can watch cannot teach. The old framework's
`visibilitySleep` answered two needs with one sleep: letting the page
settle *and* letting the eye follow. tafbase separates them —
correctness belongs to markers and [[CONCEPT-playwright-v1-003-01-auto-waiting]];
observation belongs to dwell. Keeping them apart is the whole point:
a sleep that papers over a timing bug is a lie the suite tells later.

## In this project

`dwell` is a validated step form (`taf/model.py`, `bad-dwell` refusal);
both emitters render it; the tracker model pauses 800 ms inside
`open-tot` so a watcher sees the `tot` island land. Suite-wide pacing
is the environment's job — `TAF_SLOWMO` in
[[CONCEPT-taf-v1-003-01-the-environment]].

## Touch it

```bash
.venv/bin/python -m pytest generated/python/ikc3-tracker -q   # watch the pause
```

## Neighbors

`wait-for` in [[CONCEPT-dsl-v1-004-01-the-wait]]; narration in
[[CONCEPT-dsl-v1-006-01-the-label]].
