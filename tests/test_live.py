"""T-taf-004 — E-5 acceptance: the generated suite runs against a live SUT.

Opt-in: skips unless TAF_LIVE=1 and TAF_BASE_URL points at a running system.
The ikc3-tracker model targets a probe bus:

    cd <an ikc3 detached worktree> && devbox run probe-bus   # serves :4856
    TAF_LIVE=1 .venv/bin/python -m pytest tests/test_live.py -v

Requires playwright installed in the running interpreter.
"""
import os
import subprocess
import sys

import pytest

from taf import emit_python, model

MODEL = "suts/ikc3-tracker.sut.model.json"


@pytest.mark.skipif(not os.environ.get("TAF_LIVE"), reason="live run — set TAF_LIVE=1")
def test_generated_suite_runs_against_live_sut(tmp_path):
    m = model.load(MODEL)
    outdir = str(tmp_path / "suite")
    emit_python.emit(m, outdir)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", outdir],
        env={**os.environ, "TAF_BASE_URL": os.environ.get("TAF_BASE_URL", m["sut"]["base-url"])},
        capture_output=True, text=True, timeout=300,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "passed" in r.stdout


@pytest.mark.skipif(not os.environ.get("TAF_LIVE"), reason="live run — set TAF_LIVE=1")
def test_sink_files_a_fault_report():
    """T-taf-005 (first half): the sink dispatches :support/file-report and
    the bus answers with a real report id."""
    import re
    from taf import sink_ikc3

    ws = os.environ.get("TAF_IKC3_WS", "ws://127.0.0.1:4856/bus-ws")
    rid = sink_ikc3.file_report(
        ws, "tafbase T-taf-005 live probe — expect a fault report",
        url="tafbase://test", island="board")
    assert re.fullmatch(r"[0-9a-f-]{36}", rid), rid


@pytest.mark.skipif(not os.environ.get("TAF_LIVE"), reason="live run — set TAF_LIVE=1")
def test_red_suite_files_reports(tmp_path):
    """A suite pointed at a dead SUT goes red, and every red test files a
    fault report — fail → file is the loop's first half."""
    m = model.load(MODEL)
    outdir = str(tmp_path / "suite")
    emit_python.emit(m, outdir)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-s", outdir],
        env={**os.environ,
             "TAF_BASE_URL": "http://127.0.0.1:1",  # nothing listens there
             "TAF_IKC3_WS": os.environ.get("TAF_IKC3_WS", "ws://127.0.0.1:4856/bus-ws")},
        capture_output=True, text=True, timeout=300,
    )
    assert r.returncode != 0                      # the suite really went red
    assert "fault report filed:" in r.stdout      # and the loop filed it


@pytest.mark.skipif(not os.environ.get("TAF_LIVE"), reason="live run — set TAF_LIVE=1")
def test_java_suite_runs_against_live_sut(tmp_path):
    """The Java emitter's output is real: mvn test, green, live SUT.
    Verified 2026-10-15: 2 tests, 0 failures, probe bus :4856."""
    import shutil
    from taf import emit_java

    if not shutil.which("mvn"):
        pytest.skip("no maven")
    m = model.load(MODEL)
    outdir = str(tmp_path / "java-suite")
    emit_java.emit(m, outdir)
    r = subprocess.run(
        ["mvn", "-q", "test"], cwd=outdir,
        env={**os.environ, "TAF_BASE_URL": os.environ.get("TAF_BASE_URL", m["sut"]["base-url"])},
        capture_output=True, text=True, timeout=600,
    )
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]
