"""Tests of taf/emit_python.py — lane B-2.

Test IDs: T-emit-001..T-emit-008, T-taf-004 (the lane acceptance:
one declaration produces a committed, reviewable pytest suite).
"""

import json
import os

from taf import emit_python, model


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_MODEL = os.path.join(REPO, "suts", "ikc3-tracker.sut.model.json")


def emit(tmp_path, doc=None):
    if doc is None:
        m = model.load(TRACKER_MODEL)
    else:
        m = model.loads(json.dumps(doc))
    out = str(tmp_path / "suite")
    emit_python.emit(m, out)
    return out


def read(out, name):
    with open(os.path.join(out, name)) as f:
        return f.read()


# T-taf-004 — the tracker model produces a real suite
def test_the_tracker_model_emits_a_suite(tmp_path):
    out = emit(tmp_path)
    names = set(os.listdir(out))
    assert {"conftest.py", "pages.py", "actions.py",
            "test_journeys.py", "taf.manifest.json"} <= names


def test_pages_prove_arrival(tmp_path):
    pages = read(emit(tmp_path), "pages.py")
    assert 'class BoardPage' in pages and 'class TotPage' in pages
    assert 'locator(".ikc-dock-theme")' in pages
    assert 'expect(self.marker).to_be_visible()' in pages


def test_journey_test_is_aaa(tmp_path):
    j = read(emit(tmp_path), "test_journeys.py")
    assert "def test_board_to_tot(page, base_url, soft):" in j
    assert "actions.open_tot(page, base_url, soft)" in j
    # the to-marker of the action and the expect-final state are asserted
    assert j.count("TotPage(page).expect_arrived()") == 2
    # every generated file teaches: concept citations travel with the code
    assert "@concept CONCEPT-testing-v1-001-01-arrange-act-assert" in j


def test_the_manifest_traces_tests_to_model(tmp_path):
    man = json.loads(read(emit(tmp_path), "taf.manifest.json"))
    assert man["sut"] == "ikc3-tracker"
    t = {t["test"]: t for t in man["tests"]}
    assert t["test_board_to_tot"]["journey"] == "board-to-tot"
    assert t["test_board_to_tot"]["actions"] == ["open-tot"]
    assert t["test_board_to_tot"]["states"] == ["board", "tot"]


def test_conftest_is_real_playwright(tmp_path):
    c = read(emit(tmp_path), "conftest.py")
    assert "sync_playwright" in c and "browser.new_context" in c
    assert '"http://127.0.0.1:4856"' in c


def test_elements_and_endpoints_emit_when_declared(tmp_path):
    doc = {
        "sut": {"name": "x", "base-url": "http://x"},
        "states": {"a": {"route": "/a", "marker": {"css": ".a"}},
                   "b": {"route": "/b", "marker": {"css": ".b"}}},
        "elements": {"go-btn": {"role": "button", "name": "Go"},
                     "nick": {"label": "Nickname"}},
        "actions": {"go": {"from": "a", "to": "b",
                           "do": [{"click": "go-btn"},
                                  {"fill": {"element": "nick", "value": "ada"}},
                                  {"api": "list"}]}},
        "journeys": {"j": {"start": "a", "steps": ["go"],
                           "expect-final": {"state": "b"}}},
        "endpoints": {"list": {"method": "GET", "path": "/api/x",
                               "expect": {"status": 200}}},
    }
    out = emit(tmp_path, doc)
    els = read(out, "elements.py")
    assert 'get_by_role("button", name="Go")' in els
    assert 'get_by_label("Nickname")' in els
    acts = read(out, "actions.py")
    assert "elements.go_btn(page).click()" in acts
    assert 'elements.nick(page).fill("ada")' in acts
    assert 'page.request.get(base_url + "/api/x".format(**{}))' in acts
    assert "assert resp.status == 200" in acts


def test_inline_steps_in_a_journey(tmp_path):
    doc = {
        "sut": {"name": "x", "base-url": "http://x"},
        "states": {"a": {"route": "/a", "marker": {"css": ".a"}},
                   "b": {"route": "/b", "marker": {"css": ".b"}}},
        "elements": {}, "endpoints": {},
        "actions": {},
        "journeys": {"j": {"start": "a",
                           "steps": [{"navigate": "b"}],
                           "expect-final": {"state": "b"}}},
    }
    j = read(emit(tmp_path, doc), "test_journeys.py")
    assert 'page.goto(base_url + ROUTES["b"])' in j


def test_dwell_emits_a_real_pause(tmp_path):
    acts = read(emit(tmp_path), "actions.py")
    assert "page.wait_for_timeout(800)" in acts


def test_actions_narrate_their_title(tmp_path):
    acts = read(emit(tmp_path), "actions.py")
    assert 'taf_journal.note("→ open the TOT island")' in acts


def test_watch_forms_emit(tmp_path):
    doc = {
        "sut": {"name": "x", "base-url": "http://x"},
        "states": {"a": {"route": "/a", "marker": {"css": ".a"}},
                   "b": {"route": "/b", "marker": {"css": ".b"}}},
        "elements": {"x1": {"css": ".x1"}, "x2": {"css": ".x2"},
                     "maybe-x": {"css": ".maybe"}},
        "endpoints": {},
        "actions": {"go-b": {"from": "a", "to": "b", "title": "go to b",
                             "do": [{"wait-any": ["x1", "x2"]},
                                    {"maybe": {"click": "maybe-x"}},
                                    {"expect": {"element": "x1", "soft": True}}]}},
        "journeys": {"j": {"start": "a", "steps": ["go-b"],
                           "expect-final": {"state": "b"}}},
    }
    acts = read(emit(tmp_path, doc), "actions.py")
    assert "elements.x1(page).or_(elements.x2(page))" in acts
    assert "except Exception:" in acts and "maybe:" in acts
    assert 'print("soft expect failed:"' in acts


def test_generated_code_is_python(tmp_path):
    import py_compile
    out = emit(tmp_path)
    for name in os.listdir(out):
        if name.endswith(".py"):
            py_compile.compile(os.path.join(out, name), doraise=True)
