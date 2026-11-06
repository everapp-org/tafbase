"""T-rec-* — the recorder maps events to model clauses by the ladder."""
from taf import record


def test_click_becomes_a_click_step_and_element():
    elements = {}
    step = record._to_step({"type": "click",
                            "loc": ["css", '[data-import-id="top-bar/report-a-fault"]']},
                           elements)
    assert step == {"click": "data-import-id-top-bar-report-a-fault"}
    assert len(elements) == 1


def test_fill_carries_the_value_and_roles_name():
    elements = {}
    step = record._to_step({"type": "fill",
                            "loc": ["role", "textbox", "Code from your signed-in"],
                            "value": "AB12"}, elements)
    name = step["fill"]["element"]
    assert step["fill"]["value"] == "AB12"
    locs = [loc for _, loc in elements.values()]
    assert locs == [{"role": "textbox", "name": "Code from your signed-in"}]


def test_same_locator_reuses_the_element():
    elements = {}
    ev = {"type": "click", "loc": ["label", "Handle"]}
    assert record._to_step(ev, elements) == record._to_step(ev, elements)
    assert len(elements) == 1


def test_navigate_is_a_note_not_a_step():
    step = record._to_step({"type": "navigate", "url": "http://x/island=board"}, {})
    assert "note" in step


# T-rec-005 — a fill on an env: element records the reference, not the
# typed secret (the model's env: clauses teach the recorder)
def test_env_fill_locators_redact_the_typed_value():
    m = {"elements": {"code": {"css": "#code-in"}},
         "actions": {"log-in": {"do": [
             {"fill": {"element": "code", "value": "env-pool:TAF_SUT_CODES"}}]}}}
    secrets = record._secret_locators(m)
    elements = {}
    step = record._to_step({"type": "fill", "loc": ["css", "#code-in"],
                            "value": "ESCW-UYAV"}, elements, secrets)
    assert step["fill"]["value"] == "env-pool:TAF_SUT_CODES"
    assert "ESCW" not in repr(step)
