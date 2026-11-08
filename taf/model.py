"""The SUT model loader — lane TAF/PLAN-taf-v1-001-01/A-1.

@concept CONCEPT-dsl-v1-001-01-the-sut-model
@concept CONCEPT-qa-v1-002-01-the-locator-ladder
@concept CONCEPT-playwright-v1-002-01-semantic-locators
@concept CONCEPT-dsl-v1-015-01-the-env-value
@spec SPEC-taf-v1-003-01-the-browser-workbench

Implements SPEC-taf-v1-001-04: loads a sut.model.json document, validates
every clause, and reports every refusal as {"clause", "reason", "message"}.
A model with any refusal is not a model: load() raises ModelRefusal and the
emitters never see it. One form only — nothing is guessed.
"""

import json
import keyword
import re

from taf import ops

# THE LOCATOR LADDER (CONCEPT-qa-v1-002-01): a locator dict is valid when it
# carries at least one of these keys. Order is the preference; `css`/`xpath`
# are the last-resort rung and flag the element `fragile` in the manifest.
# Derived from taf/dsl/framework-spec.dsl — the validator is a spec
# consumer like the emitters (SPEC-taf-v1-002-02).
def _derive():
    from taf import spec as _s
    return _s.rungs(), _s.forms(), set(_s.spec()["contract"]["refusals"])

LOCATOR_RUNGS, STEP_FORMS, DECLARED_REFUSALS = _derive()

REQUIRED_TOP = ("sut", "states", "journeys")

SECURITY_MODES = ("shield", "audit", "raw", "off")
SECURITY_HUDS = ("docked", "toast-on-alert", "detached")
SECURITY_SINKS = (
    "password-read",
    "global-keylogger",
    "cookie-read",
    "storage-read",
    "unexpected-egress",
    "dynamic-eval",
    "clipboard-write",
    "overlay-trap",
    "phishing-marker",
)

_JAVA_JS_RESERVED = frozenset({
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "debugger", "default", "delete", "do",
    "double", "else", "enum", "export", "extends", "false", "final", "finally",
    "float", "for", "function", "goto", "if", "implements", "import", "in",
    "instanceof", "int", "interface", "let", "long", "native", "new", "null",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "true", "try", "typeof", "var", "void", "volatile", "while",
    "with", "yield",
})


def _valid_identifier(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name):
        return False
    if keyword.iskeyword(ops.snake(name)) or ops.camel(name) in _JAVA_JS_RESERVED:
        return False
    return True


class ModelRefusal(Exception):
    """A model that failed validation. .refusals is the list the SPEC gives."""


def _refusal(clause, reason, message):
    if reason not in DECLARED_REFUSALS:
        raise AssertionError("undeclared refusal reason: %s" % reason)
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
        val = arg.get("value") if isinstance(arg, dict) else None
        if isinstance(val, str) and val.startswith("env:") and not val[4:]:
            refusals.append(_refusal(clause, "bad-env",
                                     "env: names no variable: %r" % val))
        if isinstance(val, str) and val.startswith("env-pool:") and not val[9:]:
            refusals.append(_refusal(clause, "bad-env",
                                     "env-pool: names no variable: %r" % val))
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
        if isinstance(arg, dict):
            if not isinstance(arg.get("name"), str) or not arg["name"]:
                refusals.append(_refusal(
                    clause, "bad-compare-screen",
                    "compare-screen dict needs a snapshot name: %r" % (arg,)))
            mask = arg.get("mask") or []
            if not isinstance(mask, list):
                refusals.append(_refusal(
                    clause, "bad-compare-screen",
                    "compare-screen mask takes element names: %r" % (mask,)))
            else:
                for el in mask:
                    if el not in elements:
                        refusals.append(_refusal(
                            clause, "unknown-element",
                            "compare-screen mask names no element: %r" % el))
        elif not isinstance(arg, str) or not arg:
            refusals.append(_refusal(clause, "bad-compare-screen",
                                     "compare-screen takes a snapshot name or "
                                     "{name, mask}: %r" % (arg,)))
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


def _step_strings(node):
    """Every string inside a step's arg tree — where ${name}
    placeholders live."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _step_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _step_strings(v)


def _check_journey_extras(name, j, elements, refusals):
    """type / tags / examples — the clauses that sort a journey into
    its suite file and parametrize it."""
    clause = "journeys.%s" % name
    t = j.get("type")
    if t is not None and t not in ops.JOURNEY_TYPES:
        refusals.append(_refusal(
            clause, "bad-journey-type",
            "type is one of %s, not %r" % (", ".join(ops.JOURNEY_TYPES), t)))
    tags = j.get("tags") or []
    if not isinstance(tags, list) or any(not _valid_identifier(x) for x in tags):
        refusals.append(_refusal(
            "%s.tags" % clause, "bad-identifier",
            "tags is a list of identifiers (smoke, regression, ...): %r" % (tags,)))
    steps = j.get("steps", [])
    jtype = ops.journey_type({"journeys": {name: j}}, name)
    if jtype == "api":
        if not all(isinstance(s, dict) and ops._step_api_safe(s) for s in steps):
            refusals.append(_refusal(
                clause, "bad-journey-type",
                "an api journey writes inline browserless steps only "
                "(api, dwell, expect on saved values)"))
        if (j.get("expect-final") or {}).get("state") is not None:
            refusals.append(_refusal(
                "%s.expect-final" % clause, "bad-journey-type",
                "an api journey has no page — expect-final cannot name a state"))
    rows = j.get("examples")
    used = {k for s in steps for txt in _step_strings(s)
            for k in ops.placeholder_keys(txt)}
    if rows is not None:
        if not all(isinstance(s, dict) for s in steps):
            refusals.append(_refusal(
                "%s.examples" % clause, "bad-examples",
                "examples parametrize inline steps — a journey naming "
                "actions cannot take rows"))
        if not isinstance(rows, list) or not rows \
                or not all(isinstance(r, dict) and r for r in rows):
            refusals.append(_refusal(
                "%s.examples" % clause, "bad-examples",
                "examples is a non-empty list of row objects: %r" % (rows,)))
        else:
            keys = set(rows[0])
            for i, r in enumerate(rows):
                if set(r) != keys:
                    refusals.append(_refusal(
                        "%s.examples[%d]" % (clause, i), "bad-examples",
                        "row keys differ from the first row: %s vs %s"
                        % (sorted(r), sorted(keys))))
                for k, v in r.items():
                    if not _valid_identifier(k):
                        refusals.append(_refusal(
                            "%s.examples" % clause, "bad-identifier",
                            "example key %r is not a valid identifier" % k))
                    if not isinstance(v, (str, int, float, bool)):
                        refusals.append(_refusal(
                            "%s.examples[%d]" % (clause, i), "bad-examples",
                            "row values are scalars, not %r" % (v,)))
            missing = used - keys
            if missing:
                refusals.append(_refusal(
                    "%s.examples" % clause, "bad-examples",
                    "steps reference ${%s} but no row declares it"
                    % "}, ${".join(sorted(missing))))
    elif used:
        refusals.append(_refusal(
            clause, "bad-examples",
            "${%s} placeholders need an examples table"
            % "}, ${".join(sorted(used))))


def _check_security(sec, refusals):
    """Validate the optional top-level `security` block (SPEC-taf-v1-003-01)."""
    if not isinstance(sec, dict):
        refusals.append(_refusal(
            "security", "bad-security",
            "security must be a JSON object: %r" % (sec,)))
        return
    allowed_keys = {
        "mode", "hud", "allowed-origins",
        "third-party-patterns", "forbid-sinks",
    }
    for k in sec:
        if k != "__dupes__" and k not in allowed_keys:
            refusals.append(_refusal(
                "security.%s" % k, "bad-security",
                "unknown security field %r (allowed: %s)"
                % (k, ", ".join(sorted(allowed_keys)))))
    mode = sec.get("mode")
    if mode is not None and mode not in SECURITY_MODES:
        refusals.append(_refusal(
            "security.mode", "bad-security",
            "security.mode must be one of %s, not %r"
            % (", ".join(SECURITY_MODES), mode)))
    hud = sec.get("hud")
    if hud is not None and hud not in SECURITY_HUDS:
        refusals.append(_refusal(
            "security.hud", "bad-security",
            "security.hud must be one of %s, not %r"
            % (", ".join(SECURITY_HUDS), hud)))
    for list_key in ("allowed-origins", "third-party-patterns"):
        val = sec.get(list_key)
        if val is not None:
            if not isinstance(val, list) or not all(isinstance(x, str) and x for x in val):
                refusals.append(_refusal(
                    "security.%s" % list_key, "bad-security",
                    "security.%s must be a list of non-empty strings: %r"
                    % (list_key, val)))
    sinks = sec.get("forbid-sinks")
    if sinks is not None:
        if not isinstance(sinks, list) or not all(isinstance(x, str) for x in sinks):
            refusals.append(_refusal(
                "security.forbid-sinks", "bad-security",
                "security.forbid-sinks must be a list of sink names: %r" % (sinks,)))
        else:
            for s in sinks:
                if s not in SECURITY_SINKS:
                    refusals.append(_refusal(
                        "security.forbid-sinks", "bad-security",
                        "unknown security sink %r (have %s)"
                        % (s, ", ".join(SECURITY_SINKS))))


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

    for sec_name, sec_map in (("states", states), ("elements", elements),
                              ("actions", actions), ("journeys", journeys),
                              ("endpoints", endpoints)):
        if isinstance(sec_map, dict):
            for k in sec_map:
                if not _valid_identifier(k):
                    refusals.append(_refusal(
                        f"{sec_name}.{k}", "bad-identifier",
                        f"'{k}' is not a valid identifier"))

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
        _check_journey_extras(name, j, elements, refusals)
        jtype = ops.journey_type({"journeys": {name: j}}, name)
        start = j.get("start")
        if start is None and jtype != "api":
            refusals.append(_refusal(clause, "missing-field", "a journey needs a start state"))
        if start is None:
            cursor = None
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
                for inner in act.get("do") or []:
                    if isinstance(inner, dict):
                        nav = inner.get("navigate")
                        if nav in states:
                            visited.add(nav)
                        wf = inner.get("wait-for")
                        if isinstance(wf, dict) and wf.get("state") in states:
                            visited.add(wf["state"])
            else:
                _check_step(s, elements, states, endpoints, "%s.steps[%d]" % (clause, i), refusals)
                if isinstance(s, dict):
                    nav = s.get("navigate")
                    if nav in states:
                        cursor = nav
                        visited.add(nav)
                    wf = s.get("wait-for")
                    if isinstance(wf, dict) and wf.get("state") in states:
                        visited.add(wf["state"])
        if fstate is not None and fstate in states and steps and cursor in states and cursor != fstate:
            refusals.append(_refusal(
                "%s.expect-final" % clause, "edge-gap",
                "journey ends at state %r but expect-final names %r" % (cursor, fstate)))

    auth = sut.get("auth")
    if auth is not None:
        if not isinstance(auth, dict) or "action" not in auth:
            refusals.append(_refusal("sut.auth", "missing-field",
                                     "auth needs an action"))
        elif auth["action"] not in actions:
            refusals.append(_refusal("sut.auth", "unknown-action",
                                     "auth names no action: %r" % auth["action"]))
        else:
            act = actions[auth["action"]]
            if "from" not in act:
                refusals.append(_refusal(
                    "sut.auth", "bad-auth",
                    "the auth action needs a from state — the run "
                    "navigates there to sign in"))
            else:
                visited.add(act["from"])
                if act.get("to"):
                    visited.add(act["to"])

    if "security" in doc:
        _check_security(doc["security"], refusals)

    for name in states:
        if name not in visited:
            refusals.append(_refusal("states.%s" % name, "unreachable",
                                     "no journey reaches state %r" % name))

    return refusals


def env_needs(m):
    """The env:/env-pool: variables a run reads at run time — the needs
    of the declared journeys, not of actions nothing walks. The model
    names the need; the environment supplies the value.

    @concept CONCEPT-dsl-v1-015-01-the-env-value
    """
    needs = set()
    actions = m.get("actions") or {}

    def scan(step):
        if not isinstance(step, dict) or len(step) != 1:
            return
        form, arg = next(iter(step.items()))
        if form == "fill" and isinstance(arg, dict):
            v = arg.get("value")
            if isinstance(v, str):
                if v.startswith("env:"):
                    needs.add(v[4:])
                elif v.startswith("env-pool:"):
                    needs.add(v[9:])
        elif form == "maybe" and isinstance(arg, dict):
            scan(arg)

    for j in (m.get("journeys") or {}).values():
        if not isinstance(j, dict):
            continue
        for s in j.get("steps", []):
            if isinstance(s, str):
                for st in (actions.get(s) or {}).get("do", []):
                    scan(st)
            else:
                scan(s)
    auth = ((m.get("sut") or {}).get("auth") or {}).get("action")
    if auth:
        for st in (actions.get(auth) or {}).get("do", []):
            scan(st)
    return sorted(needs)


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
