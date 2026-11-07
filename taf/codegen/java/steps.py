"""Step-form generators — dsl vocabulary → Java lines."""

import json
import re

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
        return "compare-screen %s" % (
            arg.get("name") if isinstance(arg, dict) else arg)
    if form == "save":
        return "save %s" % arg
    if form == "expect":
        return "expect %s" % (arg.get("element") or arg.get("value")
                              or arg.get("saved") or "?")
    return form


def _pval(v, ctx, as_string=True):
    """A model value → a Java expression. Strings carrying ${key}
    placeholders read the journey's example row (Map<String,Object>)."""
    row = (ctx or {}).get("row")
    if not isinstance(v, str) or "${" not in v or not row:
        return _q(v) if isinstance(v, str) else json.dumps(v)
    m = re.fullmatch(r"\$\{([A-Za-z][A-Za-z0-9_-]*)\}", v)
    if m:
        return ('String.valueOf(%s.get(%s))' % (row, _q(m.group(1)))
                if as_string else '%s.get(%s)' % (row, _q(m.group(1))))
    # embedded placeholder — literal concatenation
    out = []
    for p in re.split(r"(\$\{[A-Za-z][A-Za-z0-9_-]*\})", v):
        mm = re.fullmatch(r"\$\{([A-Za-z][A-Za-z0-9_-]*)\}", p)
        out.append('String.valueOf(%s.get(%s))' % (row, _q(mm.group(1)))
                   if mm else _q(p))
    return " + ".join(o for o in out if o != '""')


def _emit_step(step, endpoints, pad, ctx=None):
    form, arg = next(iter(step.items()))
    if form != "maybe":
        # every step captions itself — narration rides the .srt
        return ([f'{pad}try {{ TafJournal.note({_q(_caption(form, arg))}); }}'
                 f' catch (java.io.IOException ignored) {{ /* best-effort */ }}'] +
                _emit_step_body(step, endpoints, pad, ctx))
    return _emit_step_body(step, endpoints, pad, ctx)


def _emit_step_body(step, endpoints, pad, ctx=None):
    """One model step → Java lines, spelled by
    taf/dsl/framework-spec.dsl. ctx keys: "api" (browserless — the
    request field is an APIRequestContext), "row" (example-row var),
    "visual" (golden-grammar compare)."""
    ctx = ctx or {}
    form, arg = next(iter(step.items()))
    e = _forms()[form]
    darg = arg if isinstance(arg, dict) else {}
    e = _variant_entry(e, [k for k in darg
                           if k not in ("soft", "mask", "name")])

    if form == "navigate":
        return [pad + _sp(e, arg=arg, state_class=_state_class(arg))]
    if form in ("click", "check"):
        name = arg.get("element") if isinstance(arg, dict) else arg
        return [pad + _sp(e, **{"j:name": _j(name)})]
    if form == "select":
        name = arg.get("element") if isinstance(arg, dict) else arg
        val = (_pval(arg["value"], ctx)
               if isinstance(arg, dict) and "value" in arg else '""')
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
            val = _pval(v, ctx)
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
            '.replace("{%s}", %s)' % (_esc(k), _pval(v, ctx))
            for k, v in args.items())
        kw = {"method_lower": ep["method"].lower(),
              "pexpr": pexpr, "status": status}
        tpl = e["spell"]["java"]
        lines = [pad + _sub(tpl[0], kw), pad + _sub(tpl[1], kw)]
        if isinstance(arg, dict) and arg.get("save"):
            for k, jpath in arg["save"].items():
                lines.append(pad + _sub(tpl[2],
                {"save_key": _esc(k), "jsonpath": _jsonpath(jpath)}))
        if ctx.get("api"):
            lines = [l.replace("page.request()", "request") for l in lines]
        # two api calls in one method would redeclare resp — scope each
        return [pad + "{"] + [pad + "    " + l.strip() for l in lines] \
            + [pad + "}"]
    if form == "dwell":
        # A pause for a watching human — observation, not synchronization.
        if ctx.get("api"):
            return [pad + ("try { Thread.sleep(%s); } catch "
                           "(InterruptedException ie) { "
                           "Thread.currentThread().interrupt(); }" % arg)]
        return [pad + _sp(e, arg=arg)]
    if form == "wait-any":
        locs = f"Elements.{_j(arg[0])}(page)" + "".join(
            f".or(Elements.{_j(n)}(page))" for n in arg[1:])
        return [pad + _sp(e, loc_chain=locs)]
    if form == "compare-screen":
        if isinstance(arg, dict):
            name, masks = arg["name"], (arg.get("mask") or [])
        else:
            name, masks = arg, []
        mask_list = "java.util.List.of(%s)" % ", ".join(
            "Elements.%s(page)" % _j(el) for el in masks) \
            if masks else "java.util.List.of()"
        if ctx.get("visual"):
            # the dedicated suite writes the
            # {name}_{Expected,Actual,Diff} grammar; `taf promote`
            # approves a new baseline
            return [pad + "VisualComparator.compare(page, %s, %s);"
                    % (_pval(name, ctx), mask_list)]
        return [pad + _sp(e, arg=_esc(name))]
    if form == "maybe":
        # An ifPresent step: try it, never fail.
        inner = _emit_step(arg, endpoints, pad + "    ", ctx)
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
                                   endpoints, pad + "        ", ctx)
                stmt = inner[-1].strip()
                return [
                    f"{pad}if (soft != null) {{",
                    f'{pad}    soft.check({_q(arg["element"])}, () -> {stmt[:-1]});',
                    f"{pad}}} else {{",
                    f"{pad}    try {{ {stmt}",
                    f'{pad}    }} catch (AssertionError e) {{ System.out.println("soft expect failed: " + e.getMessage()); }}',
                    f"{pad}}}"]
            if isinstance(arg.get("text"), str) and "${" in arg["text"] \
                    and ctx.get("row"):
                return [pad + 'assertThat(%s).hasText(%s);'
                        % (el, _pval(arg["text"], ctx))]
            kw = {"el": el}
            if "text" in arg:
                kw["text"] = _esc(arg["text"])
            if "count" in arg:
                kw["count"] = arg["count"]
            return [pad + _sp(e, **kw)]
        if isinstance(arg, dict) and "value" in arg:
            return [pad + _sp(e, value=_esc(arg["value"]),
                              equals=_pval(arg.get("equals"), ctx,
                                           as_string=False))]
    return [f"{pad}// unsupported step: {form}"]
