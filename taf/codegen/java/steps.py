"""Step-form generators — dsl vocabulary → Java lines."""

import json

from .common import *


def _caption(form, arg):
    """What the .srt says at this step — names only, never values."""
    name = (lambda a: a.get("element") if isinstance(a, dict) else a)
    if form == "navigate":
        return "goto %s" % arg
    if form in ("click", "check", "select"):
        return "%s %s" % (form, name(arg))
    if form == "fill":
        return "fill %s" % name(arg)
    if form == "wait-for":
        return "wait-for %s" % (arg.get("state") or arg.get("element"))
    if form == "api":
        return "api %s" % (arg if isinstance(arg, str)
                           else arg.get("endpoint"))
    if form == "dwell":
        return "dwell %sms" % arg
    if form == "wait-any":
        return "wait-any %s" % ", ".join(arg)
    if form == "compare-screen":
        return "compare-screen %s" % arg
    if form == "save":
        return "save %s" % arg
    if form == "expect":
        return "expect %s" % (arg.get("element") or arg.get("value")
                              or arg.get("saved") or "?")
    return form


def _emit_step(step, endpoints, pad):
    form, arg = next(iter(step.items()))
    if form != "maybe":
        # every step captions itself — narration rides the .srt
        return ([f'{pad}try {{ TafJournal.note({_q(_caption(form, arg))}); }}'
                 f' catch (java.io.IOException ignored) {{}}'] +
                _emit_step_body(step, endpoints, pad))
    return _emit_step_body(step, endpoints, pad)


def _emit_step_body(step, endpoints, pad):
    """One model step → Java lines, spelled by
    taf/dsl/framework-spec.dsl."""
    form, arg = next(iter(step.items()))
    e = _forms()[form]
    darg = arg if isinstance(arg, dict) else {}
    e = _variant_entry(e, [k for k in darg if k != "soft"])

    if form == "navigate":
        return [pad + _sp(e, arg=arg, state_class=_state_class(arg))]
    if form in ("click", "check"):
        name = arg.get("element") if isinstance(arg, dict) else arg
        return [pad + _sp(e, **{"j:name": _j(name)})]
    if form == "select":
        name = arg.get("element") if isinstance(arg, dict) else arg
        val = _q(arg["value"]) if isinstance(arg, dict) and "value" in arg else ""
        return [pad + _sp(e, **{"j:name": _j(name), "val_quoted": val})]
    if form == "fill":
        v = arg.get("value", "")
        if isinstance(v, str) and v.startswith("env-pool:"):
            # env-pool:NAME — a list in the env; one value spent per call.
            val = 'TafJournal.envPool(%s)' % _q(v[9:])
        elif isinstance(v, str) and v.startswith("env:"):
            # env:NAME — the model names the need; the run reads the
            # variable. The secret is never in emitted code.
            nm = _esc(v[4:])
            val = ('java.util.Objects.requireNonNull('
                   'System.getenv("%s"), "%s is not set")' % (nm, nm))
        else:
            val = _q(v)
        return [pad + _sp(e, **{"j:name": _j(arg["element"]),
                                "value_expr": val})]
    if form == "wait-for":
        kw = {"j:element": _j(arg.get("element", ""))}
        if "state" in arg:
            kw["state_class"] = _state_class(arg["state"])
        return [pad + _sp(e, **kw)]
    if form == "api":
        name = arg if isinstance(arg, str) else arg.get("endpoint")
        args = {} if isinstance(arg, str) else arg.get("args") or {}
        ep = endpoints[name]
        path, status = ep["path"], (ep.get("expect") or {}).get("status", 200)
        pexpr = _q(path) + "".join(
            '.replace("{%s}", %s)' % (_esc(k), _q(v))
            for k, v in args.items())
        kw = {"method_lower": ep["method"].lower(),
              "pexpr": pexpr, "status": status}
        tpl = e["spell"]["java"]
        lines = [pad + _sub(tpl[0], kw), pad + _sub(tpl[1], kw)]
        if isinstance(arg, dict) and arg.get("save"):
            for k, jpath in arg["save"].items():
                lines.append(pad + _sub(tpl[2],
                {"save_key": _esc(k), "jsonpath": _jsonpath(jpath)}))
        return lines
    if form == "dwell":
        # A pause for a watching human — observation, not synchronization.
        return [pad + _sp(e, arg=arg)]
    if form == "wait-any":
        locs = f"Elements.{_j(arg[0])}(page)" + "".join(
            f".or(Elements.{_j(n)}(page))" for n in arg[1:])
        return [pad + _sp(e, loc_chain=locs)]
    if form == "compare-screen":
        return [pad + _sp(e, arg=_esc(arg))]
    if form == "maybe":
        # An ifPresent step: try it, never fail.
        inner = _emit_step(arg, endpoints, pad + "    ")
        w = e["wrap"]["java"]
        return ([pad + x for x in w["pre"]] + inner +
                [pad + x for x in w["post"]])
    if form == "expect":
        if isinstance(arg, dict) and "element" in arg:
            el = f"Elements.{_j(arg['element'])}(page)"
            if arg.get("soft"):
                # Collect into the SoftChecks stack; @AfterEach flushes
                # once — the run shows every failed check.
                inner = _emit_step({"expect": {k: v for k, v in arg.items()
                                               if k != "soft"}},
                                   endpoints, pad + "        ")
                stmt = inner[-1].strip()
                return [
                    f"{pad}if (soft != null) {{",
                    f'{pad}    soft.check({_q(arg["element"])}, () -> {stmt[:-1]});',
                    f"{pad}}} else {{",
                    f"{pad}    try {{ {stmt}",
                    f'{pad}    }} catch (AssertionError e) {{ System.out.println("soft expect failed: " + e.getMessage()); }}',
                    f"{pad}}}"]
            kw = {"el": el}
            if "text" in arg:
                kw["text"] = _esc(arg["text"])
            if "count" in arg:
                kw["count"] = arg["count"]
            return [pad + _sp(e, **kw)]
        if isinstance(arg, dict) and "value" in arg:
            return [pad + _sp(e, value=_esc(arg["value"]),
                              equals=json.dumps(arg.get("equals")))]
    return [f"{pad}// unsupported step: {form}"]
