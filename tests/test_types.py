"""Tests of the TAF/PLAN-taf-v1-002-01 contract — vendor/user
separation and the native test types.

Test IDs: T-types-001.. — tagged journeys, browserless api journeys,
examples/data-driven rows, visual regression, walk separation, the two
emit commands, and the validation refusals that guard them all.
"""

import json
import os
import subprocess
import sys

import pytest

from taf import model, ops
from taf.codegen.python import emitter as emit_python
from taf.codegen.java import emitter as emit_java
from taf.codegen.ts import emitter as emit_ts
from taf.codegen.js import emitter as emit_js


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_MODEL = os.path.join(REPO, "suts", "ikc3-tracker.sut.model.json")


def tracker():
    return model.load(TRACKER_MODEL)


def emit_all(m, tmp_path):
    outs = {}
    for lang, em in (("py", emit_python), ("jv", emit_java),
                     ("ts", emit_ts), ("js", emit_js)):
        out = str(tmp_path / lang)
        em.emit(m, out)
        outs[lang] = out
    return outs


def read(base, rel):
    with open(os.path.join(base, rel)) as f:
        return f.read()


def _bad(doc, *reasons):
    with pytest.raises(model.ModelRefusal) as e:
        model.loads(json.dumps(doc))
    got = {r["reason"] for r in e.value.refusals}
    assert set(reasons) <= got, (set(reasons), got)


# ── the model clauses ──────────────────────────────────────────────

def test_journey_type_inference():
    """type is declared or inferred: compare-screen → visual; only
    api-safe steps without start → api; walk tag → walk; else ui."""
    m = model.loads(json.dumps({
        "sut": {"name": "x", "base-url": "http://x"},
        "states": {"a": {"marker": {"css": ".a"}}},
        "endpoints": {"ep": {"method": "GET", "path": "/p"}},
        "journeys": {
            "ui": {"start": "a", "steps": []},
            "vis": {"start": "a",
                    "steps": [{"compare-screen": "shot"}]},
            "api": {"steps": [{"api": "ep"}]},
            "w": {"start": "a", "steps": [],
                  "type": "walk", "tags": ["walk"]},
        }}))
    assert ops.journey_type(m, "ui") == "ui"
    assert ops.journey_type(m, "vis") == "visual"
    assert ops.journey_type(m, "api") == "api"
    assert ops.journey_type(m, "w") == "walk"


def test_bad_journey_type_refuses():
    _bad({"sut": {"name": "x", "base-url": "x"},
          "states": {"a": {"marker": {"css": ".a"}}},
          "journeys": {"j": {"start": "a", "type": "bogus", "steps": []}}},
         "bad-journey-type")


def test_api_journey_with_page_step_refuses():
    _bad({"sut": {"name": "x", "base-url": "x"},
          "states": {"a": {"marker": {"css": ".a"}}},
          "endpoints": {"ep": {"method": "GET", "path": "/p"}},
          "elements": {"b": {"css": ".b"}},
          "journeys": {"j": {"type": "api",
                             "steps": [{"api": "ep"}, {"click": "b"}]}}},
         "bad-journey-type")


def test_api_journey_named_action_refuses():
    _bad({"sut": {"name": "x", "base-url": "x"},
          "states": {"a": {"marker": {"css": ".a"}},
                      "b": {"marker": {"css": ".b"}}},
          "actions": {"go": {"from": "a", "to": "b", "do": []}},
          "journeys": {"j": {"type": "api", "steps": ["go"]}}},
         "bad-journey-type")


def test_bad_examples_refuse():
    _bad({"sut": {"name": "x", "base-url": "x"},
          "states": {"a": {"marker": {"css": ".a"}}},
          "elements": {"n": {"label": "Nick"}},
          "journeys": {"j": {"start": "a",
                             "steps": [{"fill": {"element": "n",
                                                 "value": "${id}"}}],
                             "examples": [{"name": "r1"}]}}},
         "bad-examples")


def test_bad_tag_refuses():
    _bad({"sut": {"name": "x", "base-url": "x"},
          "states": {"a": {"marker": {"css": ".a"}}},
          "journeys": {"j": {"start": "a", "tags": ["not a tag"],
                             "steps": []}}},
         "bad-identifier")


def test_compare_screen_dict_validation():
    _bad({"sut": {"name": "x", "base-url": "x"},
          "states": {"a": {"marker": {"css": ".a"}}},
          "journeys": {"j": {"start": "a",
                             "steps": [{"compare-screen": {}}]}}},
         "bad-compare-screen")


# ── the emitted separation ─────────────────────────────────────────

def test_emit_framework_needs_no_model(tmp_path):
    """The vendor artifact emits from no model at all — pure machinery."""
    for lang, em in (("py", emit_python), ("jv", emit_java),
                     ("ts", emit_ts), ("js", emit_js)):
        out = str(tmp_path / lang)
        written = em.emit_framework(out)
        assert written and all(os.path.exists(p) for p in written)


def test_framework_contains_no_sut_facts(tmp_path):
    """grep the emitted taf-runtime for the SUT's url — it must not
    appear anywhere in the vendor artifact."""
    out = str(tmp_path / "fw")
    emit_python.emit_framework(out)
    for root, _, files in os.walk(out):
        for f in files:
            text = open(os.path.join(root, f), encoding="utf8").read()
            assert "127.0.0.1:4856" not in text
            assert "TAF_SUT_CODES" not in text  # SUT needs stay SUT-side


def test_user_suite_contains_the_sut_facts(tmp_path):
    out = str(tmp_path / "suite")
    emit_python.emit_tests(tracker(), out, framework="../taf-runtime")
    sc = read(out, "sut_config.py")
    assert "http://127.0.0.1:4856" in sc
    assert "TAF_SUT_CODES" in sc
    meta = json.loads(read(out, "taf.suite.json"))
    assert meta["lang"] == "python" and meta["framework"] == "../taf-runtime"
    assert "TAF_SUT_CODES" in meta["env-needs"]


def test_tags_reach_all_four_runners(tmp_path):
    m = tracker()
    outs = emit_all(m, tmp_path)
    assert "@pytest.mark.smoke" in read(outs["py"], "test_journeys.py")
    assert '@Tag("smoke")' in read(
        outs["jv"], "src/test/java/taf/generated/JourneysTest.java")
    assert '"@smoke"' in read(outs["ts"], "journeys.spec.ts")
    assert '"@smoke"' in read(outs["js"], "journeys.spec.mjs")


def test_api_journeys_emit_browserless_in_all_four(tmp_path):
    m = tracker()
    outs = emit_all(m, tmp_path)
    py = read(outs["py"], "test_api.py")
    assert "def test_make_a_tot_over_the_api(api, base_url, soft" in py
    assert "page" not in py.split(
        "def test_make_a_tot_over_the_api(")[1].split("):", 1)[0]
    jv = read(outs["jv"], "src/test/java/taf/generated/ApiTest.java")
    assert "extends taf.runtime.ApiBaseTest" in jv
    ts = read(outs["ts"], "api.spec.ts")
    assert "{ request, baseUrl, soft }" in ts and "request.post" in ts
    js = read(outs["js"], "api.spec.mjs")
    assert "{ request, baseUrl, soft }" in js and "request.post" in js


def test_examples_emit_native_parameterization(tmp_path):
    m = tracker()
    outs = emit_all(m, tmp_path)
    py = read(outs["py"], "test_api.py")
    assert "@pytest.mark.parametrize" in py
    assert '"tot-a"' in py and '"tot-b"' in py
    jv = read(outs["jv"], "src/test/java/taf/generated/ApiTest.java")
    assert "@ParameterizedTest" in jv and "@MethodSource" in jv
    ts = read(outs["ts"], "api.spec.ts")
    assert ".entries()" in ts and '"tot-a"' in ts
    js = read(outs["js"], "api.spec.mjs")
    assert ".entries()" in js and '"tot-a"' in js


def test_visual_journeys_emit_the_comparator(tmp_path):
    m = tracker()
    outs = emit_all(m, tmp_path)
    py = read(outs["py"], "test_visual.py")
    assert "visual.compare(" in py and '"board-top"' in py
    jv = read(outs["jv"], "src/test/java/taf/generated/VisualTest.java")
    assert "VisualComparator.compare" in jv
    ts = read(outs["ts"], "visual.spec.ts")
    assert "visual.compare(" in ts and '"board-top"' in ts
    js = read(outs["js"], "visual.spec.mjs")
    assert "visual.compare(" in js and '"board-top"' in js


def test_walks_never_mix_with_authored_journeys(tmp_path):
    m = tracker()
    m["journeys"]["walk-board-1"] = {
        "type": "walk", "tags": ["walk", "exploratory"],
        "start": "board", "steps": ["open-tot"],
        "expect-final": {"state": "tot"}}
    out = str(tmp_path / "suite")
    emit_python.emit(m, out)
    ui = read(out, "test_journeys.py")
    walks = read(out, "test_walks.py")
    assert "test_walk_board_1" not in ui
    assert "test_walk_board_1" in walks
    assert "@pytest.mark.walk" in walks


def test_manifest_records_type_and_tags(tmp_path):
    man = json.loads(read(str(tmp_path / "s"), "taf.manifest.json")) \
        if False else None
    m = tracker()
    man = ops.manifest(m)
    by_journey = {t["journey"]: t for t in man["tests"]}
    assert by_journey["board-to-tot"]["type"] == "ui"
    assert "smoke" in by_journey["board-to-tot"]["tags"]
    assert by_journey["make-a-tot-over-the-api"]["type"] == "api"
    assert by_journey["the-board-looks-right"]["type"] == "visual"


# ── the CLI surface ────────────────────────────────────────────────

def test_cli_emit_framework_and_emit_tests(tmp_path):
    fw = str(tmp_path / "taf-runtime")
    r = subprocess.run(
        [sys.executable, "-m", "taf", "emit-framework",
         "--lang", "python", "-o", fw],
        capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stderr
    assert os.path.exists(os.path.join(fw, "taf_runtime", "fixtures.py"))
    out = str(tmp_path / "suite")
    r = subprocess.run(
        [sys.executable, "-m", "taf", "emit-tests", TRACKER_MODEL,
         "--lang", "python", "-o", out, "--framework", fw],
        capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stderr
    meta = json.loads(open(os.path.join(out, "taf.suite.json")).read())
    assert meta["framework"] == fw


def test_cli_promote_copies_actuals_to_expected(tmp_path):
    run_dir = tmp_path / "results" / "run1" / "test-x"
    run_dir.mkdir(parents=True)
    (run_dir / "board-top_Actual.png").write_bytes(b"png")
    goldens = tmp_path / "suite" / "goldens"
    r = subprocess.run(
        [sys.executable, "-m", "taf", "promote",
         "--results", str(tmp_path / "results"),
         "--goldens", str(goldens)],
        capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stderr
    assert (goldens / "board-top_Expected.png").read_bytes() == b"png"
    assert "promoted" in r.stdout
