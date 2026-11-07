"""The spec files — one per test type: journeys.spec.ts (ui),
api.spec.ts (browserless), visual.spec.ts (golden grammar),
walks.spec.ts (seeded graph walks)."""

import json

from .common import *
from .actions import _saves
from .steps import _emit_step

_SUITE_FILES = {"ui": "journeys.spec.ts", "api": "api.spec.ts",
                "visual": "visual.spec.ts", "walk": "walks.spec.ts"}

_SUITE_TITLES = {
    "ui": "One test per declared journey — arrange, act, assert.",
    "api": "Browserless endpoint journeys — no Page ever opens.",
    "visual": "Golden-screenshot regression — `taf promote` approves baselines.",
    "walk": "Seeded graph walks — exploratory, deterministic by seed.",
}

_FIXTURE_ARGS = {"ui": "{ page, baseUrl, soft }",
                 "visual": "{ page, baseUrl, soft }",
                 "walk": "{ page, baseUrl, soft }",
                 "api": "{ request, baseUrl, soft }"}


def suite_filename(jtype):
    return _SUITE_FILES[jtype]


def _tag_opt(m, name):
    """The playwright { tag: [...] } option from journey.tags — native
    filtering: `--grep @smoke`."""
    tags = ops.journey_tags(m, name)
    return "{ tag: [%s] }, " % ", ".join(
        json.dumps("@" + t) for t in tags) if tags else ""


def _body_ui(m, name, j):
    start = j["start"]
    ctx = {"visual": ops.journey_type(m, name) == "visual"}
    if ops.journey_examples(m, name):
        ctx["row"] = "example"
    body = [
        "  // arrange\n",
        f"  const sut = new {ops.state_class(start)}(page);\n",
        "  await sut.goto(baseUrl);\n",
        "  await sut.expectArrived();\n",
        "  // act\n"
    ]
    inline_steps = [s for s in j.get("steps", []) if isinstance(s, dict)]
    if _saves(inline_steps):
        body.append("  const saved: Record<string, any> = {};\n")
    for op, arg in ops.journey_ops(m, name)[1:]:
        if op == "run":
            body.append(f"  await actions.{ops.camel(arg)}(page, baseUrl, soft);\n")
        elif op == "step":
            body.append("\n".join(_emit_step(
                arg, m["states"], m.get("endpoints") or {}, "  ", ctx)) + "\n")
        elif op == "assert-marker":
            body.append(f"  await new {ops.state_class(arg)}(page).expectArrived();\n")
        elif op == "assert-final":
            body.append("  // assert\n")
            body.append(f"  await new {ops.state_class(arg)}(page).expectArrived();\n")
    if not any(op == "assert-final" for op, _ in ops.journey_ops(m, name)):
        body.append("  // assert\n")
    return body


def _body_api(m, name, j):
    ctx = {"api": True}
    if ops.journey_examples(m, name):
        ctx["row"] = "example"
    body = []
    inline = [s for s in j.get("steps", []) if isinstance(s, dict)]
    if _saves(inline):
        body.append("  const saved: Record<string, any> = {};\n")
    for s in inline:
        body.append("\n".join(_emit_step(
            s, m["states"], m.get("endpoints") or {}, "  ", ctx)) + "\n")
    return body or ["  // no steps\n"]


def _test_fn(m, name, jtype):
    j = m["journeys"][name]
    rows = ops.journey_examples(m, name)
    sig = _FIXTURE_ARGS[jtype]
    tag = _tag_opt(m, name)
    body = "".join(_body_api(m, name, j) if jtype == "api"
                   else _body_ui(m, name, j))
    title = ops.test_name_camel(name)
    if rows:
        return (
            "const %sExamples: Record<string, unknown>[] = %s;\n"
            "for (const [i, example] of %sExamples.entries()) {\n"
            "  test(%s + \"[\" + i + \"]\", %sasync (%s) => {\n%s});\n"
            "}\n\n"
            % (ops.camel(name), json.dumps(rows), ops.camel(name),
               json.dumps(title), tag, sig, body))
    return ("test(%s, %sasync (%s) => {\n%s});\n\n"
            % (json.dumps(title), tag, sig, body))


def _imports(m, names, jtype):
    inline = [s for name in names
              for s in m["journeys"][name].get("steps", [])
              if isinstance(s, dict)]
    imports = ['import { test, expect } from "./fixtures";']
    if inline:
        imports.append('import { tafJournal } from "%s";' % _fw("taf_journal"))
    if jtype == "api":
        return "\n".join(imports) + "\n\n"
    uses_actions = any(isinstance(s, str)
                       for name in names
                       for s in m["journeys"][name].get("steps", []))
    if uses_actions and m.get("actions"):
        imports.append('import * as actions from "./actions";')
    if m.get("elements"):
        imports.append('import * as elements from "./elements";')
    if jtype == "visual":
        imports.append('import * as visual from "%s";' % _fw("visual"))
    states_needed = {m["journeys"][n].get("start") for n in names}
    for name in names:
        for op, arg in ops.journey_ops(m, name):
            if op in ("assert-marker", "assert-final"):
                states_needed.add(arg)
    states_needed.discard(None)
    if states_needed:
        imports.append('import { %s } from "./pages";' % ", ".join(
            sorted(ops.state_class(s) for s in states_needed)))
    return "\n".join(imports) + "\n\n"


def _suite_file(m, jtype):
    """The emitted spec for one type, or None when the model has no
    journeys of it."""
    names = [n for n in m["journeys"] if ops.journey_type(m, n) == jtype]
    if not names:
        return None
    lines = [
        _HEADER,
        "// @concept CONCEPT-testing-v1-001-01-arrange-act-assert\n",
        "// @concept CONCEPT-qa-v1-001-01-arrange-act-assert\n",
        "// %s\n\n" % _SUITE_TITLES[jtype],
        _imports(m, names, jtype),
    ]
    for name in names:
        lines.append(_test_fn(m, name, jtype))
    return "".join(lines)
