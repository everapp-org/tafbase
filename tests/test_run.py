"""Tests of taf/runner.py — the executed-suite contract.

Test IDs: T-run-001.. — `taf run <dir>` never emits; it reads
taf.suite.json for its toolchain/base-url/env-needs, gates on the
preflight, then calls pytest / mvn / npx playwright test.
"""

import json
import os
import subprocess
import sys

from taf import model, runner
from taf.codegen.python import emitter as emit_python


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_MODEL = os.path.join(REPO, "suts", "ikc3-tracker.sut.model.json")

# The tracker model needs env: credentials — the gate refuses without them.
NEEDS = {"TAF_SUT_CODES": "code-1 code-2"}


def tracker():
    return model.load(TRACKER_MODEL)


def suite(tmp_path):
    out = str(tmp_path / "suite")
    emit_python.emit(tracker(), out)
    return out


def fake_exec(seen, rc=0):
    def _run(cmd, cwd=None, env=None):
        seen["cmd"] = cmd
        seen["cwd"] = cwd
        seen["env"] = env
        return rc
    return _run


# T-run-001 — run executes the emitted suite, never emits
def test_run_executes_the_emitted_suite(tmp_path, monkeypatch, capsys):
    out = suite(tmp_path)
    before = set(os.listdir(out))
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    rc = runner.run(out, env=dict(NEEDS), probe=False,
                    extra=["-k", "board"])
    assert rc == 0
    cmd = seen["cmd"]
    assert cmd[:3] == [sys.executable, "-m", "pytest"]
    assert out in cmd                          # the suite is the target
    assert "-k" in cmd and "board" in cmd      # passthrough reaches the runner
    assert set(os.listdir(out)) == before      # nothing generated at run time
    assert "run:" in capsys.readouterr().out


# T-run-002 — the runner's red is the command's red
def test_runner_exit_code_passes_through(tmp_path, monkeypatch):
    out = suite(tmp_path)
    monkeypatch.setattr(runner, "_exec", fake_exec({}, rc=3))
    assert runner.run(out, env=dict(NEEDS), probe=False) == 3


# T-run-003 — --probe refuses before the runner is ever called
def test_probe_missing_refuses_to_run(tmp_path, monkeypatch, capsys):
    doc = {"sut": {"name": "x", "base-url": "http://127.0.0.1:1"},
           "states": {"a": {"marker": {"css": ".a"}}},
           "journeys": {"j": {"start": "a", "steps": []}}}
    p = tmp_path / "x.sut.model.json"
    p.write_text(json.dumps(doc))
    out = str(tmp_path / "suite")
    emit_python.emit(model.load(str(p)), out)
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    assert runner.run(out, probe=True) == 2
    assert "cmd" not in seen                   # no browser ever opened
    assert "refuse" in capsys.readouterr().out


# T-run-004 — a model file is refused: run takes a suite dir
def test_run_refuses_a_model_file(tmp_path, capsys):
    p = tmp_path / "x.sut.model.json"
    p.write_text("{}")
    from taf import __main__ as cli
    rc = cli.main(["run", str(p)])
    assert rc == 2
    assert "emit-tests" in capsys.readouterr().out


# T-run-006 — the suite's recorded lang picks the runner
def test_java_runs_mvn_test(tmp_path, monkeypatch):
    from taf.codegen.java import emitter as emit_java
    out = str(tmp_path / "suite")
    emit_java.emit(tracker(), out)
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    runner.run(out, env=dict(NEEDS), probe=False)
    cmd = seen["cmd"]
    assert cmd[0] == "mvn" and "pom.xml" in cmd[-2] and cmd[-1] == "test"


def test_ts_and_js_run_playwright_test(tmp_path, monkeypatch):
    from taf.codegen.ts import emitter as emit_ts
    from taf.codegen.js import emitter as emit_js
    for lang, em in (("ts", emit_ts), ("js", emit_js)):
        out = str(tmp_path / ("suite-" + lang))
        em.emit(tracker(), out)
        seen = {}
        monkeypatch.setattr(runner, "_exec", fake_exec(seen))
        runner.run(out, env=dict(NEEDS), probe=False)
        assert seen["cmd"][:3] == ["npx", "playwright", "test"]
        assert seen["cwd"] == out              # playwright runs in the suite


# T-run-007 — the CLI splits at -- and forwards the runner args;
# the gate is on by default
def test_cli_forwards_passthrough(tmp_path):
    out = suite(tmp_path)
    env = {**os.environ, **NEEDS}
    r = subprocess.run(
        [sys.executable, "-m", "taf", "run", out, "--", "--collect-only"],
        capture_output=True, text=True, env=env)
    # probe is the default: it refuses first (no SUT up)
    assert r.returncode == 2
    assert "refuse" in r.stdout
    r = subprocess.run(
        [sys.executable, "-m", "taf", "run", out, "--no-probe",
         "--", "--collect-only", "-q"],
        capture_output=True, text=True, env=env)
    assert "6 tests collected" in r.stdout
    assert r.returncode == 0


# T-run-010 — an unset env: need gates by default, warns under --no-probe
def test_missing_env_need_refuses_by_default(tmp_path, monkeypatch, capsys):
    out = suite(tmp_path)
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    assert runner.run(out, env={}, probe=True) == 2
    assert "cmd" not in seen
    assert "env TAF_SUT_CODES" in capsys.readouterr().out


def test_missing_env_need_only_warns_without_probe(tmp_path, monkeypatch,
                                                   capsys):
    out = suite(tmp_path)
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    assert runner.run(out, env={}, probe=False) == 0
    assert "cmd" in seen                           # the run proceeded
    out_ = capsys.readouterr().out
    assert "preflight warning" in out_ and "env TAF_SUT_CODES" in out_


# T-run-008 — run-profile vars become the child's TAF_* contract
def test_setenv_flags_set_child_env(tmp_path, monkeypatch):
    out = suite(tmp_path)
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    runner.run(out, env=dict(NEEDS), probe=False,
               setenv={"TAF_SLOWMO": "500", "TAF_VIDEO": "1",
                       "TAF_BASE_URL": "http://staging:9",
                       "TAF_IKC3_WS": "ws://staging:9/bus-ws"})
    env = seen["env"]
    assert env["TAF_SLOWMO"] == "500" and env["TAF_VIDEO"] == "1"
    assert env["TAF_BASE_URL"] == "http://staging:9"
    assert env["TAF_IKC3_WS"] == "ws://staging:9/bus-ws"


# T-run-011 — the suite's recorded framework resolves to TAF_FRAMEWORK
def test_recorded_framework_path_reaches_the_child(tmp_path, monkeypatch):
    out = str(tmp_path / "suite")
    emit_python.emit_tests(tracker(), out, framework="../taf-runtime")
    os.makedirs(os.path.join(tmp_path, "taf-runtime"))
    seen = {}
    monkeypatch.setattr(runner, "_exec", fake_exec(seen))
    runner.run(out, env=dict(NEEDS), probe=False)
    assert seen["env"]["TAF_FRAMEWORK"] == os.path.normpath(
        os.path.join(out, "..", "taf-runtime"))
