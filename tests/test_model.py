"""Tests of taf/model.py — the SPEC-taf-v1-001-04 refusal contract.

Test IDs: T-model-001..T-model-013, T-taf-001 (the lane A-1 acceptance:
a valid model loads, a broken model names its fault).
"""

import json
import os

import pytest

from taf import model


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_MODEL = os.path.join(REPO, "suts", "ikc3-tracker.sut.model.json")


def minimal(**over):
    doc = {
        "sut": {"name": "fixture", "base-url": "http://x"},
        "states": {"a": {"route": "/a", "marker": {"role": "heading", "name": "A"}},
                   "b": {"route": "/b", "marker": {"css": ".b"}}},
        "elements": {"go": {"role": "button", "name": "Go"}},
        "actions": {"go-b": {"from": "a", "to": "b",
                             "do": [{"click": "go"}]}},
        "journeys": {"go": {"start": "a", "steps": ["go-b"],
                            "expect-final": {"state": "b"}}},
        "endpoints": {},
    }
    doc.update(over)
    return doc


def refusals_of(doc):
    return model.validate(doc)


# T-taf-001 — the acceptance of lane A-1
def test_the_tracker_model_loads():
    m = model.load(TRACKER_MODEL)
    assert m["sut"]["name"] == "ikc3-tracker"
    assert set(m["journeys"]) == {"the-board-is-up", "board-to-tot", "files-a-fault-report"}


def test_a_valid_model_refuses_nothing():
    assert refusals_of(minimal()) == []


def test_refusal_shape_is_the_spec_contract():
    rs = refusals_of({"journeys": {}, "states": {}, "sut": {"name": "x", "base-url": "x"}})
    assert rs
    for r in rs:
        assert set(r) == {"clause", "reason", "message"}


# T-model-001
def test_not_json():
    with pytest.raises(model.ModelRefusal) as e:
        model.loads("{not json")
    assert e.value.refusals[0]["reason"] == "not-json"


# T-model-002
def test_empty_model():
    rs = refusals_of({"sut": {"name": "x", "base-url": "x"},
                      "states": {}, "journeys": {}})
    assert [r["reason"] for r in rs] == ["empty-model"]


# T-model-003
def test_missing_top_level_field():
    rs = refusals_of({"sut": {"name": "x", "base-url": "x"}, "states": {}})
    assert any(r["reason"] == "missing-field" and "journeys" in r["message"] for r in rs)


# T-model-004
def test_bad_locator():
    doc = minimal()
    doc["elements"]["go"] = {"wrong": "form"}
    rs = refusals_of(doc)
    assert any(r["reason"] == "bad-locator" and r["clause"] == "elements.go" for r in rs)


# T-model-005
def test_a_state_needs_a_marker():
    doc = minimal()
    doc["states"]["a"] = {"route": "/a"}
    rs = refusals_of(doc)
    assert any(r["reason"] == "missing-field" and r["clause"] == "states.a" for r in rs)


# T-model-006
def test_unknown_state_in_action_and_journey():
    doc = minimal()
    doc["actions"]["go-b"]["to"] = "nowhere"
    doc["journeys"]["go"]["expect-final"] = {"state": "elsewhere"}
    reasons = [r["reason"] for r in refusals_of(doc)]
    assert reasons.count("unknown-state") == 2


# T-model-007
def test_unknown_element():
    doc = minimal()
    doc["actions"]["go-b"]["do"] = [{"click": "not-there"}]
    assert any(r["reason"] == "unknown-element" for r in refusals_of(doc))


# T-model-008
def test_unknown_endpoint():
    doc = minimal()
    doc["actions"]["call"] = {"from": "a", "to": "b", "do": [{"api": "no-such"}]}
    assert any(r["reason"] == "unknown-endpoint" for r in refusals_of(doc))


# T-model-009
def test_unknown_action():
    doc = minimal()
    doc["journeys"]["go"]["steps"] = ["not-an-action"]
    assert any(r["reason"] == "unknown-action" for r in refusals_of(doc))


# T-model-010
def test_edge_gap():
    doc = minimal()
    doc["actions"]["elsewhere"] = {"from": "z", "to": "b", "do": []}
    doc["states"]["z"] = {"marker": {"css": ".z"}}
    doc["journeys"]["go"]["steps"] = ["elsewhere", "go-b"]
    rs = refusals_of(doc)
    assert any(r["reason"] == "edge-gap" for r in rs)


# T-model-011
def test_unreachable_state():
    doc = minimal()
    doc["states"]["orphan"] = {"marker": {"css": ".orphan"}}
    assert any(r["reason"] == "unreachable" and "orphan" in r["clause"] for r in refusals_of(doc))


# T-model-012
def test_duplicate_name():
    text = '{"sut": {"name": "x", "name": "y", "base-url": "b"}, ' \
           '"states": {"a": {"marker": {"css": ".a"}}}, ' \
           '"journeys": {"j": {"start": "a", "steps": []}}}'
    with pytest.raises(model.ModelRefusal) as e:
        model.loads(text)
    assert any(r["reason"] == "duplicate-name" for r in e.value.refusals)


# T-model-013
def test_dwell_is_pacing_not_sync():
    doc = minimal()
    doc["actions"]["go-b"]["do"] = [{"click": "go"}, {"dwell": 400}]
    assert refusals_of(doc) == []


def test_bad_dwell_refuses():
    for bad in (-1, "400", None):
        doc = minimal()
        doc["actions"]["go-b"]["do"] = [{"dwell": bad}]
        rs = refusals_of(doc)
        assert any(r["reason"] == "bad-dwell" for r in rs), (bad, rs)


def test_wait_any_and_maybe_validate():
    doc = minimal()
    doc["actions"]["go-b"]["do"] = [
        {"wait-any": ["go", "go"]},
        {"maybe": {"click": "go"}},
        {"expect": {"element": "go", "soft": True}},
    ]
    assert refusals_of(doc) == []


def test_wait_any_bad_args_refuse():
    for bad in ("go", ["go"], ["go", "nope"]):
        doc = minimal()
        doc["actions"]["go-b"]["do"] = [{"wait-any": bad}]
        rs = refusals_of(doc)
        assert rs, bad
        assert any(r["reason"] in ("bad-wait-any", "unknown-element")
                   for r in rs), (bad, rs)


def test_maybe_wraps_and_validates_inner():
    doc = minimal()
    doc["actions"]["go-b"]["do"] = [{"maybe": {"click": "nope"}}]
    assert any(r["reason"] == "unknown-element" for r in refusals_of(doc))
    doc = minimal()
    doc["actions"]["go-b"]["do"] = [{"maybe": 5}]
    assert any(r["reason"] == "bad-maybe" for r in refusals_of(doc))


def test_mixed_steps():
    doc = minimal()
    doc["journeys"]["go"]["steps"] = ["go-b", {"navigate": "a"}]
    assert any(r["reason"] == "mixed-steps" for r in refusals_of(doc))


# T-model-014 — env: values name a need; an empty env: is a refusal
def test_env_fill_names_a_variable():
    doc = minimal()
    doc["elements"]["secret"] = {"label": "Secret"}
    doc["actions"]["go-b"]["do"] = [
        {"fill": {"element": "secret", "value": "env:TAF_SUT_SECRET"}}]
    assert refusals_of(doc) == []
    doc["actions"]["go-b"]["do"] = [
        {"fill": {"element": "secret", "value": "env:"}}]
    reasons = [r["reason"] for r in refusals_of(doc)]
    assert "bad-env" in reasons


def test_env_needs_collects_what_steps_read():
    doc = minimal()
    doc["elements"]["secret"] = {"label": "Secret"}
    doc["actions"]["go-b"]["do"] = [
        {"fill": {"element": "secret", "value": "env:TAF_SUT_SECRET"}},
        {"maybe": {"fill": {"element": "secret", "value": "env:TAF_SUT_HANDLE"}}}]
    m = model.loads(json.dumps(doc))
    assert model.env_needs(m) == ["TAF_SUT_HANDLE", "TAF_SUT_SECRET"]


# T-model-015 — sut.auth names an action; its from state is reachable
def test_auth_clause_validation():
    doc = minimal()
    doc["sut"]["auth"] = {"action": "go-b"}
    assert refusals_of(doc) == []
    doc["sut"]["auth"] = {"action": "ghost"}
    assert any(r["reason"] == "unknown-action" for r in refusals_of(doc))
    doc["sut"]["auth"] = {}
    assert any(r["reason"] == "missing-field" and r["clause"] == "sut.auth"
               for r in refusals_of(doc))
    doc["sut"]["auth"] = {"action": "to-b"}
    doc["actions"]["to-b"] = {"to": "b", "do": []}   # no from — can't bootstrap
    assert any(r["reason"] == "bad-auth" for r in refusals_of(doc))


def test_env_needs_includes_the_auth_action():
    doc = minimal()
    doc["elements"]["code"] = {"label": "Code"}
    doc["actions"]["auth-in"] = {
        "from": "a", "to": "b",
        "do": [{"fill": {"element": "code", "value": "env-pool:CODES"}}]}
    doc["sut"]["auth"] = {"action": "auth-in"}
    m = model.loads(json.dumps(doc))
    assert model.env_needs(m) == ["CODES"]


def test_env_pool_spends_in_order_and_dries(monkeypatch):
    from taf import journal_runtime as jr
    monkeypatch.setenv("P", "a b c")
    assert [jr.env_pool("P"), jr.env_pool("P"), jr.env_pool("P")] == ["a", "b", "c"]
    with pytest.raises(RuntimeError, match="ran dry"):
        jr.env_pool("P")
    with pytest.raises(RuntimeError, match="unset"):
        jr.env_pool("NOPE")


def test_load_raises_with_all_refusals():
    bad = dict(minimal())
    bad["states"] = {"a": {}}
    bad["journeys"] = {"j": {"steps": ["ghost"]}}
    with pytest.raises(model.ModelRefusal) as e:
        model.loads(json.dumps(bad))
    reasons = {r["reason"] for r in e.value.refusals}
    assert {"missing-field", "unknown-action", "unreachable"} <= reasons
