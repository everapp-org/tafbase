"""The actions module — journeys' building blocks (TypeScript)."""

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
        decl = "  const saved: Record<string, any> = {};\n" if _saves(steps) else ""
        title = json.dumps("→ " + act.get("title", name), ensure_ascii=False)
        narrate = f"  tafJournal.note({title});\n"
        bodies.append(
            f"export async function {ops.camel(name)}(page: Page, baseUrl: string, soft?: SoftChecks): Promise<void> {{\n"
            f"{narrate}{decl}{body or '  // no steps'}\n"
            f"}}\n\n"
        )
    text = "".join(bodies)
    lines = [
        _HEADER,
        "import { Page, expect } from \"@playwright/test\";\n",
        "import { %s } from \"./pages\";\n" % ", ".join(["ROUTES"] + [ops.state_class(s) for s in m["states"]]),
    ]
    if m.get("elements"):
        lines.append("import * as elements from \"./elements\";\n")
    lines.append("import { tafJournal } from \"%s\";\n" % _fw("taf_journal"))
    lines.append("import type { SoftChecks } from \"%s\";\n\n" % _fw("soft-checks"))
    lines.append(text)
    return "".join(lines)
