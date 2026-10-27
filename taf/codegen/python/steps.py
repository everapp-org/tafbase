"""Step-form generators — dsl vocabulary → Python lines."""

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
        # every step captions itself — narration rides the .srt
        return ([f'{pad}taf_journal.note({_dq(_caption(form, arg))})'] +
                _emit_step_body(step, states, endpoints, pad))
    return _emit_step_body(step, states, endpoints, pad)


def _dq(s):
    return json.dumps(s)


def _emit_step_body(step, states, endpoints, pad):
    form, arg = next(iter(step.items()))
    if form == "navigate":
        return [f'{pad}page.goto(base_url + ROUTES["{arg}"])']
    if form == "click":
        name = arg.get("element") if isinstance(arg, dict) else arg
        return [f"{pad}elements.{_py(name)}(page).click()"]
    if form == "check":
        name = arg.get("element") if isinstance(arg, dict) else arg
        return [f"{pad}elements.{_py(name)}(page).check()"]
    if form == "select":
        name = arg.get("element") if isinstance(arg, dict) else arg
        val = f'"{arg["value"]}"' if isinstance(arg, dict) and "value" in arg else ""
        return [f"{pad}elements.{_py(name)}(page).select_option({val})"]
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
            val = '"%s"' % v
        return [f'{pad}elements.{_py(arg["element"])}(page).fill({val})']
    if form == "wait-for":
        if "state" in arg:
            return [f"{pad}{_state_class(arg['state'])}(page).expect_arrived()"]
        return [f"{pad}expect(elements.{_py(arg['element'])}(page)).to_be_visible()"]
    if form == "api":
        name = arg if isinstance(arg, str) else arg.get("endpoint")
        args = {} if isinstance(arg, str) else arg.get("args") or {}
        ep = endpoints[name]
        path, status = ep["path"], (ep.get("expect") or {}).get("status", 200)
        lines = [f'{pad}resp = page.request.{ep["method"].lower()}(base_url + "{path}".format(**{json.dumps(args)}))',
                 f"{pad}assert resp.status == {status}"]
        if isinstance(arg, dict) and arg.get("save"):
            for k, jpath in arg["save"].items():
                lines.append(f"{pad}saved[{json.dumps(k)}] = resp.json(){_jsonpath(jpath)}")
        return lines
    if form == "dwell":
        # A pause for a watching human — observation, not synchronization.
        return [f"{pad}page.wait_for_timeout({arg})"]
    if form == "wait-any":
        locs = f"elements.{_py(arg[0])}(page)" + "".join(
            f".or_(elements.{_py(n)}(page))" for n in arg[1:])
        return [f"{pad}expect({locs}).to_be_visible()"]
    if form == "compare-screen":
        return [f'{pad}expect(page).to_have_screenshot("{arg}.png")']
    if form == "maybe":
        # An ifPresent step: try it, never fail.
        inner = _emit_step(arg, states, endpoints, pad + "    ")
        return [f"{pad}try:"] + inner + [
            f"{pad}except Exception:",
            f"{pad}    pass  # maybe: the step did not apply"]
    if form == "expect":
        if isinstance(arg, dict) and "element" in arg:
            el = f"elements.{_py(arg['element'])}(page)"
            if arg.get("soft"):
                # Collect into the SoftChecks stack; the fixture flushes
                # once at test end — the run shows every failed check.
                inner = _emit_step({"expect": {k: v for k, v in arg.items()
                                               if k != "soft"}},
                                   states, endpoints, pad + "        ")
                stmt = inner[-1].strip()
                return [
                    f"{pad}if soft is not None:",
                    f'{pad}    soft.check("{arg["element"]}", lambda: {stmt})',
                    f"{pad}else:",
                    f"{pad}    try:",
                    f"{pad}        {stmt}",
                    f"{pad}    except AssertionError as _e:",
                    f'{pad}        print("soft expect failed:", _e)']
            if arg.get("hidden"):
                return [f"{pad}expect({el}).to_be_hidden()"]
            if "text" in arg:
                return [f'{pad}expect({el}).to_have_text("{arg["text"]}")']
            if "count" in arg:
                return [f"{pad}expect({el}).to_have_count({arg['count']})"]
            return [f"{pad}expect({el}).to_be_visible()"]
        if isinstance(arg, dict) and "value" in arg:
            return [f"{pad}assert saved[{json.dumps(arg['value'])}] == {json.dumps(arg.get('equals'))}"]
    return [f"{pad}# unsupported step: {form}"]
