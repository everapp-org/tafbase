"""The parity contract of SPEC-taf-v1-001-04 — lane D-4.

Test IDs: T-parity-001..T-parity-006, T-taf-003 (the lane acceptance:
the same declaration generates equivalent suites in two languages,
or both emitters refuse the same broken model the same way).
"""

import json
import os
import re

from taf import emit_java, emit_python, model, ops


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_MODEL = os.path.join(REPO, "suts", "ikc3-tracker.sut.model.json")


def emit_both(tmp_path):
    m = model.load(TRACKER_MODEL)
    py = str(tmp_path / "py")
    jv = str(tmp_path / "jv")
    emit_python.emit(m, py)
    emit_java.emit(m, jv)
    return py, jv


def read(base, rel):
    with open(os.path.join(base, rel)) as f:
        return f.read()


def norm(name):
    """A test or symbol name modulo language idiom: test_board_to_tot and
    boardToTot are the same name (the test_ prefix is pytest's idiom)."""
    n = re.sub(r"[^a-z0-9]", "", name.lower())
    return n[4:] if n.startswith("test") else n


# T-taf-003 — the contract, whole
def test_same_model_two_equivalent_suites(tmp_path):
    py, jv = emit_both(tmp_path)
    assert read(py, "taf.manifest.json") == read(jv, "taf.manifest.json")


def test_same_test_names_modulo_casing(tmp_path):
    py, jv = emit_both(tmp_path)
    py_names = set(re.findall(r"def (test_\w+)\(", read(py, "test_journeys.py")))
    jv_names = set(re.findall(r"void (\w+)\(\)", read(jv, "src/test/java/taf/generated/JourneysTest.java")))
    assert {norm(n) for n in py_names} == {norm(n) for n in jv_names}


def test_same_assertion_sequence_per_journey(tmp_path):
    """Each journey's marker assertions, in order, in both languages."""
    py, jv = emit_both(tmp_path)
    m = model.load(TRACKER_MODEL)
    for name in m["journeys"]:
        asserts = [arg for op, arg in ops.journey_ops(m, name)
                   if op in ("assert-marker", "assert-final")]
        py_t = read(py, "test_journeys.py")
        jv_t = read(jv, "src/test/java/taf/generated/JourneysTest.java")
        for state in asserts:
            assert f"{ops.state_class(state)}(page).expect_arrived()" in py_t
            assert f"new {ops.state_class(state)}(page).expectArrived();" in jv_t


def test_same_actions_same_steps(tmp_path):
    py, jv = emit_both(tmp_path)
    py_a = read(py, "actions.py")
    jv_a = read(jv, "src/test/java/taf/generated/Actions.java")
    assert "def open_tot(page, base_url):" in py_a
    assert "static void openTot(Page page, String baseUrl)" in jv_a
    assert 'page.goto(base_url + ROUTES["tot"])' in py_a
    assert 'page.navigate(baseUrl + TotPage.ROUTE);' in jv_a


def test_page_objects_carry_the_same_markers(tmp_path):
    py, jv = emit_both(tmp_path)
    assert 'locator(".ikc-dock-theme")' in read(py, "pages.py")
    jdir = "src/test/java/taf/generated/"
    assert 'page.locator(".ikc-dock-theme")' in read(jv, jdir + "BoardPage.java")
    assert 'page.locator(".ikc-dock-theme")' in read(jv, jdir + "TotPage.java")


def test_both_refuse_identically(tmp_path):
    """'Or both refuse': one shared loader — the refusal list a broken model
    gets cannot differ between emitters, because the emitter never runs."""
    bad = json.dumps({"sut": {"name": "x", "base-url": "x"},
                      "states": {}, "journeys": {}})
    for _ in (emit_python, emit_java):
        try:
            model.loads(bad)
        except model.ModelRefusal as e:
            assert e.refusals[0]["reason"] == "empty-model"
        else:
            raise AssertionError("a broken model must be refused")


def test_java_suite_is_reviewable_java(tmp_path):
    _, jv = emit_both(tmp_path)
    t = read(jv, "src/test/java/taf/generated/JourneysTest.java")
    assert "@Test" in t and "extends BaseTest" in t
    assert "// @concept CONCEPT-testing-v1-001-01-arrange-act-assert" in t
    bt = read(jv, "src/test/java/taf/generated/BaseTest.java")
    assert 'getOrDefault("TAF_BASE_URL", "http://127.0.0.1:4856")' in bt
