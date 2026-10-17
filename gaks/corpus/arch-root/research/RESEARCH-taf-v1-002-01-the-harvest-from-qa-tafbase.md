---
id: RESEARCH-taf-v1-002-01-the-harvest-from-qa-tafbase
status: draft
subproject: taf
authored: 2026-10-15
authors:
  - George Petrov
  - Devin
---

# The harvest from qa-tafbase

## What this is

A previous-generation framework — a Java/Selenium/Cucumber suite
(`tests_base` engine + per-product modules, JUnit4, Appium) — was mapped
end-to-end for reusable design. This document keeps the result and the
decisions it produced. The raw harvest — 28 ideas with evidence paths,
translations and costs — is
[[RESEARCH-taf-v1-003-01-the-harvest-in-detail]].

## The rules the harvest confirmed

- **Declared beats interpreted.** What the old runtime computed — device
  capability strings, tag→env mapping, layered properties — tafbase
  emits at codegen. The generator absorbs what a factory once computed.
- **Dwell is for observation, not synchronization.** `visibilitySleep`
  (a global + per-call-site `Thread.sleep` around every action) answered
  two needs at once: letting JS settle *and* letting a human watch.
  Auto-waiting markers own the first; a declared `dwell` owns the
  second. They must not fuse — sleeps-for-correctness is the disease
  this framework is built to avoid.

## Adopted (lanes in PLAN-taf-v1-001-01)

| idea | becomes | lane |
|---|---|---|
| `visibilitySleep` pacing | `dwell` — per-step/ms or a suite profile, emitted as a literal | H-8 |
| named wait vocabulary + soft/hard | `wait`/`check` step forms, `wait any (X\|Y)` | H-8 |
| version × language locator matrix | versioned elements, generated lookup tables | I-9 |
| screenshot grammar + approval loop | `compare screen` step, `TCID_run_res_step_{E,A,D}`, `taf promote` | J-10 |
| capability token (`Pixel9ProXL_chrome`) | `device:`/`env:` model header emitting the driver block | K-11 |
| column-model schema (its TSV interpreter) | stays as proof the grammar works — the tafbase DSL is its compile-time heir | (settled) |
| `rerun.txt` failed-only replay | `taf run --last-failed` manifest | L-12 |
| debug affordances | `--debug`: keep browser open, break on failure | L-12 |
| circuit breaker / preflight | `requires:` model clause → emitted preflight | L-12 |
| self-narrating actions | required human `label` on elements/steps → emitted logs | H-8 |
| the never-built `.srt` subtitles | narrated steps + timestamps → sidecar `.srt` beside run video | H-8 (with J-10 artifacts) |

The `.srt` item deserves a note: all five teardown paths of the old
framework captured a video-stop timestamp and called a
`createSubTitlesFile` that was only ever committed commented out — the
intent was a subtitle track mapping each narrated action line
(`Clicking 'X' on 'Y'`) onto video timecodes. The hard half —
timestamped narration — already existed. In generated code both halves
are cheap: emitted steps know their text and their clock, so a teardown
writer emits `results/<runId>/<test>.srt` beside the video. A run
becomes replayable *and* readable.

## Deliberately left behind

PPTX reports, Robot/AWT screen capture, hotkey-driven video, Swing
overlay strips, VM-awake mouse jiggles, X:-drive archiving, hardcoded
notification tokens. Playwright viewport capture + HTML reports +
committed artifacts replace the whole cluster.
