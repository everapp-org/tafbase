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
