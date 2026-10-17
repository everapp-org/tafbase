"""The SUT model loader — lane TAF/PLAN-taf-v1-001-01/A-1.

@concept CONCEPT-dsl-v1-001-01-the-sut-model
@concept CONCEPT-playwright-v1-001-01-the-locator-ladder

Implements SPEC-taf-v1-001-04: loads a sut.model.json document, validates
every clause, and reports every refusal as {"clause", "reason", "message"}.
A model with any refusal is not a model: load() raises ModelRefusal and the
emitters never see it. One form only — nothing is guessed.
"""

import json

# THE LOCATOR LADDER (CONCEPT-playwright-v1-001-01): a locator dict is valid when it
# carries at least one of these keys. Order is the preference; `css`/`xpath`
# are the last-resort rung and flag the element `fragile` in the manifest.
LOCATOR_RUNGS = ("role", "label", "text", "placeholder", "testid", "css", "xpath")

STEP_FORMS = ("click", "fill", "check", "select", "navigate", "wait-for",
              "api", "expect", "dwell", "wait-any", "maybe",
              "compare-screen")

REQUIRED_TOP = ("sut", "states", "journeys")


class ModelRefusal(Exception):
    """A model that failed validation. .refusals is the list the SPEC gives."""


def _refusal(clause, reason, message):
    return {"clause": clause, "reason": reason, "message": message}


def _pairs_no_dupes():
    """JSON object_pairs_hook: marks objects whose keys repeat, so a duplicate
    name is a :duplicate-name refusal instead of silent last-write-wins."""
    def hook(pairs):
        keys = [k for k, _ in pairs]
        d = dict(pairs)
        seen, dup = set(), set()
        for k in keys:
            if k in seen:
                dup.add(k)
            seen.add(k)
        if dup:
            d["__dupes__"] = sorted(dup)
        return d
    return hook


def _locator_ok(loc):
    return isinstance(loc, dict) and any(r in loc for r in LOCATOR_RUNGS)


def _check_locator(loc, clause, refusals):
    if not _locator_ok(loc):
        refusals.append(_refusal(
            clause, "bad-locator",
            "%s names no locator rung (role+name, label, text, placeholder, "
            "testid, css, xpath): %r" % (clause, loc)))


def _check_step(step, elements, states, endpoints, clause, refusals):
    """One step of an action's `do` or a journey's inline list."""
    if not isinstance(step, dict) or len(step) != 1:
        refusals.append(_refusal(clause, "unknown-step",
                                 "a step is one key with its args, not %r" % (step,)))
        return
    form, arg = next(iter(step.items()))
    if form not in STEP_FORMS:
        refusals.append(_refusal(clause, "unknown-step",
                                 "no step form %r (have %s)" % (form, ", ".join(STEP_FORMS))))
        return
    if form in ("click", "check", "select"):
        name = arg.get("element") if isinstance(arg, dict) else arg
        if name not in elements:
            refusals.append(_refusal(clause, "unknown-element",
                                     "%s names no element: %r" % (form, name)))
    elif form == "fill":
        name = arg.get("element") if isinstance(arg, dict) else None
        if name not in elements:
            refusals.append(_refusal(clause, "unknown-element",
                                     "fill names no element: %r" % (arg,)))
    elif form == "navigate":
        if arg not in states:
            refusals.append(_refusal(clause, "unknown-state",
                                     "navigate names no state: %r" % (arg,)))
    elif form == "wait-for":
        if not isinstance(arg, dict) or not (("element" in arg) ^ ("state" in arg)):
            refusals.append(_refusal(clause, "unknown-step",
                                     "wait-for takes {\"element\": x} or {\"state\": y}: %r" % (arg,)))
        elif "element" in arg and arg["element"] not in elements:
            refusals.append(_refusal(clause, "unknown-element",
                                     "wait-for names no element: %r" % arg["element"]))
        elif "state" in arg and arg["state"] not in states:
            refusals.append(_refusal(clause, "unknown-state",
                                     "wait-for names no state: %r" % arg["state"]))
    elif form == "api":
        name = arg if isinstance(arg, str) else (arg or {}).get("endpoint")
        if name not in endpoints:
            refusals.append(_refusal(clause, "unknown-endpoint",
                                     "api names no endpoint: %r" % (name,)))
    elif form == "dwell":
        if not isinstance(arg, (int, float)) or isinstance(arg, bool) or arg < 0:
            refusals.append(_refusal(clause, "bad-dwell",
                                     "dwell takes milliseconds, a number >= 0: %r" % (arg,)))
    elif form == "wait-any":
        if not isinstance(arg, list) or len(arg) < 2:
            refusals.append(_refusal(clause, "bad-wait-any",
                                     "wait-any takes a list of 2+ element names: %r" % (arg,)))
        else:
            for name in arg:
                if name not in elements:
                    refusals.append(_refusal(clause, "unknown-element",
                                           "wait-any names no element: %r" % (name,)))
    elif form == "compare-screen":
        if not isinstance(arg, str) or not arg:
            refusals.append(_refusal(clause, "bad-compare-screen",
                                     "compare-screen takes a snapshot name: %r" % (arg,)))
    elif form == "maybe":
        if not isinstance(arg, dict):
            refusals.append(_refusal(clause, "bad-maybe",
                                     "maybe wraps one step: %r" % (arg,)))
        else:
            _check_step(arg, elements, states, endpoints, clause + ".maybe", refusals)
    elif form == "expect":
        el = arg.get("element") if isinstance(arg, dict) else None
        if el is not None and el not in elements:
            refusals.append(_refusal(clause, "unknown-element",
                                     "expect names no element: %r" % el))


def _collect_dupes(node, path, refusals):
    if isinstance(node, dict):
        for d in node.get("__dupes__") or []:
            refusals.append(_refusal(path, "duplicate-name",
                                     "%r is declared twice in %s" % (d, path)))
        for k, v in node.items():
            if k != "__dupes__":
                _collect_dupes(v, "%s.%s" % (path, k) if path else k, refusals)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _collect_dupes(v, "%s[%d]" % (path, i), refusals)


def validate(doc):
    """PURE. The refusal list of a parsed model document; [] means the model
    is valid. Every refusal is {clause, reason, message}."""
    refusals = []

    if not isinstance(doc, dict):
        return [_refusal("document", "not-json", "a model is a JSON object")]

    _collect_dupes(doc, "", refusals)
    for key in REQUIRED_TOP:
        if key not in doc:
            refusals.append(_refusal("document", "missing-field",
                                     "the model needs %r" % key))
    if any(r["reason"] == "missing-field" and r["clause"] == "document" for r in refusals):
        return refusals

    sut = doc["sut"] if isinstance(doc["sut"], dict) else {}
    for key in ("name", "base-url"):
        if key not in sut:
            refusals.append(_refusal("sut", "missing-field",
                                     "sut needs %r" % key))

    states = doc.get("states") or {}
    elements = doc.get("elements") or {}
    actions = doc.get("actions") or {}
    journeys = doc.get("journeys") or {}
    endpoints = doc.get("endpoints") or {}

    if not states and not journeys:
        refusals.append(_refusal("document", "empty-model",
                                 "no states and no journeys: nothing to test"))

    for name, st in states.items():
        if not isinstance(st, dict) or "marker" not in st:
            refusals.append(_refusal("states.%s" % name, "missing-field",
                                     "a state needs a marker that proves arrival"))
        else:
            _check_locator(st["marker"], "states.%s.marker" % name, refusals)

    for name, el in elements.items():
        _check_locator(el, "elements.%s" % name, refusals)

    for name, ep in endpoints.items():
        if not isinstance(ep, dict) or "method" not in ep or "path" not in ep:
            refusals.append(_refusal("endpoints.%s" % name, "missing-field",
                                     "an endpoint needs method and path"))

    for name, act in actions.items():
        clause = "actions.%s" % name
        if not isinstance(act, dict):
            continue
        for key in ("from", "to"):
            if key in act and act[key] not in states:
                refusals.append(_refusal(clause, "unknown-state",
                                         "%s names no state: %r" % (key, act[key])))
        steps = act.get("do", [])
        for i, step in enumerate(steps):
            _check_step(step, elements, states, endpoints, "%s.do[%d]" % (clause, i), refusals)

    visited = set()
    for name, j in journeys.items():
        clause = "journeys.%s" % name
        if not isinstance(j, dict):
            continue
        start = j.get("start")
        if start is None:
            refusals.append(_refusal(clause, "missing-field", "a journey needs a start state"))
        elif start not in states:
            refusals.append(_refusal(clause, "unknown-state",
                                     "start names no state: %r" % start))
        else:
            visited.add(start)
        final = j.get("expect-final") or {}
        fstate = final.get("state")
        if fstate is not None:
            if fstate not in states:
                refusals.append(_refusal(clause, "unknown-state",
                                         "expect-final names no state: %r" % fstate))
            else:
                visited.add(fstate)

        steps = j.get("steps", [])
        kinds = {"action" if isinstance(s, str) else "inline" for s in steps}
        if len(kinds) > 1:
            refusals.append(_refusal(clause, "mixed-steps",
                                     "a journey names actions or writes steps inline, not both"))
        cursor = start if start in states else None
        for i, s in enumerate(steps):
            if isinstance(s, str):
                act = actions.get(s)
                if act is None:
                    refusals.append(_refusal(clause, "unknown-action",
                                             "journey names no action: %r" % s))
                    continue
                afrom, ato = act.get("from"), act.get("to")
                if afrom is not None and cursor is not None and afrom != cursor:
                    refusals.append(_refusal(clause, "edge-gap",
                                             "step %d starts at %r but the journey is at %r"
                                             % (i, afrom, cursor)))
                cursor = ato if ato is not None else cursor
                if cursor is not None:
                    visited.add(cursor)
            else:
                _check_step(s, elements, states, endpoints, "%s.steps[%d]" % (clause, i), refusals)

    for name in states:
        if name not in visited:
            refusals.append(_refusal("states.%s" % name, "unreachable",
                                     "no journey reaches state %r" % name))

    return refusals


def _strip_dupes_marks(node):
    if isinstance(node, dict):
        return {k: _strip_dupes_marks(v) for k, v in node.items() if k != "__dupes__"}
    if isinstance(node, list):
        return [_strip_dupes_marks(v) for v in node]
    return node


def loads(text):
    """Parse and validate model JSON. Returns the model dict; raises
    ModelRefusal carrying .refusals when the model is refused."""
    try:
        doc = json.loads(text, object_pairs_hook=_pairs_no_dupes())
    except ValueError as e:
        err = ModelRefusal("not JSON: %s" % e)
        err.refusals = [_refusal("document", "not-json", str(e))]
        raise err from None
    refusals = validate(doc)
    if refusals:
        err = ModelRefusal("model refused: %d problem(s)" % len(refusals))
        err.refusals = refusals
        raise err
    return _strip_dupes_marks(doc)


def load(path):
    """The model of the file at `path`, or ModelRefusal."""
    with open(path, "r", encoding="utf-8") as f:
        return loads(f.read())
