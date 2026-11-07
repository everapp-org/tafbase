"""taf run — execute an emitted suite — lane
TAF/PLAN-taf-v1-002-01.

@concept CONCEPT-taf-v1-003-01-the-environment
@concept CONCEPT-taf-v1-005-01-the-preflight

The run no longer emits: `taf emit-tests` produced the suite, `taf
run <dir>` executes it. The suite's taf.suite.json names its
toolchain, its framework dir, its base-url and its env needs — the
preflight checks those, then pytest, Maven, or Playwright runs the
committed suite.
"""
import glob
import json
import os
import subprocess
import sys

from taf import dryrun

PROFILES = {
    "headed": {},
    "ci": {"TAF_HEADLESS": "1", "TAF_VIDEO": "1"},
    "debug": {"TAF_DEBUG": "1", "TAF_VIDEO": "1", "TAF_SLOWMO": "400"},
}


def _exec(cmd, cwd=None, env=None):
    """The subprocess seam — tests patch this."""
    return subprocess.call(cmd, cwd=cwd, env=env)


def _emitter_for(lang):
    from taf.codegen.python import emitter as py_em
    from taf.codegen.java import emitter as java_em
    from taf.codegen.ts import emitter as ts_em
    from taf.codegen.js import emitter as js_em
    return {"python": py_em, "java": java_em,
            "ts": ts_em, "js": js_em}[lang]


def suite_meta(suite):
    """taf.suite.json of an emitted suite, or None."""
    p = os.path.join(suite, "taf.suite.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def _infer_lang(suite):
    """The toolchain a suite dir looks like — when taf.suite.json is
    absent (a hand-assembled suite, an older emit)."""
    if os.path.exists(os.path.join(suite, "pom.xml")):
        return "java"
    if glob.glob(os.path.join(suite, "*.spec.ts")):
        return "ts"
    if glob.glob(os.path.join(suite, "*.spec.mjs")):
        return "js"
    return "python"


def _command(lang, suite, extra):
    if lang == "python":
        return [sys.executable, "-m", "pytest", suite] + list(extra or [])
    if lang == "java":
        return ["mvn", "-f", os.path.join(suite, "pom.xml"), "test"] \
            + list(extra or [])
    # npx playwright test — the config inside the suite names its own
    # testDir; args pass through for filters like --grep.
    return ["npx", "playwright", "test"] + list(extra or [])


def run(suite, lang=None, extra=None, probe=True,
        env=None, profile=None, setenv=None):
    """Preflight the suite's declared env needs + an optional SUT probe,
    then execute the emitted suite in place. Returns the runner's exit
    code — a missing need or an unanswered probe exits 2, the honest
    refusal."""
    env = os.environ if env is None else env
    if not os.path.isdir(suite):
        print("refuse: no suite at %s — emit first:\n"
              "  taf emit-tests <model> --lang %s -o %s"
              % (suite, lang or "python", suite))
        return 2
    meta = suite_meta(suite) or {}
    lang = lang or meta.get("lang") or _infer_lang(suite)
    needs = meta.get("env-needs") or []
    base = meta.get("base-url") or ""

    findings = dryrun._needs_findings_for(needs, env)
    if probe:
        findings += dryrun._probe_findings_for(base, env)
    missing = [f for f in findings if f["level"] == "missing"]
    if missing and probe:
        print("refuse — the run lacks what it needs:")
        for f in missing:
            print("  %-24s %s" % (f["what"], f["detail"]))
            if f.get("hint"):
                print("    ↳ %s" % f["hint"])
        return 2
    if missing:
        print("preflight warning — needs unmet (running anyway):")
        for f in missing:
            print("  %-24s %s" % (f["what"], f["detail"]))

    child = dict(env)
    for var, val in (PROFILES.get(profile or "") or {}).items():
        child.setdefault(var, val)
    if setenv:
        child.update(setenv)
    # the suite's recorded framework path wins unless the console set one
    fw = meta.get("framework")
    if fw and "TAF_FRAMEWORK" not in child and not os.path.isabs(fw):
        cand = os.path.normpath(os.path.join(suite, fw))
        if os.path.isdir(cand):
            child["TAF_FRAMEWORK"] = cand
    cmd = _command(lang, suite, extra)
    print("run: %s" % " ".join(cmd))
    return _exec(cmd, cwd=suite if lang in ("ts", "js") else None,
                 env=child)
