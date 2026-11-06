"""Tests of `taf env` — the TAF_* contract as shell lines.

Test IDs: T-env-001.. — a console adopts the contract by eval'ing
generated exports; opt-ins export only when asked.
"""

import json
import os
import shlex
import subprocess
import sys

from taf import dryrun, model


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_MODEL = os.path.join(REPO, "suts", "ikc3-tracker.sut.model.json")


def tracker():
    return model.load(TRACKER_MODEL)


def exported(out):
    """VAR -> value for the lines eval would apply."""
    env = {}
    for line in out.splitlines():
        line = line.split("#", 1)[0].strip()   # comments drop
        if line.startswith("export "):
            var, val = line[7:].split("=", 1)
            env[var] = shlex.split(val)[0]
    return env


# T-env-001 — base vars always export; opt-ins stay comments
def test_base_exports_and_optins_stay_comments():
    env = exported(dryrun.env_lines(tracker(), env={}))
    assert env == {"TAF_BASE_URL": "http://127.0.0.1:4856",
                   "TAF_RESULTS": "results"}


# T-env-002 — flags turn the opt-ins on
def test_flags_export_the_optins():
    out = dryrun.env_lines(tracker(), env={}, video=True, headless=True,
                           slowmo=300, debug=True)
    env = exported(out)
    assert env["TAF_VIDEO"] == "1" and env["TAF_HEADLESS"] == "1"
    assert env["TAF_SLOWMO"] == "300" and env["TAF_DEBUG"] == "1"
    assert "TAF_IKC3_WS" not in env          # still a comment


# T-env-003 — a bare --sink derives the bus from the base-url
def test_sink_derives_the_bus_url():
    env = exported(dryrun.env_lines(tracker(), env={}, sink=True))
    assert env["TAF_IKC3_WS"] == "ws://127.0.0.1:4856/bus-ws"
    env = exported(dryrun.env_lines(
        tracker(), env={}, base_url="https://staging.example", sink=True))
    assert env["TAF_IKC3_WS"] == "wss://staging.example/bus-ws"
    env = exported(dryrun.env_lines(tracker(), env={},
                                    sink="ws://other:9/custom"))
    assert env["TAF_IKC3_WS"] == "ws://other:9/custom"


# T-env-003b — the model's env: needs print as fill-in lines
def test_model_needs_become_fillin_lines():
    out = dryrun.env_lines(tracker(), env={})
    assert "export TAF_SUT_CODES=''" in out
    # a set secret is never echoed into the file
    out = dryrun.env_lines(tracker(), env={"TAF_SUT_CODES": "hunter2"})
    assert "hunter2" not in out and "TAF_SUT_CODES is set" in out


# T-env-004 — already-set vars re-export (idempotent in a console)
def test_existing_env_reexports():
    env = exported(dryrun.env_lines(
        tracker(), env={"TAF_VIDEO": "1", "TAF_IKC3_WS": "ws://h/b"}))
    assert env["TAF_VIDEO"] == "1" and env["TAF_IKC3_WS"] == "ws://h/b"


# T-env-005 — --unset clears the whole contract
def test_unset_clears_every_var():
    out = dryrun.env_lines(tracker(), env={}, unset=True)
    unsets = [l.split()[1] for l in out.splitlines()
              if l.startswith("unset ")]
    assert set(unsets) == {"TAF_BASE_URL", "TAF_RESULTS", "TAF_HEADLESS",
                           "TAF_SLOWMO", "TAF_ARRIVE_MS", "TAF_VIDEO",
                           "TAF_DEBUG", "TAF_RERUN", "TAF_IKC3_WS",
                           "TAF_SUT_CODES"}


# T-env-006 — fish gets its own spelling
def test_fish_syntax():
    out = dryrun.env_lines(tracker(), env={}, shell="fish", video=True)
    assert "set -gx TAF_VIDEO 1;" in out
    assert "export TAF_VIDEO" not in out
    out = dryrun.env_lines(tracker(), env={}, shell="fish", unset=True)
    assert "set -e TAF_VIDEO;" in out


# T-env-007 — the CLI prints eval-ready lines
def test_cli_env_prints_exports(tmp_path):
    r = subprocess.run(
        [sys.executable, "-m", "taf", "env", TRACKER_MODEL, "--video"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    env = exported(r.stdout)
    assert env["TAF_BASE_URL"] == "http://127.0.0.1:4856"
    assert env["TAF_VIDEO"] == "1"
