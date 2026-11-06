"""journeys.spec.ts — one test per model journey (TypeScript)."""

import json

from .common import *
from .actions import _saves
from .steps import _emit_step


def _journeys(m):
    lines = [
        _HEADER,
        "// @concept CONCEPT-testing-v1-001-01-arrange-act-assert\n",
        "// @concept CONCEPT-qa-v1-001-01-arrange-act-assert\n\n",
        "import { test, expect } from \"./fixtures\";\n",
        "import { %s } from \"./pages\";\n" % ", ".join(ops.state_class(s) for s in m["states"]),
    ]
    if m.get("actions"):
        lines.append("import * as actions from \"./actions\";\n")
    if m.get("elements"):
        lines.append("import * as elements from \"./elements\";\n")
    lines.append("import { tafJournal } from \"./taf_journal\";\n\n")

    for name, j in m["journeys"].items():
        start = j["start"]
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
                body.append("\n".join(_emit_step(arg, m["states"], m.get("endpoints") or {}, "  ")) + "\n")
            elif op == "assert-marker":
                body.append(f"  await new {ops.state_class(arg)}(page).expectArrived();\n")
            elif op == "assert-final":
                body.append("  // assert\n")
                body.append(f"  await new {ops.state_class(arg)}(page).expectArrived();\n")
        if not any(op == "assert-final" for op, _ in ops.journey_ops(m, name)):
            body.append("  // assert\n")
        lines.append(f"test(\"{ops.test_name_camel(name)}\", async ({{ page, baseUrl, soft }}) => {{\n{''.join(body)}}});\n\n")
    return "".join(lines)
