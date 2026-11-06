"""The actions module — journeys' building blocks."""

import json

from .common import *
from .steps import _emit_step


def _step_needs(step):
    """'env' | 'pool' | None — what a fill value reads at run time."""
    if not isinstance(step, dict) or len(step) != 1:
        return None
    form, arg = next(iter(step.items()))
    if form == "fill" and isinstance(arg, dict):
        v = str(arg.get("value", ""))
        if v.startswith("env:"):
            return "env"
        if v.startswith("env-pool:"):
            return "pool"
    if form == "maybe":
        return _step_needs(arg)
    return None


def _needs_of(steps, kind):
    return any(_step_needs(s) == kind for s in steps)


def _step_state(step):
    """The state a wait-for step waits on, through a maybe wrap."""
    if not isinstance(step, dict) or len(step) != 1:
        return None
    form, arg = next(iter(step.items()))
    if form == "maybe":
        return _step_state(arg)
    if form == "wait-for" and isinstance(arg, dict):
        return arg.get("state")
    return None


def _actions(m):
    if not m.get("actions"):
        return None
    uses_env = any(_needs_of(a.get("do", []), "env")
                   for a in m["actions"].values())
    bodies = []
    for name, act in m["actions"].items():
        body = _emit_steps(act.get("do", []), m["states"], m.get("endpoints") or {}, "    ")
        # Every action narrates itself — the label; the run reads as a story.
        title = json.dumps("→ " + act.get("title", name),
                           ensure_ascii=False)
        narrate = f"    taf_journal.note({title})\n"
        bodies.append(f"def {_py(name)}(page, base_url, soft=None):\n"
                      f"{narrate}{body or '    pass'}\n\n")
    text = "".join(bodies)
    states_used = sorted({_state_class(s) for act in m["actions"].values()
                          for st in act.get("do", [])
                          for s in [_step_state(st)] if s})
    lines = [_HEADER,
             '"""One function per declared action — the edges of the graph."""\n\n',
             "from pages import %s\n" % ", ".join(["ROUTES"] + states_used),
             "from playwright.sync_api import expect\n" if "expect(" in text else "",
             "import os\n" if uses_env else "",
             "import elements\n" if m.get("elements") else "",
             "import taf_journal\n\n"]
    lines.append(text)
    return "".join(lines)


def _emit_steps(steps, states, endpoints, pad):
    lines = []
    for step in steps:
        lines.extend(_emit_step(step, states, endpoints, pad))
    return "\n".join(lines)
