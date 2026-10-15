"""The canonical emission plan — lane TAF/PLAN-taf-v1-001-01/D-4.

@concept CONCEPT-taf-v1-002-01-the-sut-model

The parity contract of SPEC-taf-v1-001-01 says two emitters produce the
same suite modulo language idioms. "Same" is made concrete here: every
emitter derives its work from these canonical ops — the naming, the
assertion sequence of a journey, the locator rung — and renders only
syntax. Semantics cannot drift between languages; only spelling can.
"""

import re


def snake(name):
    """model name -> python symbol: open-tot -> open_tot."""
    return re.sub(r"[^0-9a-zA-Z_]", "_", name)


def camel(name):
    """model name -> java symbol: open-tot -> openTot, board-to-tot -> boardToTot."""
    parts = re.split(r"[^0-9a-zA-Z]+", name)
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:] if p)


def state_class(name):
    """model state -> page-object class name: board -> BoardPage."""
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[^0-9a-zA-Z]+", name)) + "Page"


def test_name_snake(journey):
    return "test_" + snake(journey)


def test_name_camel(journey):
    n = camel(journey)
    return n


def locator_rung(loc):
    """The one rung of the ladder a locator sits on, in preference order:
    (rung, args-dict). `css`/`xpath` is the flagged last resort."""
    for rung in ("role", "label", "text", "placeholder", "testid"):
        if rung in loc:
            return rung, loc
    if "xpath" in loc:
        return "xpath", loc
    return "css", loc


def journey_ops(model, name):
    """The assertion sequence of a journey, canonical:
    [("arrive", start), ("run", action)*, ("assert-marker", to)*,
     ("step", inline)*, ("assert-final", state)?]
    Both emitters render exactly this sequence."""
    j = model["journeys"][name]
    ops = [("arrive", j["start"])]
    inline = all(isinstance(s, dict) for s in j.get("steps", []))
    for s in j.get("steps", []):
        if inline:
            ops.append(("step", s))
        else:
            ops.append(("run", s))
            to = model["actions"][s].get("to")
            if to:
                ops.append(("assert-marker", to))
    final = (j.get("expect-final") or {}).get("state")
    if final:
        ops.append(("assert-final", final))
    return ops


def manifest(model):
    """The manifest dict — identical for every emitter by construction
    (it names no language)."""
    tests = []
    for name, j in model["journeys"].items():
        used = [s for s in j.get("steps", []) if isinstance(s, str)]
        tests.append({
            "test": test_name_snake(name),
            "journey": name,
            "states": [j["start"]] + [model["actions"][s].get("to") for s in used
                                      if model["actions"][s].get("to")],
            "actions": used,
        })
    return {"sut": model["sut"]["name"], "tests": tests}
