---
id: CONCEPT-taf-v1-003-01-the-environment
status: draft
subproject: taf
authored: 2026-10-15
authors:
  - George Petrov
  - Devin
---

# The environment contract

## Definition

Every process inherits a set of text key=value pairs from the program
that started it — its **environment**. The shell exports them; the
program reads them. This page is the framework's *contract* over that
OS mechanism: the `TAF_*` variables every generated suite honors, in
every language. Python reads them through `os.environ`:

```python
os.environ.get("TAF_BASE_URL", "http://127.0.0.1:4856")  # value, or a default
os.environ.get("TAF_IKC3_WS")                            # value, or None
```

Java reads the same table through `System.getenv()`. One mechanism, two
spellings — one contract, which is why a `java` page on environment
variables does not exist: the variable means the same thing whoever
reads it. A variable set for one command applies to that run only:

```bash
TAF_SLOWMO=800 .venv/bin/python -m pytest generated/python/ikc3-tracker -q
```

*(Not this word's other meaning: the **virtual environment** is a
different thing — [[CONCEPT-python-v1-002-01-the-virtual-environment]].)*

## Why it exists

Generated code is immutable — you edit the model and regenerate, never
the output. But where the SUT runs *changes* run to run. The environment
is the seam where run-to-run variation belongs: the same committed suite
tests a probe bus, a staging box, or production by setting a variable,
not by editing code. The previous-generation framework externalized the
same seam into `config.properties` files; environment variables are the
twelve-factor form of the same idea.

## In this project

| variable       | read by                     | meaning                                     |
|----------------|-----------------------------|---------------------------------------------|
| `TAF_BASE_URL` | `conftest.py`, `BaseTest`   | where the SUT lives — probe, staging, prod  |
| `TAF_IKC3_WS`  | `pytest_runtest_makereport` | when set, a red test files a fault report   |
| `TAF_HEADLESS` | `conftest.py`, `BaseTest`   | `1` for CI; headed is the default           |
| `TAF_SLOWMO`   | `conftest.py`, `BaseTest`   | ms between Playwright actions               |
| `TAF_LIVE`     | `tests/test_live.py`        | opts the live acceptance tests in           |

`TAF_BASE_URL` appears in `taf/emit_python.py`, `taf/emit_java.py`, and
every emitted `conftest.py`/`BaseTest.java`. `TAF_IKC3_WS` drives
[[CONCEPT-taf-v1-002-01-the-result-sink]].

## Touch it

```bash
env | grep TAF                    # what is set right now — usually nothing
TAF_BASE_URL=http://x .venv/bin/python -m taf check suts/ikc3-tracker.sut.model.json
```

## Neighbors

The virtual environment (above); the result sink the `TAF_IKC3_WS`
variable enables; [[CONCEPT-taf-v1-001-01-the-learning-path]].
