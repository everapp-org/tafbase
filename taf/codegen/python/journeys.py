"""test_journeys.py — one test per model journey."""

import json

from .common import *
from .actions import _needs_of
from .steps import _emit_step


def _journeys(m):
    lines = [_HEADER,
             '"""One test per declared journey — arrange, act, assert.\n\n'
             "@concept CONCEPT-testing-v1-001-01-arrange-act-assert\n"
             "@concept CONCEPT-qa-v1-001-01-arrange-act-assert\n"
             "@concept CONCEPT-istqb-v1-010-01-state-transition-testing\n"
             '"""\n\n']
    imports = ["import actions"]
    inline = [s for j in m["journeys"].values() for s in j.get("steps", [])]
    if _needs_of(inline, "env"):
        imports.append("import os")
    if _needs_of(inline, "pool"):
        imports.append("import taf_journal")
    if m.get("elements"):
        imports.append("import elements")
    imports.append("from pages import %s" % ", ".join(
        _state_class(n) for n in m["states"]))
    lines.append("\n".join(imports) + "\n\n")
    for name, j in m["journeys"].items():
        start = j["start"]
        body = [f"    # arrange\n"
                f"    sut = {_state_class(start)}(page)\n"
                f"    sut.goto(base_url)\n"
                f"    sut.expect_arrived()\n"
                f"    # act\n"]
        for op, arg in ops.journey_ops(m, name)[1:]:
            if op == "run":
                act = m["actions"][arg]
                body.append(f"    actions.{_py(arg)}(page, base_url, soft)\n")
            elif op == "step":
                body.append("\n".join(_emit_step(arg, m["states"], m.get("endpoints") or {}, "    ")) + "\n")
            elif op == "assert-marker":
                body.append(f"    {_state_class(arg)}(page).expect_arrived()\n")
            elif op == "assert-final":
                body.append("    # assert\n")
                body.append(f"    {_state_class(arg)}(page).expect_arrived()\n")
        if not any(op == "assert-final" for op, _ in ops.journey_ops(m, name)):
            body.append("    # assert\n")
        lines.append(f"def {ops.test_name_snake(name)}(page, base_url, soft):\n{''.join(body)}\n")
    return "".join(lines)
