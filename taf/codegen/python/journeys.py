"""The test files — one per test type: test_journeys.py (ui),
test_api.py (browserless), test_visual.py (golden grammar),
test_walks.py (seeded graph walks)."""

import json

from .common import *
from .actions import _needs_of, _saves
from .steps import _emit_step

_SUITE_FILES = {"ui": "test_journeys.py", "api": "test_api.py",
                "visual": "test_visual.py", "walk": "test_walks.py"}

_SUITE_TITLES = {
    "ui": "One test per declared journey — arrange, act, assert.",
    "api": "Browserless endpoint journeys — no Page ever opens.",
    "visual": "Golden-screenshot regression — `taf promote` approves baselines.",
    "walk": "Seeded graph walks — exploratory, deterministic by seed.",
}

_FIXTURES = {"api": "(api, base_url, soft",
             "ui": "(page, base_url, soft",
             "visual": "(page, base_url, soft",
             "walk": "(page, base_url, soft"}


def suite_filename(jtype):
    return _SUITE_FILES[jtype]


def _marks(m, name):
    """pytest.mark decorators from journey.tags — native filtering:
    `pytest -m smoke`, `pytest -m "not walk"`."""
    return [f"@pytest.mark.{_py(t)}" for t in ops.journey_tags(m, name)]


def _body_ui(m, name, j):
    """arrange/act/assert for a page-bound journey (ui, visual, walk)."""
    start = j["start"]
    ctx = {"visual": ops.journey_type(m, name) == "visual"}
    if ops.journey_examples(m, name):
        ctx["row"] = "example"
    body = [f"    # arrange\n"
            f"    sut = {_state_class(start)}(page)\n"
            f"    sut.goto(base_url)\n"
            f"    sut.expect_arrived()\n"
            f"    # act\n"]
    inline = [s for s in j.get("steps", []) if isinstance(s, dict)]
    if _saves(inline):
        body.append("    saved = {}\n")
    for op, arg in ops.journey_ops(m, name)[1:]:
        if op == "run":
            body.append(f"    actions.{_py(arg)}(page, base_url, soft)\n")
        elif op == "step":
            body.append("\n".join(
                _emit_step(arg, m["states"], m.get("endpoints") or {},
                           "    ", ctx)) + "\n")
        elif op == "assert-marker":
            body.append(f"    {_state_class(arg)}(page).expect_arrived()\n")
        elif op == "assert-final":
            body.append("    # assert\n")
            body.append(f"    {_state_class(arg)}(page).expect_arrived()\n")
    if not any(op == "assert-final" for op, _ in ops.journey_ops(m, name)):
        body.append("    # assert\n")
    return body


def _body_api(m, name, j):
    """Browserless — the api fixture is an APIRequestContext."""
    ctx = {"api": True}
    if ops.journey_examples(m, name):
        ctx["row"] = "example"
    body = []
    inline = [s for s in j.get("steps", []) if isinstance(s, dict)]
    if _saves(inline):
        body.append("    saved = {}\n")
    for s in inline:
        body.append("\n".join(
            _emit_step(s, m["states"], m.get("endpoints") or {},
                       "    ", ctx)) + "\n")
    return body or ["    pass\n"]


def _test_fn(m, name, jtype):
    j = m["journeys"][name]
    rows = ops.journey_examples(m, name)
    lines = []
    for mark in _marks(m, name):
        lines.append(mark + "\n")
    sig_name = ops.test_name_snake(name)
    if rows:
        ids = [str(r.get("id", i)) for i, r in enumerate(rows)]
        lines.append(
            "@pytest.mark.parametrize(\"example\", %s, ids=%s)\n"
            % (json.dumps(rows), json.dumps(ids)))
        lines.append("def %s%s, example):\n" % (sig_name, _FIXTURES[jtype]))
    else:
        lines.append("def %s%s):\n" % (sig_name, _FIXTURES[jtype]))
    body = (_body_api(m, name, j) if jtype == "api"
            else _body_ui(m, name, j))
    return "".join(lines + body) + "\n"


def _imports(m, names, jtype):
    inline = [s for name in names
              for s in m["journeys"][name].get("steps", [])
              if isinstance(s, dict)]
    imports = ["import pytest"]
    if jtype == "api":
        imports.append("import time")
        imports.append("from taf_runtime import journal as taf_journal")
        return "\n".join(imports) + "\n\n"
    if m.get("actions") and any(
            isinstance(s, str)
            for name in names for s in m["journeys"][name].get("steps", [])):
        imports.append("import actions")
    if _needs_of(inline, "env"):
        imports.append("import os")
    if inline:
        imports.append("from taf_runtime import journal as taf_journal")
    if m.get("elements"):
        imports.append("import elements")
    if jtype == "visual":
        imports.append("from taf_runtime import visual")
    states_needed = {m["journeys"][n].get("start") for n in names}
    for name in names:
        for op, arg in ops.journey_ops(m, name):
            if op in ("assert-marker", "assert-final"):
                states_needed.add(arg)
    states_needed.discard(None)
    imports.append("from pages import ROUTES, %s" % ", ".join(
        sorted(_state_class(n) for n in states_needed)))
    return "\n".join(imports) + "\n\n"


def _suite_file(m, jtype):
    """The emitted test module for one type, or None when the model
    has no journeys of it."""
    names = [n for n in m["journeys"] if ops.journey_type(m, n) == jtype]
    if not names:
        return None
    lines = [_HEADER,
             '"""%s\n\n' % _SUITE_TITLES[jtype],
             "@concept CONCEPT-testing-v1-001-01-arrange-act-assert\n"
             "@concept CONCEPT-qa-v1-001-01-arrange-act-assert\n"
             "@concept CONCEPT-istqb-v1-010-01-state-transition-testing\n"
             '"""\n\n',
             _imports(m, names, jtype)]
    for name in names:
        lines.append(_test_fn(m, name, jtype) + "\n")
    return "".join(lines)


def _pytest_ini(m):
    """Registered markers — the declared tags a run filters by
    (`pytest -m smoke`)."""
    tags = set()
    for name in m["journeys"]:
        tags.update(ops.journey_tags(m, name))
    if not tags:
        return None
    desc = {"ui": "browser UI journeys",
            "api": "browserless endpoint tests",
            "visual": "golden-screenshot regression",
            "walk": "seeded graph walks (exploratory)",
            "exploratory": "model-derived exploratory tests"}
    lines = ["[pytest]", "markers ="]
    for t in sorted(tags):
        lines.append("    %s: %s" % (_py(t), desc.get(t, "model-declared tag")))
    return "\n".join(lines) + "\n"
