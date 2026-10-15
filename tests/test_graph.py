"""T-taf-006 — the SUT graph: seeded walks, replay, coverage, merge."""
import json
import subprocess
import sys

import pytest

from taf import emit_python, graph, model


def _graph_model(tmp_path):
    """A small graph: a->b->c->a triangle plus b->a; d is reachable but a
    dead end (the loader refuses unreachable states)."""
    doc = {
        "sut": {"name": "g", "base-url": "http://x"},
        "states": {s: {"marker": {"css": f".{s}"}, "route": f"/{s}"}
                   for s in ("a", "b", "c", "d")},
        "actions": {
            "a-to-b": {"from": "a", "to": "b", "steps": []},
            "b-to-c": {"from": "b", "to": "c", "steps": []},
            "b-to-a": {"from": "b", "to": "a", "steps": []},
            "c-to-a": {"from": "c", "to": "a", "steps": []},
            "c-to-d": {"from": "c", "to": "d", "steps": []},
        },
        "journeys": {
            "tour": {"start": "a", "steps": ["a-to-b", "b-to-c", "c-to-d"]},
        },
    }
    p = tmp_path / "g.sut.model.json"
    p.write_text(json.dumps(doc))
    return model.load(str(p))


def test_walk_is_deterministic_by_seed(tmp_path):
    m = _graph_model(tmp_path)
    j1 = graph.walk(m, "a", seed=42, steps=6)
    j2 = graph.walk(m, "a", seed=42, steps=6)
    assert j1 == j2                       # a seed replays the walk exactly
    assert j1["start"] == "a"
    assert j1["expect-final"]["state"] in ("a", "b", "c")
    # every step is a real edge from the state the walk was in
    here = "a"
    for step in j1["steps"]:
        assert m["actions"][step]["from"] == here
        here = m["actions"][step]["to"]


def test_walk_refuses_unknown_start_and_dead_end(tmp_path):
    m = _graph_model(tmp_path)
    with pytest.raises(model.ModelRefusal) as e:
        graph.walk(m, "nope", seed=1, steps=3)
    assert e.value.refusals[0]["reason"] == "unknown-state"
    with pytest.raises(model.ModelRefusal) as e:
        graph.walk(m, "d", seed=1, steps=3)
    assert e.value.refusals[0]["reason"] == "dead-end"


def test_cover_mode_takes_every_edge(tmp_path):
    m = _graph_model(tmp_path)
    j = graph.walk(m, "a", seed=7, steps=8, cover=True)
    assert set(j["steps"]) == {"a-to-b", "b-to-c", "b-to-a", "c-to-a", "c-to-d"}


def test_with_journeys_merges_and_refuses_duplicates(tmp_path):
    m = _graph_model(tmp_path)
    m2 = graph.with_journeys(m, {"j1": {"start": "a", "steps": ["a-to-b"]}})
    assert "j1" in m2["journeys"] and "j1" not in m["journeys"]
    with pytest.raises(model.ModelRefusal) as e:
        graph.with_journeys(m2, {"j1": {"start": "a", "steps": []}})
    assert e.value.refusals[0]["reason"] == "duplicate-name"


def test_cli_walk_then_emit_merges(tmp_path):
    m = _graph_model(tmp_path)
    mp = tmp_path / "g.sut.model.json"
    r = subprocess.run(
        [sys.executable, "-m", "taf", "walk", str(mp),
         "--from", "a", "--seed", "9", "--steps", "4", "--name", "walked"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    extra = tmp_path / "walk.json"
    extra.write_text(r.stdout)
    out = tmp_path / "suite"
    emit_python.emit(graph.with_journeys(m, json.loads(r.stdout)["journeys"]),
                     str(out))
    tests = (out / "test_journeys.py").read_text()
    assert "def test_walked(" in tests
    man = json.loads((out / "taf.manifest.json").read_text())
    assert any(t["journey"] == "walked" for t in man["tests"])
