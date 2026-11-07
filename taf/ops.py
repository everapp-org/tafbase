"""The canonical emission plan — lane TAF/PLAN-taf-v1-001-01/D-4.

@concept CONCEPT-dsl-v1-001-01-the-sut-model

The parity contract of SPEC-taf-v1-001-04 says two emitters produce the
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
    """The one rung of the ladder a locator sits on, in the spec's
    declared preference order: (rung, args-dict). The last rung in
    the spec is the fallback."""
    from taf import spec as _s
    rungs = _s.rungs()
    for rung in rungs[:-1]:
        if rung in loc:
            return rung, loc
    return rungs[-1], loc


JOURNEY_TYPES = ("ui", "api", "visual", "walk")

# Steps a browserless api journey may run — anything else needs a Page.
_API_FORMS = frozenset({"api", "dwell"})

_PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z][A-Za-z0-9_-]*)\}")


def placeholder_keys(v):
    """The ${name} refs inside a string value — the example row keys a
    parameterized journey substitutes at run time."""
    return _PLACEHOLDER_RE.findall(v) if isinstance(v, str) else []


def _step_api_safe(step):
    """True when the step needs no browser Page: api calls, dwells,
    expects on saved values — maybe-wrapped included."""
    if not isinstance(step, dict) or len(step) != 1:
        return False
    form, arg = next(iter(step.items()))
    if form in _API_FORMS:
        return True
    if form == "expect":
        return isinstance(arg, dict) and "value" in arg
    if form == "maybe":
        return _step_api_safe(arg)
    return False


def journey_type(model, name):
    """ui | api | visual | walk — the suite file a journey lands in.
    An explicit `type` wins; else a journey of only browserless steps
    is api; the rest are ui. `walk` journeys are marked by taf walk."""
    j = model["journeys"][name]
    t = j.get("type")
    if t:
        return t
    steps = j.get("steps", [])
    if steps and all(isinstance(s, dict) for s in steps):
        if all(_step_api_safe(s) for s in steps):
            return "api"
        if all("compare-screen" in s or "dwell" in s for s in steps):
            return "visual"
    return "ui"


def journey_tags(model, name):
    """Native runner tags: the journey's declared tags plus its type —
    every api journey answers to @api, every walk to @walk."""
    j = model["journeys"][name]
    declared = [t for t in (j.get("tags") or [])
                if isinstance(t, str)]
    return sorted(set(declared) | {journey_type(model, name)})


def journey_examples(model, name):
    """The example rows a parameterized journey emits a test per, or []."""
    return model["journeys"][name].get("examples") or []


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
        states = ([j["start"]] if j.get("start") else []) + [
            model["actions"][s].get("to") for s in used
            if model["actions"][s].get("to")]
        tests.append({
            "test": test_name_snake(name),
            "journey": name,
            "type": journey_type(model, name),
            "tags": journey_tags(model, name),
            "states": states,
            "actions": used,
        })
    return {"sut": model["sut"]["name"], "tests": tests}


def suite_info(model, lang, framework, env_needs):
    """taf.suite.json — the run descriptor `taf run` reads: which
    toolchain, which framework dir the suite binds to, the SUT's
    base-url and the env needs the preflight must check. The manifest
    stays lang-agnostic; this file is the lane's own metadata."""
    types = {}
    for name in model["journeys"]:
        t = journey_type(model, name)
        types[t] = types.get(t, 0) + 1
    return {"sut": model["sut"]["name"],
            "lang": lang,
            "framework": framework,
            "base-url": model["sut"]["base-url"],
            "env-needs": sorted(env_needs),
            "journey-types": types}
