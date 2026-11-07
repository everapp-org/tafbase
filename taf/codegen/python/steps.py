"""Step-form generators — dsl vocabulary → Python lines."""

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


def _pval(v, ctx):
    """A model value → a Python expression. Strings carrying ${key}
    placeholders read the journey's example row at run time."""
    row = (ctx or {}).get("row")
    if not isinstance(v, str) or "${" not in v or not row:
        return json.dumps(v)
    m = re.fullmatch(r"\$\{([A-Za-z][A-Za-z0-9_-]*)\}", v)
    if m:
        return '%s[%s]' % (row, json.dumps(m.group(1)))
    # embedded placeholder — an f-string; literal braces are escaped
    out = []
    for p in re.split(r"(\$\{[A-Za-z][A-Za-z0-9_-]*\})", v):
        mm = re.fullmatch(r"\$\{([A-Za-z][A-Za-z0-9_-]*)\}", p)
        if mm:
            out.append("{%s[%s]}" % (row, json.dumps(mm.group(1))))
        else:
            out.append(p.replace("{", "{{").replace("}", "}}"))
    return 'f"%s"' % "".join(out)


def _emit_step(step, states, endpoints, pad, ctx=None):
    form, arg = next(iter(step.items()))
    if form != "maybe":
        # every step captions itself — narration rides the .srt
        return ([f'{pad}taf_journal.note({_dq(_caption(form, arg))})'] +
                _emit_step_body(step, states, endpoints, pad, ctx))
    return _emit_step_body(step, states, endpoints, pad, ctx)


def _dq(s):
    return json.dumps(s)


def _pexpr_args(args, ctx):
    """The api step's substitution dict — {key: expr} with ${row-key}
    placeholders resolved."""
    return "{%s}" % ", ".join(
        "%s: %s" % (json.dumps(k), _pval(v, ctx))
        for k, v in args.items())


def _emit_step_body(step, states, endpoints, pad, ctx=None):
    """One model step → Python lines, spelled by
    taf/dsl/framework-spec.dsl. ctx keys: "api" (browserless — the api
    fixture is an APIRequestContext), "row" (example-row var name),
    "visual" (golden-grammar compare)."""
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
        return [pad + _sp(e, **{"py:name": _py(name)})]
    if form == "select":
        name = arg.get("element") if isinstance(arg, dict) else arg
        val = (_pval(arg["value"], ctx)
               if isinstance(arg, dict) and "value" in arg else '""')
        return [pad + _sp(e, **{"py:name": _py(name), "val_quoted": val})]
    if form == "fill":
        v = arg.get("value", "")
        if isinstance(v, str) and v.startswith("env-pool:"):
            # env-pool:NAME — a list in the env; one value spent per call.
            val = 'taf_journal.env_pool(%s)' % json.dumps(v[9:])
        elif isinstance(v, str) and v.startswith("env:"):
            # env:NAME — the model names the need; the run reads the
            # variable. The secret is never in emitted code.
            val = 'os.environ[%s]' % json.dumps(v[4:])
        else:
            val = _pval(v, ctx)
        return [pad + _sp(e, **{"py:name": _py(arg["element"]),
                                "value_expr": val})]
    if form == "wait-for":
        kw = {"py:element": _py(arg.get("element", ""))}
        if "state" in arg:
            kw["state_class"] = _state_class(arg["state"])
        return [pad + _sp(e, **kw)]
    if form == "api":
        name = arg if isinstance(arg, str) else arg.get("endpoint")
        args = {} if isinstance(arg, str) else arg.get("args") or {}
        ep = endpoints[name]
        path, status = ep["path"], (ep.get("expect") or {}).get("status", 200)
        kw = {"method_lower": ep["method"].lower(),
              "pexpr": '%s.format(**%s)' % (json.dumps(path),
                                           _pexpr_args(args, ctx)),
              "status": status}
        tpl = e["spell"]["python"]
        lines = [pad + _sub(tpl[0], kw), pad + _sub(tpl[1], kw)]
        if isinstance(arg, dict) and arg.get("save"):
            for k, jpath in arg["save"].items():
                lines.append(pad + _sub(tpl[2],
                {"save_key": json.dumps(k),
                 "jsonpath": _jsonpath(jpath)}))
        if ctx.get("api"):
            lines = [l.replace("page.request.", "api.") for l in lines]
        return lines
    if form == "dwell":
        # A pause for a watching human — observation, not synchronization.
        if ctx.get("api"):
            return [pad + "time.sleep(%s / 1000.0)" % arg]
        return [pad + _sp(e, arg=arg)]
    if form == "wait-any":
        locs = f"elements.{_py(arg[0])}(page)" + "".join(
            f".or_(elements.{_py(n)}(page))" for n in arg[1:])
        return [pad + _sp(e, loc_chain=locs)]
    if form == "compare-screen":
        if isinstance(arg, dict):
            name, masks = arg["name"], (arg.get("mask") or [])
        else:
            name, masks = arg, []
        mask_list = ", ".join("elements.%s(page)" % _py(el) for el in masks)
        name_expr = _pval(name, ctx)
        if ctx.get("visual"):
            # the dedicated suite writes the
            # {name}_{Expected,Actual,Diff} grammar; `taf promote`
            # approves a new baseline
            return [pad + "visual.compare(page, %s, mask=[%s])"
                    % (name_expr, mask_list)]
        spelled = _sp(e, arg=re.sub(r'^.|.$', '', name_expr))
        if mask_list:
            spelled = spelled[:-1] + ", mask=[%s])" % mask_list
        return [pad + spelled]
    if form == "maybe":
        # An ifPresent step: try it, never fail.
        inner = _emit_step(arg, states, endpoints, pad + "    ", ctx)
        w = e["wrap"]["python"]
        return ([pad + x for x in w["pre"]] + inner +
                [pad + x for x in w["post"]])
    if form == "expect":
        if isinstance(arg, dict) and "element" in arg:
            el = f"elements.{_py(arg['element'])}(page)"
            if arg.get("soft"):
                # Collect into the SoftChecks stack; the fixture flushes
                # once at test end — the run shows every failed check.
                inner = _emit_step({"expect": {k: v for k, v in arg.items()
                                               if k != "soft"}},
                                   states, endpoints, pad + "        ", ctx)
                stmt = inner[-1].strip()
                return [
                    f"{pad}if soft is not None:",
                    f'{pad}    soft.check({json.dumps(arg["element"])}, lambda: {stmt})',
                    f"{pad}else:",
                    f"{pad}    try:",
                    f"{pad}        {stmt}",
                    f"{pad}    except AssertionError as _e:",
                    f'{pad}        print("soft expect failed:", _e)']
            if isinstance(arg.get("text"), str) and "${" in arg["text"] \
                    and ctx.get("row"):
                return [pad + 'expect(%s).to_have_text(%s)'
                        % (el, _pval(arg["text"], ctx))]
            kw = {"el": el}
            if "text" in arg:
                kw["text"] = _esc(arg["text"])
            if "count" in arg:
                kw["count"] = arg["count"]
            return [pad + _sp(e, **kw)]
        if isinstance(arg, dict) and "value" in arg:
            return [pad + _sp(e, value=_pval(arg["value"], ctx),
                              equals=_pval(arg.get("equals"), ctx))]
    return [f"{pad}# unsupported step: {form}"]
