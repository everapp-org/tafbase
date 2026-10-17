"""Emit a Playwright + pytest suite from a valid SUT model — lane
TAF/PLAN-taf-v1-001-01/B-2.

@concept CONCEPT-dsl-v1-001-01-the-sut-model
@concept CONCEPT-playwright-v1-001-01-the-locator-ladder

The output is committed, reviewable Python: conftest.py (fixtures),
pages.py (one page object per state), elements.py (one function per
named locator), actions.py (one function per action), test_journeys.py
(one test per journey), taf.manifest.json (the traceability).
Generate, don't interpret — ADR-taf-v1-001-01.
"""

import json
import os

from taf import ops

_py = ops.snake


def _loc(loc, page="page"):
    """The Playwright call for one rung of the locator ladder."""
    if "role" in loc:
        extra = f', name="{loc["name"]}"' if "name" in loc else ""
        return f'{page}.get_by_role("{loc["role"]}"{extra})'
    if "label" in loc:
        return f'{page}.get_by_label("{loc["label"]}")'
    if "text" in loc:
        return f'{page}.get_by_text("{loc["text"]}")'
    if "placeholder" in loc:
        return f'{page}.get_by_placeholder("{loc["placeholder"]}")'
    if "testid" in loc:
        return f'{page}.get_by_test_id("{loc["testid"]}")'
    if "xpath" in loc:
        return f'{page}.locator("xpath={loc["xpath"]}")'
    return f'{page}.locator("{loc["css"]}")'


def _emit_step(step, states, endpoints, pad):
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
        return [f'{pad}elements.{_py(arg["element"])}(page).fill("{arg.get("value", "")}")']
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
                stmt = inner[0].strip()
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


def _jsonpath(p):
    """'$.a.b' -> ['a']['b']. v1 supports dotted keys only."""
    return "".join(f'[{json.dumps(k)}]' for k in str(p).lstrip("$").split(".") if k)


def _state_class(name):
    return ops.state_class(name)


_HEADER = "# Generated by tafbase (taf emit --lang python). Do not edit —\n" \
          "# edit the model and regenerate.\n"


def _conftest(m):
    return _HEADER + '''"""Fixtures for the generated suite.

@concept CONCEPT-pytest-v1-001-01-the-pytest-fixture
@concept CONCEPT-playwright-v1-002-01-the-browser-context
"""

import os
import pytest
from playwright.sync_api import sync_playwright

import taf_journal


# @concept CONCEPT-taf-v1-004-01-the-artifacts
@pytest.fixture(scope="session")
def run_dir():
    """results/<runId>/ — everything this run leaves, one folder."""
    import datetime
    d = os.path.join(os.environ.get("TAF_RESULTS", "results"),
                     datetime.datetime.now().strftime("%%Y%%m%%d-%%H%%M%%S"))
    os.makedirs(d, exist_ok=True)
    taf_journal.RUN_DIR = d
    return d


@pytest.fixture(autouse=True)
def journal(run_dir, request):
    """The per-test event stream — labels, checks, failures, timing."""
    taf_journal.begin(run_dir, request.node.name)
    yield
    taf_journal.end()


# @concept CONCEPT-taf-v1-003-01-the-environment
@pytest.fixture(scope="session")
def base_url():
    return os.environ.get("TAF_BASE_URL", "%s")


@pytest.fixture(scope="session")
def browser():
    """Headed by default — a learner should see the journey happen.
    TAF_HEADLESS=1 for CI; TAF_SLOWMO=<ms> slows each action."""
    with sync_playwright() as p:
        b = p.chromium.launch(
            headless=os.environ.get("TAF_HEADLESS") == "1",
            slow_mo=int(os.environ.get("TAF_SLOWMO", "0")))
        yield b
        b.close()


@pytest.fixture
def page(browser, journal):
    """A fresh context per test: full isolation, no shared state.
    TAF_VIDEO=<dir-name> records the run into the test's results dir."""
    opts = {}
    if os.environ.get("TAF_VIDEO"):
        opts["record_video_dir"] = taf_journal.test_dir()
    ctx = browser.new_context(**opts)
    pg = ctx.new_page()
    yield pg
    if os.environ.get("TAF_DEBUG") and taf_journal.failed():
        pg.pause()  # TAF_DEBUG: stop at the failure, browser stays open
    ctx.close()


# @concept CONCEPT-testing-v1-002-01-the-failure-funnel
class SoftChecks:
    """`soft` expects collect here instead of failing on the spot; the
    fixture flushes once at test end — the test still fails, but a run
    shows the whole damage, not the first hit only."""
    def __init__(self):
        self.failures = []

    def check(self, label, fn):
        try:
            fn()
        except AssertionError as e:
            self.failures.append("%%s — %%s" %% (label, e))


@pytest.fixture
def soft():
    s = SoftChecks()
    yield s
    assert not s.failures, "%%d soft check(s) failed: %%s" %% (
        len(s.failures), "; ".join(f.splitlines()[0] for f in s.failures))


# @concept CONCEPT-taf-v1-002-01-the-result-sink
def pytest_runtest_makereport(item, call):
    """A red test files a fault report into the tracker — when a sink is
    configured (TAF_IKC3_WS=ws://host:port/bus-ws). A sink that cannot
    file warns; it never fails the suite a second time."""
    if call.when != "call" or call.excinfo is None:
        return
    taf_journal.mark("failed")
    ws_url = os.environ.get("TAF_IKC3_WS")
    if not ws_url:
        return
    try:
        import ikc3_sink
        page = item.funcargs.get("page")
        err = str(call.excinfo.value).splitlines()[0][:200]
        url, dom = "", ""
        if page:
            try:  # a mid-navigation page has no readable content
                url, dom = page.url, page.content()[:50000]
            except Exception:
                pass
        d = taf_journal.test_dir()
        if d and page:
            try:  # evidence for a human: the screen, the DOM
                page.screenshot(path=os.path.join(d, "screenshot.png"))
                with open(os.path.join(d, "dom.html"), "w",
                          encoding="utf-8") as f:
                    f.write(dom)
            except Exception:
                pass
        rid = ikc3_sink.file_report(
            ws_url,
            "taf journey failed: %%s — %%s" %% (item.name, err),
            url=url, dom=dom,
        )
        print("fault report filed:", rid)
        taf_journal.event("fail", test=item.name, error=err)
    except Exception as e:  # noqa: BLE001 — the sink is a side channel
        print("ikc3 sink could not file the report:", e)


# @concept CONCEPT-testing-v1-004-01-the-rerun
def pytest_sessionfinish(session, exitstatus):
    """Write failed.txt into the run dir — the rerun manifest."""
    import glob
    run = taf_journal.RUN_DIR
    if not run:
        return
    names = [os.path.basename(os.path.dirname(jf))
             for jf in glob.glob(os.path.join(run, "*", "journal.jsonl"))
             if '"outcome": "failed"' in open(jf, encoding="utf-8").read()]
    with open(os.path.join(run, "failed.txt"), "w",
              encoding="utf-8") as f:
        f.write("\\n".join(sorted(names)))


def _last_failed_file():
    import glob
    files = glob.glob(os.path.join(
        os.environ.get("TAF_RESULTS", "results"), "*", "failed.txt"))
    return max(files) if files else None


def pytest_collection_modifyitems(items, config):
    """TAF_RERUN=1 replays only the tests in the last failed.txt."""
    if not os.environ.get("TAF_RERUN"):
        return
    f = _last_failed_file()
    if not f:
        return
    with open(f, encoding="utf-8") as fh:
        keep = set(fh.read().split())
    config.hook.pytest_deselected(
        items=[i for i in items if i.name not in keep])
    items[:] = [i for i in items if i.name in keep]
''' % m["sut"]["base-url"]


def _pages(m):
    lines = [_HEADER,
             '"""One page object per declared state.\n\n'
             "@concept CONCEPT-pom-v1-001-01-the-page-object\n"
             "@concept CONCEPT-playwright-v1-003-01-auto-waiting\n"
             '"""\n\nfrom playwright.sync_api import expect\n\n',
             "ROUTES = {%s}\n\n" % ", ".join(f'"{n}": "{s.get("route", "")}"'
                                             for n, s in m["states"].items())]
    for name, st in m["states"].items():
        lines.append(
            f"class {_state_class(name)}:\n"
            f'    """The \'{name}\' state. Its marker proves arrival."""\n\n'
            f"    def __init__(self, page):\n"
            f"        self.page = page\n"
            f"        self.marker = {_loc(st['marker'])}\n\n"
            f"    def goto(self, base_url):\n"
            f'        self.page.goto(base_url + ROUTES["{name}"])\n\n'
            f"    def expect_arrived(self):\n"
            f"        expect(self.marker).to_be_visible()\n\n")
    return "".join(lines)


def _elements(m):
    if not m.get("elements"):
        return None
    lines = [_HEADER,
             '"""Named locators, one function each — the locator ladder.\n\n'
             "@concept CONCEPT-playwright-v1-001-01-the-locator-ladder\n"
             '"""\n\n']
    for name, loc in m["elements"].items():
        lines.append(f"def {_py(name)}(page):\n    return {_loc(loc)}\n\n")
    return "".join(lines)


def _actions(m):
    if not m.get("actions"):
        return None
    lines = [_HEADER,
             '"""One function per declared action — the edges of the graph."""\n\n',
             "from pages import ROUTES\n",
             "import elements\n",
             "import taf_journal\n\n"] if m.get("elements") else [_HEADER,
             '"""One function per declared action — the edges of the graph."""\n\n',
             "from pages import ROUTES\n",
             "import taf_journal\n\n"]
    for name, act in m["actions"].items():
        body = _emit_steps(act.get("do", []), m["states"], m.get("endpoints") or {}, "    ")
        # Every action narrates itself — the label; the run reads as a story.
        title = act.get("title", name)
        narrate = f'    taf_journal.note("→ {title}")\n'
        lines.append(f"def {_py(name)}(page, base_url, soft=None):\n"
                     f"{narrate}{body or '    pass'}\n\n")
    return "".join(lines)


def _emit_steps(steps, states, endpoints, pad):
    lines = []
    for step in steps:
        lines.extend(_emit_step(step, states, endpoints, pad))
    return "\n".join(lines)


def _journeys(m):
    lines = [_HEADER,
             '"""One test per declared journey — arrange, act, assert.\n\n'
             "@concept CONCEPT-testing-v1-001-01-arrange-act-assert\n"
             '"""\n\n']
    imports = ["import actions"]
    if m.get("elements"):
        imports.append("import elements")
    imports.append("from pages import %s" % ", ".join(
        _state_class(n) for n in m["states"]))
    lines.append("\n".join(imports) + "\n\n")
    for name, j in m["journeys"].items():
        start = j["start"]
        body = [f"    # arrange\n"
                f"    sut = {_state_class(start)}(page)\n"
                f"    sut.goto(base_url)\n"
                f"    sut.expect_arrived()\n"
                f"    # act\n"]
        for op, arg in ops.journey_ops(m, name)[1:]:
            if op == "run":
                act = m["actions"][arg]
                body.append(f"    actions.{_py(arg)}(page, base_url, soft)\n")
            elif op == "step":
                body.append("\n".join(_emit_step(arg, m["states"], m.get("endpoints") or {}, "    ")) + "\n")
            elif op == "assert-marker":
                body.append(f"    {_state_class(arg)}(page).expect_arrived()\n")
            elif op == "assert-final":
                body.append("    # assert\n")
                body.append(f"    {_state_class(arg)}(page).expect_arrived()\n")
        if not any(op == "assert-final" for op, _ in ops.journey_ops(m, name)):
            body.append("    # assert\n")
        lines.append(f"def {ops.test_name_snake(name)}(page, base_url, soft):\n{''.join(body)}\n")
    return "".join(lines)


def _manifest(m):
    return json.dumps(ops.manifest(m), indent=2, sort_keys=True) + "\n"


def _sink_source():
    """The emitted ikc3_sink.py is taf/sink_ikc3.py verbatim — one source
    for the emitter's own code and the artifact it ships."""
    with open(os.path.join(os.path.dirname(__file__), "sink_ikc3.py"),
              encoding="utf-8") as f:
        return f.read()


def _journal_source():
    """The emitted taf_journal.py is taf/journal_runtime.py verbatim."""
    with open(os.path.join(os.path.dirname(__file__), "journal_runtime.py"),
              encoding="utf-8") as f:
        return f.read()


_CUSTOM_README = """# custom/ — hand-authored tests live here

Everything in this suite EXCEPT this directory is generated: edit the
model and regenerate, never the emitted files. Tests written by hand
belong in this directory — the emitter never writes here.

Hand-written tests inherit the suite: `page`, `base_url` fixtures,
`pages`, `elements`, `actions`, the fault-report hook. What they do not
inherit is the model's guarantees — they are not walked, not in the
manifest, not covered by parity.

This directory is also the DSL's incubator (the absorption loop,
CONCEPT-dsl-v1-013-01): a pattern that recurs here is a clause the
model should learn. It should trend toward empty.
"""


def emit(model, outdir):
    """Write the suite into `outdir`; returns the list of files written."""
    os.makedirs(outdir, exist_ok=True)
    files = {"conftest.py": _conftest(model),
             "ikc3_sink.py": _sink_source(),
             "taf_journal.py": _journal_source(),
             "pages.py": _pages(model),
             "actions.py": _actions(model),
             "elements.py": _elements(model),
             "test_journeys.py": _journeys(model),
             "taf.manifest.json": _manifest(model),
             os.path.join("custom", "README.md"): _CUSTOM_README}
    written = []
    for name, content in files.items():
        if content is None:
            continue
        path = os.path.join(outdir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(path)
    return written
