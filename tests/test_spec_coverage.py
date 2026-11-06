"""The §3.5 coverage gate — every coordinate in taf/dsl/framework-spec.dsl
is pinned by an emission in ALL FOUR languages (Python, Java, TS, JS).
A form or rung that any emitter cannot spell fails here, not in a generated file."""

from taf import spec
from taf.codegen.java import steps as jsteps, common as jcommon
from taf.codegen.python import steps as psteps, common as pcommon
from taf.codegen.ts import steps as tsteps, common as tcommon
from taf.codegen.js import steps as jssteps, common as jscommon


ELEMENTS = {"code": {"css": "#code-in"}, "go": {"role": "button",
                                               "name": "Go"}}
STATES = {"board": {"route": "/?island=board", "marker": {"css": "#top-bar"}}}
ENDPOINTS = {"get-board": {"method": "GET", "path": "/island/{id}",
                           "expect": {"status": 200}}}

# every form, every variant — synthesized args exercise each `when`
STEPS = [
    {"navigate": "board"},
    {"click": {"element": "go"}},
    {"check": {"element": "go"}},
    {"select": {"element": "go", "value": "x"}},
    {"fill": {"element": "code", "value": "literal"}},
    {"fill": {"element": "code", "value": "env:TAF_X"}},
    {"fill": {"element": "code", "value": "env-pool:TAF_XS"}},
    {"wait-for": {"state": "board"}},
    {"wait-for": {"element": "go"}},
    {"api": {"endpoint": "get-board", "args": {"id": "board"},
             "save": {"n": "$.n"}}},
    {"dwell": 500},
    {"wait-any": ["go", "code"]},
    {"compare-screen": "shot"},
    {"expect": {"element": "go"}},
    {"expect": {"element": "go", "hidden": True}},
    {"expect": {"element": "go", "text": "Hi"}},
    {"expect": {"element": "go", "count": 2}},
    {"expect": {"value": "n", "equals": "5"}},
    {"expect": {"element": "go", "soft": True}},
    {"maybe": {"click": {"element": "go"}}},
]

LOCS = [
    {"role": "button"},
    {"role": "button", "name": "Sign in"},
    {"role": "button", "name": "Sign in", "exact": True},
    {"role": "button", "exact": True},
    {"label": "Handle"}, {"text": "The bus"}, {"placeholder": "type"},
    {"testid": "x"}, {"xpath": "//div"}, {"css": "[data-import-id=\"a\"]"},
]


def test_every_form_emits_in_all_four_languages():
    vocab = spec.forms()
    covered = set()
    for step in STEPS:
        form = next(iter(step))
        covered.add(form)
        assert form in vocab, "a tested form missing from the spec: %s" % form
        jl = jsteps._emit_step(step, ENDPOINTS, "    ")
        pl = psteps._emit_step(step, STATES, ENDPOINTS, "    ")
        tl = tsteps._emit_step(step, STATES, ENDPOINTS, "    ")
        jsl = jssteps._emit_step(step, STATES, ENDPOINTS, "    ")
        all_lines = jl + pl + tl + jsl
        assert not any("unsupported step" in l for l in all_lines), \
            "unspellable form %s: %r" % (form, all_lines)
    assert set(vocab) == covered, \
        "spec forms with no coverage: %s" % (set(vocab) - covered)


def test_every_rung_emits_in_all_four_languages():
    rungs = spec.rungs()
    covered = set()
    for loc in LOCS:
        rung = next(iter(loc))
        covered.add(rung)
        assert rung in rungs, "a tested rung missing from the spec: %s" % rung
        for cm in (jcommon, pcommon, tcommon, jscommon):
            assert "page." in cm._loc(loc)
    assert set(rungs) == covered, \
        "spec rungs with no coverage: %s" % (set(rungs) - covered)


def test_css_quotes_escape_in_all_four_languages():
    loc = {"css": '[data-import-id="top-bar/report-a-fault"]'}
    for cm in (jcommon, pcommon, tcommon, jscommon):
        assert '\\"' in cm._loc(loc)
