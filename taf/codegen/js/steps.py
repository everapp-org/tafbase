"""Step-form generators — dsl vocabulary → JavaScript (ESM) lines."""

import json
import re

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
        return "compare-screen %s" % (
            arg.get("name") if isinstance(arg, dict) else arg)
    if form == "save":
        return "save %s" % arg
    if form == "expect":
        return "expect %s" % (arg.get("element") or arg.get("value")
                              or arg.get("saved") or "?")
    return form


def _pval(v, ctx, as_string=True):
    """A model value → a JS expression. Strings carrying ${key}
    placeholders read the journey's example row."""
    row = (ctx or {}).get("row")
    if not isinstance(v, str) or "${" not in v or not row:
        return json.dumps(v)
    m = re.fullmatch(r"\$\{([A-Za-z][A-Za-z0-9_-]*)\}", v)
    if m:
        return ('String(%s[%s])' % (row, json.dumps(m.group(1)))
                if as_string else '%s[%s]' % (row, json.dumps(m.group(1))))
    # embedded placeholder — a template literal
    out = []
    for p in re.split(r"(\$\{[A-Za-z][A-Za-z0-9_-]*)\})", v):
        mm = re.fullmatch(r"\$\{([A-Za-z][A-Za-z0-9_-]*)\}", p)
        if mm:
            out.append("${%s[%s]}" % (row, json.dumps(mm.group(1))))
        else:
            out.append(p.replace("\\", "\\\\").replace("`", "\\`")
                       .replace("${", "\\${"))
    return "`%s`" % "".join(out)


def _emit_step(step, states, endpoints, pad, ctx=None):
    form, arg = next(iter(step.items()))
    if form != "maybe":
        return ([f"{pad}tafJournal.note({json.dumps(_caption(form, arg))});"] +
                _emit_step_body(step, states, endpoints, pad, ctx))
    return _emit_step_body(step, states, endpoints, pad, ctx)


def _emit_step_body(step, states, endpoints, pad, ctx=None):
    """One model step → JavaScript lines, spelled by
    taf/dsl/framework-spec.dsl. ctx keys: "api" (browserless — request
    is an APIRequestContext), "row" (example-row var), "visual"
    (golden-grammar compare)."""
    ctx = ctx or {}
    form, arg = next(iter(step.items()))
    e = _forms()[form]
    darg = arg if isinstance(arg, dict) else {}
    e = _variant_entry(e, [k for k in darg
                           if k not in ("soft", "mask", "name")])

    if form == "navigate":
        return [pad + _sp(e, arg=_esc(arg))]
    if form in ("click", "check"):
        name = arg.get("element") if isinstance(arg, dict) else arg
        return [pad + _sp(e, **{"j:name": ops.camel(name)})]
    if form == "select":
        name = arg.get("element") if isinstance(arg, dict) else arg
        val = (_pval(arg["value"], ctx)
               if isinstance(arg, dict) and "value" in arg else '""')
        return [pad + _sp(e, **{"j:name": ops.camel(name), "val_quoted": val})]
    if form == "fill":
        v = arg.get("value", "")
        if isinstance(v, str) and v.startswith("env-pool:"):
            val = f'tafJournal.envPool({json.dumps(v[9:])})'
        elif isinstance(v, str) and v.startswith("env:"):
            val = f'process.env[{json.dumps(v[4:])}]!'
        else:
            val = _pval(v, ctx)
        return [pad + _sp(e, **{"j:name": ops.camel(arg["element"]),
                                "value_expr": val})]
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
            '.replace("{%s}", %s)' % (_esc(k), _pval(v, ctx))
            for k, v in args.items())
        kw = {"method_lower": ep["method"].lower(),
              "pexpr": pexpr, "status": status}
        tpl = e["spell"][_LANG]
        lines = [pad + _sub(tpl[0], kw), pad + _sub(tpl[1], kw)]
        if isinstance(arg, dict) and arg.get("save"):
            for k, jpath in arg["save"].items():
                lines.append(pad + _sub(tpl[2], {
                    "save_key": json.dumps(k),
                    "jsonpath": _jsonpath(jpath)}))
        if ctx.get("api"):
            lines = [l.replace("page.request.", "request.") for l in lines]
        # two api calls in one test would redeclare const resp — scope each
        return [pad + "{"] + [pad + "    " + l.strip() for l in lines] \
            + [pad + "}"]
    if form == "dwell":
        if ctx.get("api"):
            return [pad + "await new Promise(r => setTimeout(r, %s));" % arg]
        return [pad + _sp(e, arg=arg)]
    if form == "wait-any":
        loc_chain = f"elements.{ops.camel(arg[0])}(page)" + "".join(
            f".or(elements.{ops.camel(n)}(page))" for n in arg[1:]
        )
        return [pad + _sp(e, loc_chain=loc_chain)]
    if form == "compare-screen":
        if isinstance(arg, dict):
            name, masks = arg["name"], (arg.get("mask") or [])
        else:
            name, masks = arg, []
        mask_list = ", ".join("elements.%s(page)" % ops.camel(el)
                              for el in masks)
        if ctx.get("visual"):
            # the dedicated suite writes the
            # {name}_{Expected,Actual,Diff} grammar; `taf promote`
            # approves a new baseline
            return [pad + "await visual.compare(page, %s, { mask: [%s] });"
                    % (_pval(name, ctx), mask_list)]
        spelled = _sp(e, arg=re.sub(r'^.|.$', '', _pval(name, ctx)))
        if mask_list:
            spelled = spelled[:-2] + ", { mask: [%s] });" % mask_list
        return [pad + spelled]
    if form == "maybe":
        inner = _emit_step(arg, states, endpoints, pad + "    ", ctx)
        w = e["wrap"][_LANG]
        return ([pad + x for x in w["pre"]] + inner +
                [pad + x for x in w["post"]])
    if form == "expect":
        if isinstance(arg, dict) and "element" in arg:
            el = f"elements.{ops.camel(arg['element'])}(page)"
            if arg.get("soft"):
                inner = _emit_step_body(
                    {"expect": {k: v for k, v in arg.items() if k != "soft"}},
                    states, endpoints, "", ctx)
                stmt = inner[0].strip()
                label = json.dumps(arg["element"])
                return [
                    f"{pad}if (soft) {{",
                    f"{pad}    await soft.check({label}, async () => {{ {stmt} }});",
                    f"{pad}}} else {{",
                    f"{pad}    try {{ {stmt} }} catch (e) {{ console.log(\"soft expect failed:\", e); }}",
                    f"{pad}}}"
                ]
            if isinstance(arg.get("text"), str) and "${" in arg["text"] \
                    and ctx.get("row"):
                return [pad + 'await expect(%s).toHaveText(%s);'
                        % (el, _pval(arg["text"], ctx))]
            kw = {"el": el}
            if "text" in arg:
                kw["text"] = _esc(arg["text"])
            if "count" in arg:
                kw["count"] = arg["count"]
            return [pad + _sp(e, **kw)]
        if isinstance(arg, dict) and "value" in arg:
            return [pad + _sp(e, value=json.dumps(arg["value"]),
                              equals=_pval(arg.get("equals"), ctx,
                                           as_string=False))]
    return [f"{pad}// unsupported step: {form}"]
