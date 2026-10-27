"""Tests of taf/runner.py — the cycle in one command, lane L-12.

Test IDs: T-run-001.. — check happens in the loader, emit lands in a
temp suite, the runner's exit code is the command's, --probe is the
first gate.
"""

import json
import os
import subprocess
import sys

from taf import emit_python, model, runner


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_MODEL = os.path.join(REPO, "suts", "ikc3-tracker.sut.model.json")


def tracker():
    return model.load(TRACKER_MODEL)


class Proc:
    def __init__(self, rc=0):
        self.returncode = rc


def fake_exec(seen, rc=0):
    def _run(cmd, cwd=None):
        seen["cmd"] = cmd
        return Proc(rc)
    return _run


# T-run-001 — emit to a temp suite, call pytest, exit code passes through
def test_run_emits_temp_and_invokes_pytest(tmp_path, monkeypatch, capsys):
    seen = {}

    def _run(cmd, cwd=None):
        seen["cmd"] = cmd
        seen["manifest"] = os.path.exists(
            os.path.join(cmd[-1], "taf.manifest.json"))
        return Proc(0)

    monkeypatch.setattr(runner, "_exec", _run)
    rc = runner.run(tracker(), extra=["-k", "board"])
    assert rc == 0
    cmd = seen["cmd"]
    assert cmd[:4] == [sys.executable, "-m", "pytest", "-q"]
    assert seen["manifest"]                    # emit happened before exec
    assert "-k" in cmd and "board" in cmd      # passthrough reached the runner
    assert not os.path.isdir(cmd[-1])          # temp suite is cleaned up
    assert "taf run — ikc3-tracker" in capsys.readouterr().out


# T-run-002 — the runner's red is the command's red
def test_runner_exit_code_passes_through(monkeypatch):
    monkeypatch.setattr(runner, "_exec", fake_exec({}, rc=3))
    assert runner.run(tracker()) == 3


# T-run-003 — --probe refuses before the runner is ever called
def test_probe_missing_refuses_to_run(tmp_path, monkeypatch, capsys):
    doc = {"sut": {"name": "x", "base-url": "http://127.0.0.1:1"},
           "states": {"a": {"marker": {"css": ".a"}}},
           "journeys": {"j": {"start": "a", "steps": []}}}
    p = tmp_path / "x.sut.model.json"
    p.write_text(json.dumps(doc))
    m = model.load(str(p))
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    assert runner.run(m, probe=True) == 1
    assert "cmd" not in seen                   # no browser ever opened
    assert "preflight missing" in capsys.readouterr().out


# T-run-004 — --suite runs the committed suite, no emit
def test_committed_suite_runs_in_place(tmp_path, monkeypatch):
    out = str(tmp_path / "suite")
    emit_python.emit(tracker(), out)
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    assert runner.run(tracker(), suite=out) == 0
    assert seen["cmd"][-1] == out
    assert os.path.isdir(out)                  # the suite stays


# T-run-005 — --keep keeps the temp suite for debugging
def test_keep_preserves_the_emitted_suite(monkeypatch):
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    runner.run(tracker(), keep=True)
    suite = seen["cmd"][-1]
    assert os.path.isdir(suite) and "test_journeys.py" in os.listdir(suite)
    import shutil
    shutil.rmtree(suite)


# T-run-006 — --lang java calls mvn, not pytest
def test_java_runs_mvn_test(monkeypatch):
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    runner.run(tracker(), lang="java")
    cmd = seen["cmd"]
    assert cmd[0] == "mvn" and "pom.xml" in cmd[-2] and cmd[-1] == "test"


# T-run-007 — the CLI splits at -- and forwards the runner args
def test_cli_forwards_passthrough(tmp_path):
    r = subprocess.run(
        [sys.executable, "-m", "taf", "run", TRACKER_MODEL, "--probe",
         "--", "--collect-only"],
        capture_output=True, text=True)
    # probe refuses first (no SUT up): the point is parse order held
    assert r.returncode == 1
    assert "preflight missing" in r.stdout
    r = subprocess.run(
        [sys.executable, "-m", "taf", "run", TRACKER_MODEL,
         "--", "--collect-only", "-q"],
        capture_output=True, text=True)
    assert "test_journeys.py: 2" in r.stdout
    assert r.returncode == 0
