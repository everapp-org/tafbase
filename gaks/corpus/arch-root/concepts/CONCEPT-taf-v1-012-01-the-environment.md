---
id: CONCEPT-taf-v1-012-01-the-environment
status: draft
subproject: taf
authored: 2026-10-15
authors:
  - George Petrov
  - Devin
---

# The environment

## Definition

Two different things share this word, and the project uses both.

**The virtual environment** — `.venv/`, an isolated copy of Python with
its own installed packages. `pytest`, `playwright`, and
`websocket-client` live there, so `python3 -m venv .venv` reproduces the
toolchain on any machine without touching the system Python. Commands in
this repo always name `.venv/bin/python` explicitly.

**Environment variables** — `os.environ`, the per-process settings the
operating system hands a program. Generated suites read `TAF_*` variables
at runtime:

| variable        | read by                  | meaning                                    |
|-----------------|--------------------------|--------------------------------------------|
| `TAF_BASE_URL`  | `conftest.py` (both langs) | where the SUT lives — probe, staging, prod |
| `TAF_IKC3_WS`   | `pytest_runtest_makereport` | when set, a red test files a fault report |
| `TAF_LIVE`      | `tests/test_live.py`     | opt the live acceptance tests in           |

## Why it exists

Generated code is immutable — you edit the model and regenerate, never
the output. But where the SUT runs *changes* run to run. The environment
is the seam for run-to-run variation: the same committed suite tests a
probe bus, a staging box, or production by setting a variable, not by
editing code. Configuration outside the artifact is a classic test
framework practice (the old Selenium demo externalized the same thing
into a config file; environment variables are the twelve-factor form).

## In this repo

`.venv/` is created in the README's "Hacking on it" section. `TAF_BASE_URL`
appears in `taf/emit_python.py`, `taf/emit_java.py`, and every generated
`conftest.py`/`BaseTest.java`. `TAF_IKC3_WS` drives
[CONCEPT-taf-v1-010-01-the-result-sink](CONCEPT-taf-v1-010-01-the-result-sink.md).
