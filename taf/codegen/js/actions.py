"""The actions module — journeys' building blocks (JavaScript ESM)."""

import json

from .common import *
from .steps import _emit_step


def _saves(steps):
    return any(isinstance(s.get("api"), dict) and s["api"].get("save")
               for s in steps if isinstance(s, dict) and "api" in s)


def _actions(m):
    if not m.get("actions"):
        return None
    bodies = []
    for name, act in m["actions"].items():
        steps = act.get("do", [])
        body_lines = []
        for step in steps:
            body_lines.extend(_emit_step(step, m["states"], m.get("endpoints") or {}, "  "))
        body = "\n".join(body_lines)
        decl = "  const saved = {};\n" if _saves(steps) else ""
        title = json.dumps("→ " + act.get("title", name), ensure_ascii=False)
        narrate = f"  tafJournal.note({title});\n"
        bodies.append(
            f"/**\n"
            f" * @param {{import(\"@playwright/test\").Page}} page\n"
            f" * @param {{string}} baseUrl\n"
            f" * @param {{import(\"./fixtures.mjs\").SoftChecks}} [soft]\n"
            f" */\n"
            f"export async function {ops.camel(name)}(page, baseUrl, soft) {{\n"
            f"{narrate}{decl}{body or '  // no steps'}\n"
            f"}}\n\n"
        )
    text = "".join(bodies)
    lines = [
        _HEADER,
        "import { expect } from \"@playwright/test\";\n",
        "import { %s } from \"./pages.mjs\";\n" % ", ".join(["ROUTES"] + [ops.state_class(s) for s in m["states"]]),
    ]
    if m.get("elements"):
        lines.append("import * as elements from \"./elements.mjs\";\n")
    lines.append("import { tafJournal } from \"./taf_journal.mjs\";\n\n")
    lines.append(text)
    return "".join(lines)
