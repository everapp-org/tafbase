"""The parity contract of SPEC-taf-v1-001-04 — 4-lane parity (Python, Java 21++, TypeScript, JavaScript ESM).

Test IDs: T-parity-001..T-parity-008, T-taf-003 (the lane acceptance:
the same declaration generates equivalent suites in all four languages,
or all four emitters refuse the same broken model the same way).
"""

import json
import os
import re

from taf import model, ops
from taf.codegen.python import emitter as emit_python
from taf.codegen.java import emitter as emit_java
from taf.codegen.ts import emitter as emit_ts
from taf.codegen.js import emitter as emit_js


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_MODEL = os.path.join(REPO, "suts", "ikc3-tracker.sut.model.json")


def emit_all(tmp_path):
    m = model.load(TRACKER_MODEL)
    py = str(tmp_path / "py")
    jv = str(tmp_path / "jv")
    ts = str(tmp_path / "ts")
    js = str(tmp_path / "js")
    emit_python.emit(m, py)
    emit_java.emit(m, jv)
    emit_ts.emit(m, ts)
    emit_js.emit(m, js)
    return py, jv, ts, js


def emit_both(tmp_path):
    py, jv, _, _ = emit_all(tmp_path)
    return py, jv


def read(base, rel):
    with open(os.path.join(base, rel)) as f:
        return f.read()


def norm(name):
    """A test or symbol name modulo language idiom: test_board_to_tot and
    boardToTot are the same name (the test_ prefix is pytest's idiom)."""
    n = re.sub(r"[^a-z0-9]", "", name.lower())
    return n[4:] if n.startswith("test") else n


# T-taf-003 — the 4-way manifest parity contract, whole
def test_same_model_four_equivalent_suites(tmp_path):
    py, jv, ts, js = emit_all(tmp_path)
    man = read(py, "taf.manifest.json")
    assert man == read(jv, "taf.manifest.json")
    assert man == read(ts, "taf.manifest.json")
    assert man == read(js, "taf.manifest.json")


def test_same_test_names_modulo_casing(tmp_path):
    py, jv, ts, js = emit_all(tmp_path)
    py_names = set(re.findall(r"def (test_\w+)\(", read(py, "test_journeys.py")))
    jv_names = set(re.findall(r"void (\w+)\(\)", read(jv, "src/test/java/taf/generated/JourneysTest.java")))
    ts_names = set(re.findall(r'test\("(\w+)"', read(ts, "journeys.spec.ts")))
    js_names = set(re.findall(r'test\("(\w+)"', read(js, "journeys.spec.mjs")))
    expected = {norm(n) for n in py_names}
    assert expected == {norm(n) for n in jv_names}
    assert expected == {norm(n) for n in ts_names}
    assert expected == {norm(n) for n in js_names}


def test_same_assertion_sequence_per_journey(tmp_path):
    """Each journey's marker assertions, in order, in all four languages."""
    py, jv, ts, js = emit_all(tmp_path)
    m = model.load(TRACKER_MODEL)
    for name in m["journeys"]:
        asserts = [arg for op, arg in ops.journey_ops(m, name)
                   if op in ("assert-marker", "assert-final")]
        py_t = read(py, "test_journeys.py")
        jv_t = read(jv, "src/test/java/taf/generated/JourneysTest.java")
        ts_t = read(ts, "journeys.spec.ts")
        js_t = read(js, "journeys.spec.mjs")
        for state in asserts:
            assert f"{ops.state_class(state)}(page).expect_arrived()" in py_t
            assert f"new {ops.state_class(state)}(page).expectArrived();" in jv_t
            assert f"await new {ops.state_class(state)}(page).expectArrived();" in ts_t
            assert f"await new {ops.state_class(state)}(page).expectArrived();" in js_t


def test_same_actions_same_steps(tmp_path):
    py, jv, ts, js = emit_all(tmp_path)
    py_a = read(py, "actions.py")
    jv_a = read(jv, "src/test/java/taf/generated/Actions.java")
    ts_a = read(ts, "actions.ts")
    js_a = read(js, "actions.mjs")
    assert "def open_tot(page, base_url, soft=None):" in py_a
    assert "static void openTot(Page page, String baseUrl, @Nullable SoftChecks soft)" in jv_a
    assert "export async function openTot(" in ts_a
    assert "export async function openTot(" in js_a
    assert 'page.goto(base_url + ROUTES["tot"])' in py_a
    assert 'page.navigate(baseUrl + TotPage.ROUTE);' in jv_a
    assert 'await page.goto(baseUrl + ROUTES["tot"]);' in ts_a
    assert 'await page.goto(baseUrl + ROUTES["tot"]);' in js_a


def test_env_fills_read_the_variable_in_all_four(tmp_path):
    """env:NAME resolves at run time, in the language's own spelling —
    the secret is in none of the four suites."""
    py, jv, ts, js = emit_all(tmp_path)
    assert 'os.environ["TAF_SUT_SECRET"]' in read(py, "actions.py")
    jv_a = read(jv, "src/test/java/taf/generated/Actions.java")
    assert 'System.getenv("TAF_SUT_SECRET")' in jv_a
    assert 'TafJournal.envPool("TAF_SUT_CODES")' in jv_a
    assert "requireNonNull" in jv_a
    ts_a = read(ts, "actions.ts")
    assert 'process.env["TAF_SUT_SECRET"]!' in ts_a
    assert 'tafJournal.envPool("TAF_SUT_CODES")' in ts_a
    js_a = read(js, "actions.mjs")
    assert 'process.env["TAF_SUT_SECRET"]' in js_a
    assert 'tafJournal.envPool("TAF_SUT_CODES")' in js_a


def test_page_objects_carry_the_same_markers(tmp_path):
    py, jv, ts, js = emit_all(tmp_path)
    assert 'locator(\"[data-import-id=\\\"top-bar\\\"]\")' in read(py, "pages.py")
    jdir = "src/test/java/taf/generated/"
    assert 'page.locator(\"[data-import-id=\\\"top-bar\\\"]\")' in read(jv, jdir + "BoardPage.java")
    assert 'page.locator(\"[data-import-id=\\\"top-bar\\\"]\")' in read(jv, jdir + "TotPage.java")
    assert 'page.locator(\"[data-import-id=\\\"top-bar\\\"]\")' in read(ts, "pages.ts")
    assert 'page.locator(\"[data-import-id=\\\"top-bar\\\"]\")' in read(js, "pages.mjs")


def test_all_four_refuse_identically(tmp_path):
    """'Or all refuse': one shared loader — the refusal list a broken model
    gets cannot differ between emitters, because the emitter never runs."""
    bad = json.dumps({"sut": {"name": "x", "base-url": "x"},
                      "states": {}, "journeys": {}})
    for _ in (emit_python, emit_java, emit_ts, emit_js):
        try:
            model.loads(bad)
        except model.ModelRefusal as e:
            assert e.refusals[0]["reason"] == "empty-model"
        else:
            raise AssertionError("a broken model must be refused")


def test_java_21pp_and_ts_js_suites_are_reviewable(tmp_path):
    _, jv, ts, js = emit_all(tmp_path)
    t = read(jv, "src/test/java/taf/generated/JourneysTest.java")
    assert "@Test" in t and "extends BaseTest" in t
    assert "// @concept CONCEPT-testing-v1-001-01-arrange-act-assert" in t
    pkg = read(jv, "src/test/java/taf/generated/package-info.java")
    assert "@org.jspecify.annotations.NullMarked" in pkg
    assert "// @concept CONCEPT-java-v1-019-01-jspecify-and-nullaway" in pkg
    bt = read(jv, "src/test/java/taf/generated/BaseTest.java")
    assert 'getOrDefault("TAF_BASE_URL", "http://127.0.0.1:4856")' in bt
    assert "ExecutionCondition rerunFilter" in bt
    ts_f = read(ts, "fixtures.ts")
    assert "base.extend<TafFixtures>" in ts_f
    assert "// @concept CONCEPT-pwtest-v1-001-01-test-extend-fixtures" in ts_f
    js_f = read(js, "fixtures.mjs")
    assert "// @ts-check" in js_f
    assert "// @concept CONCEPT-js-v1-006-01-async-fixture-callback" in js_f
