"""Step-form generators — dsl vocabulary → TypeScript lines."""

import json

from .common import *


def _caption(form, arg):
    """What the .srt says at this step — element/state names only,
    never values: a caption must not leak a secret."""
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


def _emit_step(step, states, endpoints, pad):
    form, arg = next(iter(step.items()))
    if form != "maybe":
        return ([f"{pad}tafJournal.note({json.dumps(_caption(form, arg))});"] +
                _emit_step_body(step, states, endpoints, pad))
    return _emit_step_body(step, states, endpoints, pad)


def _emit_step_body(step, states, endpoints, pad):
    """One model step → TypeScript lines, spelled by
    taf/dsl/framework-spec.dsl."""
    form, arg = next(iter(step.items()))
    e = _forms()[form]
    darg = arg if isinstance(arg, dict) else {}
    e = _variant_entry(e, [k for k in darg if k != "soft"])

    if form == "navigate":
        return [pad + _sp(e, arg=_esc(arg))]

    if form in ("click", "check"):
        name = arg.get("element") if isinstance(arg, dict) else arg
        return [pad + _sp(e, **{"j:name": ops.camel(name)})]

    if form == "select":
        name = arg.get("element") if isinstance(arg, dict) else arg
        val = arg["value"] if isinstance(arg, dict) and "value" in arg else ""
        return [pad + _sp(e, **{"j:name": ops.camel(name), "val_quoted": json.dumps(val)})]

    if form == "fill":
        v = arg.get("value", "")
        if isinstance(v, str) and v.startswith("env-pool:"):
            val = f'tafJournal.envPool({json.dumps(v[9:])})'
        elif isinstance(v, str) and v.startswith("env:"):
            val = f'process.env[{json.dumps(v[4:])}]!'
        else:
            val = json.dumps(v)
        return [pad + _sp(e, **{"j:name": ops.camel(arg["element"]), "value_expr": val})]

    if form == "wait-for":
        kw = {"j:element": ops.camel(arg.get("element", ""))}
        if "state" in arg:
            kw["state_class"] = ops.state_class(arg["state"])
        return [pad + _sp(e, **kw)]

    if form == "api":
        name = arg if isinstance(arg, str) else arg.get("endpoint")
        args = {} if isinstance(arg, str) else arg.get("args") or {}
        ep = endpoints[name]
        path, status = ep["path"], (ep.get("expect") or {}).get("status", 200)
        pexpr = json.dumps(path) + "".join(
            '.replace("{%s}", %s)' % (_esc(k), json.dumps(v))
            for k, v in args.items()
        )
        kw = {"method_lower": ep["method"].lower(), "pexpr": pexpr, "status": status}
        tpl = e["spell"]["ts"]
        lines = [pad + _sub(tpl[0], kw), pad + _sub(tpl[1], kw)]
        if isinstance(arg, dict) and arg.get("save"):
            for k, jpath in arg["save"].items():
                lines.append(pad + _sub(tpl[2], {"save_key": json.dumps(k), "jsonpath": _jsonpath(jpath)}))
        return lines

    if form == "dwell":
        return [pad + _sp(e, arg=arg)]

    if form == "wait-any":
        loc_chain = f"elements.{ops.camel(arg[0])}(page)" + "".join(
            f".or(elements.{ops.camel(n)}(page))" for n in arg[1:]
        )
        return [pad + _sp(e, loc_chain=loc_chain)]

    if form == "compare-screen":
        return [pad + _sp(e, arg=_esc(arg))]

    if form == "maybe":
        inner = _emit_step(arg, states, endpoints, pad + "    ")
        w = e["wrap"]["ts"]
        return ([pad + x for x in w["pre"]] + inner + [pad + x for x in w["post"]])

    if form == "expect":
        if isinstance(arg, dict) and "element" in arg:
            el = f"elements.{ops.camel(arg['element'])}(page)"
            if arg.get("soft"):
                inner = _emit_step_body({"expect": {k: v for k, v in arg.items() if k != "soft"}},
                                         states, endpoints, "")
                stmt = inner[0].strip()
                label = json.dumps(arg["element"])
                return [
                    f"{pad}if (soft) {{",
                    f"{pad}    await soft.check({label}, async () => {{ {stmt} }});",
                    f"{pad}}} else {{",
                    f"{pad}    try {{ {stmt} }} catch (e) {{ console.log(\"soft expect failed:\", e); }}",
                    f"{pad}}}"
                ]
            kw = {"el": el}
            if "text" in arg:
                kw["text"] = _esc(arg["text"])
            if "count" in arg:
                kw["count"] = arg["count"]
            return [pad + _sp(e, **kw)]
        if isinstance(arg, dict) and "value" in arg:
            return [pad + _sp(e, value=json.dumps(arg["value"]),
                              equals=json.dumps(arg.get("equals")))]

    return [f"{pad}// unsupported step: {form}"]
