"""taf dry-run — what a run would do, and what it lacks — lane
TAF/PLAN-taf-v1-001-01/L-12.

@concept CONCEPT-taf-v1-008-01-the-dry-run
@concept CONCEPT-taf-v1-003-01-the-environment
@concept CONCEPT-taf-v1-005-01-the-preflight

A report, not a gate: the dry run names the tests a run would execute,
the TAF_* contract as this shell sets it, and what the run lacks —
unset video, a missing golden baseline, a stale emitted suite, a SUT
that does not answer (--probe). Exit is 0; the person decides. The
fail-fast form (`requires:`) is the same honesty one step further.
"""

import glob
import importlib.util
import json
import os
import shutil
import socket
import urllib.request

from taf import ops

# The TAF_* contract, in display order. Each row names what the
# variable means when the run reads it — unset rows show the default
# the emitted suite falls back to.
def _env_table(m, env):
    base = env.get("TAF_BASE_URL")
    rows = [
        ("TAF_BASE_URL", base or m["sut"]["base-url"],
         "overrides the model" if base else "from the model"),
        ("TAF_HEADLESS", "headless" if env.get("TAF_HEADLESS") == "1" else "headed",
         "headed is the default; =1 for CI"),
        ("TAF_SLOWMO", (env.get("TAF_SLOWMO") or "0") + " ms",
         "slows each action"),
        ("TAF_VIDEO", "on" if env.get("TAF_VIDEO") else "off",
         "records .webm into the test's results dir"),
        ("TAF_DEBUG", "on" if env.get("TAF_DEBUG") else "off",
         "pauses at the failure, browser stays open"),
        ("TAF_RERUN", "on" if env.get("TAF_RERUN") else "off",
         "replays only the last failed.txt"),
        ("TAF_RESULTS", env.get("TAF_RESULTS") or "results/",
         "one folder per run"),
        ("TAF_IKC3_WS", env.get("TAF_IKC3_WS") or "off",
         "a red test files a fault report"),
    ]
    return [{"var": v, "set": v in env, "effective": eff, "note": note}
            for v, eff, note in rows]


def _finding(level, what, detail):
    return {"level": level, "what": what, "detail": detail}


def _walk_step(step):
    form, arg = next(iter(step.items()))
    yield form, arg
    if form == "maybe" and isinstance(arg, dict):
        yield from _walk_step(arg)


def _journey_steps(m, j):
    """The step dicts a journey executes — inline steps plus the
    do-lists of the actions it names."""
    for s in j.get("steps", []):
        if isinstance(s, str):
            for st in m["actions"].get(s, {}).get("do", []):
                yield st
        else:
            yield s


def _golden_names(m):
    """Every compare-screen name the declared journeys would assert."""
    names = []
    for j in m["journeys"].values():
        for st in _journey_steps(m, j):
            for form, arg in _walk_step(st):
                if form == "compare-screen" and arg not in names:
                    names.append(arg)
    return names


def _env_findings(m, env):
    out = []
    if env.get("TAF_VIDEO"):
        out.append(_finding("ok", "video",
                            "TAF_VIDEO=%s — the run records" % env["TAF_VIDEO"]))
    else:
        out.append(_finding("off", "video",
                            "TAF_VIDEO unset — the run leaves no recording"))
    if env.get("TAF_IKC3_WS"):
        out.append(_finding("ok", "fault reports",
                            "a red test files into %s" % env["TAF_IKC3_WS"]))
    else:
        out.append(_finding("off", "fault reports",
                            "TAF_IKC3_WS unset — a red test files nothing"))
    if env.get("TAF_DEBUG"):
        out.append(_finding("ok", "debug",
                            "TAF_DEBUG set — the run pauses at a failure"))
    if env.get("TAF_RERUN"):
        f = _last_failed(env)
        if f:
            n = len(open(f, encoding="utf-8").read().split())
            out.append(_finding("ok", "rerun",
                                "replays %d failed test(s) from %s" % (n, f)))
        else:
            out.append(_finding("missing", "rerun",
                                "TAF_RERUN set but no failed.txt under %s — "
                                "nothing to replay" % (env.get("TAF_RESULTS") or "results/")))
    base = env.get("TAF_BASE_URL")
    if base and base != m["sut"]["base-url"]:
        out.append(_finding("note", "base url",
                            "TAF_BASE_URL=%s overrides the model's %s"
                            % (base, m["sut"]["base-url"])))
    return out


def _last_failed(env):
    files = glob.glob(os.path.join(
        env.get("TAF_RESULTS") or "results", "*", "failed.txt"))
    return max(files) if files else None


def _model_findings(m, suite):
    out = []
    for name, loc in (m.get("elements") or {}).items():
        rung, _ = ops.locator_rung(loc)
        if rung in ("css", "xpath"):
            out.append(_finding("note", "elements.%s" % name,
                                "%s locator — the last-resort rung; it will "
                                "flag fragile in the manifest" % rung))
    for name, st in (m.get("states") or {}).items():
        rung, _ = ops.locator_rung(st["marker"])
        if rung in ("css", "xpath"):
            out.append(_finding("note", "states.%s.marker" % name,
                                "%s marker — the last-resort rung" % rung))
    goldens = _golden_names(m)
    if not goldens:
        return out
    if not suite:
        out.append(_finding("note", "compare-screen",
                            "%d snapshot name(s) declared (%s) — pass "
                            "--suite to check the baselines"
                            % (len(goldens), ", ".join(goldens))))
        return out
    for name in goldens:
        hits = glob.glob(os.path.join(suite, "**", name + ".png"),
                         recursive=True)
        if hits:
            out.append(_finding("ok", "golden '%s.png'" % name,
                                "baseline exists: %s" % hits[0]))
        else:
            out.append(_finding(
                "missing", "golden '%s.png'" % name,
                "compare-screen has no baseline under %s — the first run "
                "fails and writes Actual for a person to promote" % suite))
    return out


def _suite_findings(m, suite):
    if not os.path.isdir(suite):
        return [_finding("missing", "suite",
                         "no emitted suite at %s" % suite)]
    out = []
    man_path = os.path.join(suite, "taf.manifest.json")
    if not os.path.exists(man_path):
        out.append(_finding("missing", "suite",
                            "%s has no taf.manifest.json — is it an "
                            "emitted suite?" % suite))
    else:
        with open(man_path, encoding="utf-8") as f:
            emitted = json.load(f)
        if emitted == ops.manifest(m):
            out.append(_finding("ok", "suite", "manifest matches the model"))
        else:
            out.append(_finding("missing", "suite",
                                "stale — the model changed since emit; "
                                "regenerate"))
    customs = (glob.glob(os.path.join(suite, "custom", "test_*.py")) +
               glob.glob(os.path.join(suite, "custom", "**", "*.java"),
                         recursive=True))
    customs = [c for c in customs if not c.endswith("README.md")]
    if customs:
        out.append(_finding("note", "custom tests",
                            "%d hand-written file(s) in custom/ — not "
                            "walked, not in the manifest" % len(customs)))
    return out


def _toolchain_findings(lang):
    out = []
    if lang == "python":
        have = [p for p in ("pytest", "playwright")
                if importlib.util.find_spec(p)]
        missing = [p for p in ("pytest", "playwright") if p not in have]
        if missing:
            out.append(_finding("missing", "python toolchain",
                                "not importable: %s" % ", ".join(missing)))
        else:
            out.append(_finding("ok", "python toolchain",
                                "pytest and playwright importable"))
    else:
        if shutil.which("mvn"):
            out.append(_finding("ok", "java toolchain", "mvn on PATH"))
        else:
            out.append(_finding("missing", "java toolchain",
                                "mvn not on PATH — the emitted suite "
                                "cannot build"))
    return out


def _probe_findings(m, env):
    out = []
    url = env.get("TAF_BASE_URL") or m["sut"]["base-url"]
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            out.append(_finding("ok", "sut",
                                "%s answers: HTTP %d" % (url, r.status)))
    except Exception as e:
        out.append(_finding("missing", "sut",
                            "%s does not answer: %s" % (url, e)))
    ws = env.get("TAF_IKC3_WS")
    if ws:
        hostport = ws.split("://", 1)[-1].split("/", 1)[0]
        host, _, port = hostport.partition(":")
        try:
            with socket.create_connection((host, int(port or 80)), timeout=3):
                out.append(_finding("ok", "ikc3 bus",
                                    "%s accepts a connection" % hostport))
        except Exception as e:
            out.append(_finding("missing", "ikc3 bus",
                                "%s refuses: %s" % (hostport, e)))
    browsers = env.get("PLAYWRIGHT_BROWSERS_PATH") or os.path.expanduser(
        "~/.cache/ms-playwright")
    if glob.glob(os.path.join(browsers, "chromium*")):
        out.append(_finding("ok", "browsers", "a chromium build is installed"))
    else:
        out.append(_finding("missing", "browsers",
                            "no chromium under %s — run "
                            "`playwright install chromium`" % browsers))
    return out


def report(m, env=None, suite=None, lang="python", probe=False):
    """PURE apart from the filesystem/toolchain reads it reports on.
    The dry-run document: tests, env rows, findings."""
    env = os.environ if env is None else env
    tests = []
    for t in ops.manifest(m)["tests"]:
        j = m["journeys"][t["journey"]]
        forms = [f for st in _journey_steps(m, j)
                 for f, _ in _walk_step(st)]
        tests.append({"test": t["test"], "journey": t["journey"],
                      "start": j["start"], "actions": t["actions"],
                      "steps": forms,
                      "final": (j.get("expect-final") or {}).get("state")})
    findings = (_env_findings(m, env) +
                _model_findings(m, suite) +
                (_suite_findings(m, suite) if suite else []) +
                _toolchain_findings(lang))
    if probe:
        findings += _probe_findings(m, env)
    return {"sut": {"name": m["sut"]["name"],
                    "base-url": env.get("TAF_BASE_URL") or m["sut"]["base-url"]},
            "tests": tests,
            "env": _env_table(m, env),
            "findings": findings}


_LEVELS = ("missing", "off", "note", "ok")


def render(rep):
    """The report as text — the same content --json prints, for a human."""
    lines = ["sut: %s — %s" % (rep["sut"]["name"], rep["sut"]["base-url"]), ""]
    lines.append("would run — %d test(s):" % len(rep["tests"]))
    for t in rep["tests"]:
        steps = ", ".join(t["actions"]) if t["actions"] else \
            ", ".join(t["steps"]) or "arrive only"
        line = "  %-28s start=%s  %s" % (t["test"], t["start"], steps)
        if t["final"]:
            line += "  → %s" % t["final"]
        lines.append(line)
    lines.append("")
    lines.append("environment — as this shell sets it:")
    for r in rep["env"]:
        tag = "set  " if r["set"] else "unset"
        lines.append("  %-14s %s → %-28s %s"
                     % (r["var"], tag, r["effective"], r["note"]))
    lines.append("")
    lines.append("findings:")
    by = {lv: [f for f in rep["findings"] if f["level"] == lv]
          for lv in _LEVELS}
    for lv in _LEVELS:
        for f in by[lv]:
            lines.append("  %-8s %-24s %s" % (lv, f["what"], f["detail"]))
    if not rep["findings"]:
        lines.append("  (nothing to report)")
    lines.append("")
    counts = ["%d %s" % (len(by[lv]), lv) for lv in _LEVELS if by[lv]]
    lines.append(" · ".join(counts) if counts else "clean")
    return "\n".join(lines)
