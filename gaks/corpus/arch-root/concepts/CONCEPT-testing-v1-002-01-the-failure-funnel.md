---
id: CONCEPT-testing-v1-002-01-the-failure-funnel
status: draft
subproject: testing
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The failure funnel

## Definition

One place every failure passes through — capture what the screen was
(DOM, screenshot, URL, which step), then fail. The old framework called
it `teststepFail`: every step def, every wait, funneled into the same
routine that grabbed the DOM, took the driver-appropriate screenshot,
and failed once.

## Why it exists

Scattered failure handling loses evidence — each `try` invents its own
half-broken capture. One funnel means one place to attach capture,
reporting, and debugging; a red test leaves *evidence*, not just a
stack. The companion idea — dead-session recovery — came from the same
scar: a driver that died mid-wait was re-acquired rather than
destroying the whole run.

## In this project

`pytest_runtest_makereport` in the generated `conftest.py` is the
funnel: a red call → URL + DOM captured (guarded against mid-navigation),
→ `ikc3_sink.file_report` → a tracker fault report. The capture half
(screenshot, console slice) is lane J-10/L-12; the recover half is
deferred (short tests rarely need it).

The **collect-and-flush stack** (harvest item 28) also lives here: a
`SoftChecks` collector per test — `soft` expects append
`{label, error}` instead of failing on the spot — and the fixture (or
Java `@AfterEach`) flushes once at test end, failing with *all* of
them. The old framework's `verificationErrors` + final `fail()` is the
ancestor; the `[M x / N y]` tally survives as the flush's count.

## Touch it

```bash
TAF_IKC3_WS=ws://127.0.0.1:4856/bus-ws TAF_BASE_URL=http://127.0.0.1:9 \
  .venv/bin/python -m pytest generated/python/ikc3-tracker -q
# a red test files a report — printed as 'fault report filed: <uuid>'
```

## Neighbors

[[CONCEPT-taf-v1-002-01-the-result-sink]],
[[CONCEPT-taf-v1-004-01-the-artifacts]],
[[CONCEPT-testing-v1-005-01-the-debug-run]].
