"""conftest.py — the fixture layer, auth bootstrap, hooks."""

import json

from .common import *


def _auth_fixture(m):
    """sut.auth — sign in once per run in a bootstrap context at the
    action's `from` state; the session is kept as storage state and
    every test's fresh context inherits it.

    @concept CONCEPT-dsl-v1-016-01-the-auth-clause
    """
    act = m["sut"]["auth"]["action"]
    cls = _state_class(m["actions"][act]["from"])
    return '''
# @concept CONCEPT-dsl-v1-016-01-the-auth-clause
# @concept CONCEPT-playwright-v1-008-01-storage-state-reuse
@pytest.fixture(scope="session")
def auth_state(browser, base_url, run_dir):
    """One sign-in per run — the session kept as storage state; every
    test's fresh context inherits it. One credential spent per run."""
    import actions
    from pages import %s
    path = os.path.join(run_dir, "@@auth-state@@")
    ctx = browser.new_context()
    pg = ctx.new_page()
    try:
        %s(pg).goto(base_url)
        actions.%s(pg, base_url)
    except Exception:
        # the bootstrap owns no journal — leave the same evidence a
        # test failure leaves, under a setup/ dir in the run.
        d = os.path.join(run_dir, "setup")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "@@dom@@"), "w",
                  encoding="utf-8") as f:
            f.write(pg.content())
        pg.screenshot(path=os.path.join(d, "@@screenshot@@"))
        if os.environ.get("TAF_DEBUG"):
            pg.pause()  # TAF_DEBUG: stop at the failure, browser stays open
        raise
    ctx.storage_state(path=path)
    ctx.close()
    return path
''' % (cls, cls, _py(act))


def _conftest(m):
    conf = _HEADER + '''"""Fixtures for the generated suite.

@concept CONCEPT-pytest-v1-001-01-dependency-injected-fixtures
@concept CONCEPT-python-v1-006-01-pytest-yield-fixture
@concept CONCEPT-python-v1-010-01-os-environ-get
@concept CONCEPT-playwright-v1-001-01-browser-context-page-hierarchy
"""

import os
import pytest
from playwright.sync_api import sync_playwright

import taf_journal

_MODEL_BASE_URL = "%s"

# Failures the journal cannot carry: a teardown-phase failure lands
# after journal.end() already wrote the outcome, and a setup failure
# before begin() leaves no journal at all. sessionfinish unions these
# into failed.txt so TAF_RERUN still finds them.
_LATE_FAILURES = []


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
    return os.environ.get("TAF_BASE_URL", _MODEL_BASE_URL)


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
    if call.excinfo is None or isinstance(call.excinfo.value,
                                          pytest.skip.Exception):
        return  # green, or a skip — neither is a failure
    taf_journal.mark("failed")
    _LATE_FAILURES.append(item.name)
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
                page.screenshot(path=os.path.join(d, "@@screenshot@@"))
                with open(os.path.join(d, "@@dom@@"), "w",
                          encoding="utf-8") as f:
                    f.write(dom)
            except Exception:
                pass
        fp = ikc3_sink.fingerprint(item.name, err)
        old = ikc3_sink.filed(fp)
        if old:
            print("fault report already filed: %%s (fp %%s)" %% (old, fp))
            taf_journal.note("fault report already filed: %%s" %% old)
        else:
            rid = ikc3_sink.file_report(
                ws_url,
                "taf journey failed: %%s — %%s" %% (item.name, err),
                url=url, dom=dom,
            )
            ikc3_sink.record(fp, rid)
            print("fault report filed:", rid)
        taf_journal.event("fail", test=item.name, error=err)
    except Exception as e:  # noqa: BLE001 — the sink is a side channel
        print("ikc3 sink could not file the report:", e)


def pytest_sessionstart(session):
    """The run contract, printed once: what env shaped this run."""
    print("taf env: base_url=%%s headless=%%s slowmo=%%s video=%%s "
          "arrive_ms=%%s results=%%s" %% (
              os.environ.get("TAF_BASE_URL", _MODEL_BASE_URL),
              os.environ.get("TAF_HEADLESS", "0") == "1",
              os.environ.get("TAF_SLOWMO", "0"),
              "on" if "TAF_VIDEO" in os.environ else "off",
              os.environ.get("TAF_ARRIVE_MS", "15000"),
              os.environ.get("TAF_RESULTS", "results")))


# @concept CONCEPT-testing-v1-004-01-the-rerun
def pytest_sessionfinish(session, exitstatus):
    """Write failed.txt into the run dir — the rerun manifest."""
    import glob
    run = taf_journal.RUN_DIR
    if not run:
        return
    names = {os.path.basename(os.path.dirname(jf))
             for jf in glob.glob(os.path.join(run, "*", "@@journal@@"))
             if '"outcome": "failed"' in open(jf, encoding="utf-8").read()}
    names.update(_LATE_FAILURES)
    with open(os.path.join(run, "@@failed@@"), "w",
              encoding="utf-8") as f:
        f.write("\\n".join(sorted(names)))
    print("\\nresults → %%s" %% run)


def _last_failed_file():
    import glob
    files = glob.glob(os.path.join(
        os.environ.get("TAF_RESULTS", "results"), "*", "@@failed@@"))
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
    auth = m["sut"].get("auth")
    if auth:
        conf = conf.replace(
            "def page(browser, journal):",
            "def page(browser, journal, auth_state):")
        conf = conf.replace(
            "ctx = browser.new_context(**opts)",
            "ctx = browser.new_context(storage_state=auth_state, **opts)")
        conf += _auth_fixture(m)
    return conf
