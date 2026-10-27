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

# The tracker model needs env: credentials — the gate refuses without them.
NEEDS = {"TAF_SUT_HANDLE": "ada", "TAF_SUT_SECRET": "s3cret"}


def tracker():
    return model.load(TRACKER_MODEL)


class Proc:
    def __init__(self, rc=0):
        self.returncode = rc


def fake_exec(seen, rc=0):
    def _run(cmd, cwd=None, env=None):
        seen["cmd"] = cmd
        seen["env"] = env
        return Proc(rc)
    return _run


# T-run-001 — emit to a temp suite, call pytest, exit code passes through
def test_run_emits_temp_and_invokes_pytest(tmp_path, monkeypatch, capsys):
    seen = {}

    def _run(cmd, cwd=None, env=None):
        seen["cmd"] = cmd
        seen["manifest"] = os.path.exists(
            os.path.join(cmd[-1], "taf.manifest.json"))
        return Proc(0)

    monkeypatch.setattr(runner, "_exec", _run)
    rc = runner.run(tracker(), env=dict(NEEDS), extra=["-k", "board"])
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
    assert runner.run(tracker(), env=dict(NEEDS)) == 3


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
    out = capsys.readouterr().out
    assert "preflight missing" in out
    assert "--base-url" in out                 # the hint names the fix


# T-run-004 — --suite runs the committed suite, no emit
def test_committed_suite_runs_in_place(tmp_path, monkeypatch):
    out = str(tmp_path / "suite")
    emit_python.emit(tracker(), out)
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    assert runner.run(tracker(), env=dict(NEEDS), suite=out) == 0
    assert seen["cmd"][-1] == out
    assert os.path.isdir(out)                  # the suite stays


# T-run-005 — --keep keeps the temp suite for debugging
def test_keep_preserves_the_emitted_suite(monkeypatch):
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    runner.run(tracker(), env=dict(NEEDS), keep=True)
    suite = seen["cmd"][-1]
    assert os.path.isdir(suite) and "test_journeys.py" in os.listdir(suite)
    import shutil
    shutil.rmtree(suite)


# T-run-006 — --lang java calls mvn, not pytest
def test_java_runs_mvn_test(monkeypatch):
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    runner.run(tracker(), env=dict(NEEDS), lang="java")
    cmd = seen["cmd"]
    assert cmd[0] == "mvn" and "pom.xml" in cmd[-2] and cmd[-1] == "test"


# T-run-007 — the CLI splits at -- and forwards the runner args;
# the gate is on by default
def test_cli_forwards_passthrough(tmp_path):
    env = {**os.environ, **NEEDS}
    r = subprocess.run(
        [sys.executable, "-m", "taf", "run", TRACKER_MODEL,
         "--", "--collect-only"],
        capture_output=True, text=True, env=env)
    # probe is the default: it refuses first (no SUT up)
    assert r.returncode == 1
    assert "preflight missing" in r.stdout
    r = subprocess.run(
        [sys.executable, "-m", "taf", "run", TRACKER_MODEL, "--no-probe",
         "--", "--collect-only", "-q"],
        capture_output=True, text=True, env=env)
    assert "test_journeys.py: 2" in r.stdout
    assert r.returncode == 0


# T-run-010 — an unset env: need is a gate, no probe required
def test_missing_env_need_refuses_without_probe(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    assert runner.run(tracker(), env={}, probe=False) == 1
    assert "cmd" not in seen
    assert "env TAF_SUT_HANDLE" in capsys.readouterr().out


# T-run-008 — run-profile flags become the child's TAF_* contract
def test_profile_flags_set_child_env(monkeypatch):
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    runner.run(tracker(), env=dict(NEEDS),
               profile={"slowmo": 500, "video": True, "sink": True,
                        "base_url": "http://staging:9"})
    env = seen["env"]
    assert env["TAF_SLOWMO"] == "500" and env["TAF_VIDEO"] == "1"
    assert env["TAF_BASE_URL"] == "http://staging:9"
    assert env["TAF_IKC3_WS"] == "ws://staging:9/bus-ws"


# T-run-009 — the header names the effective profile
def test_header_shows_the_profile(monkeypatch, capsys):
    monkeypatch.setattr(runner, "_exec", fake_exec({}))
    runner.run(tracker(), env=dict(NEEDS), profile={"slowmo": 500, "video": True})
    out = capsys.readouterr().out
    assert "headed" in out and "slowmo 500ms" in out and "video" in out
