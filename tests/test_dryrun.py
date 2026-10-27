"""Tests of taf/dryrun.py — the report half of lane L-12.

Test IDs: T-dry-001.. — a dry run names the tests a run would execute,
the TAF_* contract as the shell sets it, and what the run lacks.
"""

import json
import os
import subprocess
import sys

from taf import dryrun, emit_python, model


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_MODEL = os.path.join(REPO, "suts", "ikc3-tracker.sut.model.json")


def tracker():
    return model.load(TRACKER_MODEL)


def levels(rep):
    return {f["what"]: f["level"] for f in rep["findings"]}


def screen_model(tmp_path):
    doc = {
        "sut": {"name": "x", "base-url": "http://x"},
        "states": {"a": {"route": "/a", "marker": {"role": "heading", "name": "A"}},
                   "b": {"route": "/b", "marker": {"role": "heading", "name": "B"}}},
        "elements": {}, "actions": {},
        "journeys": {"j": {"start": "a",
                           "steps": [{"navigate": "b"},
                                     {"compare-screen": "b-landed"}],
                           "expect-final": {"state": "b"}}},
        "endpoints": {},
    }
    p = tmp_path / "x.sut.model.json"
    p.write_text(json.dumps(doc))
    return model.load(str(p))


# T-dry-001 — what would run is the manifest's truth
def test_report_names_the_tests_a_run_executes():
    rep = dryrun.report(tracker(), env={})
    names = [t["test"] for t in rep["tests"]]
    assert names == ["test_the_board_is_up", "test_board_to_tot"]
    t = rep["tests"][1]
    assert t["journey"] == "board-to-tot" and t["final"] == "tot"
    assert "dwell" in t["steps"]            # forms inside used actions show


# T-dry-002 — the env table is the contract as this shell sets it
def test_env_table_shows_set_and_default():
    rep = dryrun.report(tracker(), env={"TAF_VIDEO": "1", "TAF_HEADLESS": "1"})
    rows = {r["var"]: r for r in rep["env"]}
    assert rows["TAF_VIDEO"]["set"] and rows["TAF_VIDEO"]["effective"] == "on"
    assert rows["TAF_HEADLESS"]["effective"] == "headless"
    assert not rows["TAF_IKC3_WS"]["set"]
    assert rows["TAF_BASE_URL"]["effective"] == "http://127.0.0.1:4856"


# T-dry-003 — unset opt-ins report off, not missing
def test_unset_video_and_sink_report_off():
    lv = levels(dryrun.report(tracker(), env={}))
    assert lv["video"] == "off" and lv["fault reports"] == "off"
    lv = levels(dryrun.report(tracker(), env={"TAF_VIDEO": "x",
                                            "TAF_IKC3_WS": "ws://h/bus-ws"}))
    assert lv["video"] == "ok" and lv["fault reports"] == "ok"


# T-dry-004 — compare-screen without a baseline is missing
def test_golden_baseline_missing_then_found(tmp_path):
    m = screen_model(tmp_path)
    out = str(tmp_path / "suite")
    emit_python.emit(m, out)
    lv = levels(dryrun.report(m, env={}, suite=out))
    assert lv["golden 'b-landed.png'"] == "missing"
    snap = tmp_path / "suite" / "test_journeys.py-snapshots"
    snap.mkdir()
    (snap / "b-landed.png").write_bytes(b"png")
    lv = levels(dryrun.report(m, env={}, suite=out))
    assert lv["golden 'b-landed.png'"] == "ok"


# T-dry-005 — a stale emitted suite is named
def test_stale_suite_is_missing(tmp_path):
    out = str(tmp_path / "suite")
    emit_python.emit(tracker(), out)
    lv = levels(dryrun.report(tracker(), env={}, suite=out))
    assert lv["suite"] == "ok"
    stale = dict(tracker())
    stale["journeys"] = dict(stale["journeys"],
                             extra={"start": "board", "steps": []})
    lv = levels(dryrun.report(stale, env={}, suite=out))
    assert lv["suite"] == "missing"
    lv = levels(dryrun.report(tracker(), env={},
                              suite=str(tmp_path / "nope")))
    assert lv["suite"] == "missing"


# T-dry-006 — rerun with no manifest is missing; with one it replays
def test_rerun_needs_a_failed_manifest(tmp_path):
    env = {"TAF_RERUN": "1", "TAF_RESULTS": str(tmp_path / "results")}
    lv = levels(dryrun.report(tracker(), env=env))
    assert lv["rerun"] == "missing"
    run = tmp_path / "results" / "20261027-010000"
    run.mkdir(parents=True)
    (run / "failed.txt").write_text("test_board_to_tot\n")
    lv = levels(dryrun.report(tracker(), env=env))
    assert lv["rerun"] == "ok"


# T-dry-007 — probes touch the network only on demand
def test_probe_reports_an_unanswering_sut(tmp_path):
    doc = {"sut": {"name": "x", "base-url": "http://127.0.0.1:1"},
           "states": {"a": {"marker": {"css": ".a"}}},
           "journeys": {"j": {"start": "a", "steps": []}}}
    p = tmp_path / "x.sut.model.json"
    p.write_text(json.dumps(doc))
    m = model.load(str(p))
    lv = levels(dryrun.report(m, env={}, probe=True))
    assert lv["sut"] == "missing"
    rep = dryrun.report(m, env={}, probe=False)
    assert "sut" not in levels(rep)          # no probe, no opinion


# T-dry-008 — the CLI prints the report and stays a report (exit 0)
def test_cli_dry_run_prints_and_exits_0(tmp_path):
    r = subprocess.run(
        [sys.executable, "-m", "taf", "dry-run", TRACKER_MODEL],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "would run — 2 test(s)" in r.stdout
    assert "TAF_VIDEO" in r.stdout and "off" in r.stdout
    r = subprocess.run(
        [sys.executable, "-m", "taf", "dry-run", TRACKER_MODEL, "--json"],
        capture_output=True, text=True)
    assert json.loads(r.stdout)["sut"]["name"] == "ikc3-tracker"
