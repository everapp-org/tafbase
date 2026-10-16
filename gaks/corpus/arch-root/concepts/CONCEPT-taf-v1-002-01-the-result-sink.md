---
id: CONCEPT-taf-v1-002-01-the-result-sink
status: draft
subproject: taf
authored: 2026-10-15
authors:
  - George Petrov
  - Devin
---

# The result sink

## Definition

Where a finished test run sends what it found. A sink is a side channel:
the suite never waits on it, and a sink that cannot file warns instead of
failing the suite a second time. The first sink is the IKC3 tracker — a
red test dispatches `:support/file-report` over the bus's WebSocket, and
the tracker writes a `:fault-report` frame with its own page. Because the
manifest maps each test to its journey, the report names the model
element that failed, not only the test.

```python
rid = ikc3_sink.file_report(
    "ws://127.0.0.1:4856/bus-ws",
    "taf journey failed: board_to_tot — TimeoutError …",
    url=page.url, dom=page.content()[:50000])
```

## Why it exists

A suite that only turns red ends the loop in a log file. The sink closes
it: fail → report → ticket → fix → repaired is the quality loop the whole
platform demonstrates, and the tracker is both the SUT and the tracker.

## In this repo

`taf/sink_ikc3.py` — the wire protocol and `file_report`. Emitted
verbatim into every Python suite (`ikc3_sink.py`) and driven by the
`pytest_runtest_makereport` hook in `conftest.py` when `TAF_IKC3_WS` is
set. Verified live in `tests/test_live.py` (opt-in `TAF_LIVE=1`).
