"""taf run — emit and execute: the full cycle in one command — lane
TAF/PLAN-taf-v1-001-01/L-12.

@concept CONCEPT-taf-v1-005-01-the-preflight
@concept CONCEPT-taf-v1-003-01-the-environment
@concept CONCEPT-taf-v1-008-01-the-dry-run

The phases the person used to run by hand: check (the loader refuses a
broken model before anything else), emit (a temp suite, or --suite for
a committed one), execute (pytest; mvn test for --lang java). The
TAF_* contract flows through the environment — `taf env` sets it, the
runner inherits it. Exit code is the runner's. --probe is the first
gate: a missing probe finding refuses before a browser opens.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from taf import dryrun, emit_java, emit_python


def _exec(cmd, cwd=None, env=None):
    """The runner subprocess — patched out in tests."""
    return subprocess.run(cmd, cwd=cwd, env=env)


def _child_env(env, base_url=None, results=None, headless=False,
               slowmo=None, video=False, debug=False, rerun=False,
               sink=None):
    """Run-profile flags become the TAF_* contract of the child's
    environment — an explicit flag wins over the shell's setting."""
    child = dict(env)
    if base_url:
        child["TAF_BASE_URL"] = base_url
    if results:
        child["TAF_RESULTS"] = results
    if headless:
        child["TAF_HEADLESS"] = "1"
    if slowmo is not None:
        child["TAF_SLOWMO"] = str(slowmo)
    if video:
        child["TAF_VIDEO"] = "1"
    if debug:
        child["TAF_DEBUG"] = "1"
    if rerun:
        child["TAF_RERUN"] = "1"
    if sink is True:
        base = child.get("TAF_BASE_URL") or "http://x"
        child["TAF_IKC3_WS"] = dryrun._bus_url(base)
    elif sink:
        child["TAF_IKC3_WS"] = sink
    return child


def _profile_bits(child):
    """The effective run profile, one line of the header: headed,
    slowmo 300ms, video, sink."""
    bits = ["headless" if child.get("TAF_HEADLESS") == "1" else "headed"]
    if child.get("TAF_SLOWMO") not in (None, "0"):
        bits.append("slowmo %sms" % child["TAF_SLOWMO"])
    if child.get("TAF_VIDEO"):
        bits.append("video")
    if child.get("TAF_DEBUG"):
        bits.append("debug")
    if child.get("TAF_RERUN"):
        bits.append("rerun")
    if child.get("TAF_IKC3_WS"):
        bits.append("sink")
    return ", ".join(bits)


def run(m, suite=None, lang="python", extra=(), probe=False, keep=False,
        env=None, profile=None, setenv=None):
    """check -> emit -> execute; returns the runner's exit code.
    `profile` is the run-profile flags (see _child_env); `setenv` is
    --set NAME=VALUE pairs, arbitrary vars for the child."""
    env = os.environ if env is None else env
    child = _child_env(env, **(profile or {}))
    child.update(setenv or {})
    base = child.get("TAF_BASE_URL") or m["sut"]["base-url"]
    tmp = None
    if suite is None:
        tmp = tempfile.mkdtemp(prefix="taf-run-")
        suite = tmp
        (emit_python if lang == "python" else emit_java).emit(m, suite)
        origin = "emitted (%s)" % ("kept" if keep else "temp")
    else:
        origin = "committed"
    print("taf run — %s @ %s · %d test(s) · %s · suite: %s (%s)"
          % (m["sut"]["name"], base, len(m["journeys"]),
             _profile_bits(child), suite, origin), flush=True)
    try:
        needs = [f for f in dryrun._needs_findings(m, child)
                 if f["level"] == "missing"]
        if probe:
            missing = needs + [f for f in dryrun._probe_findings(m, child)
                               if f["level"] == "missing"]
            if missing:
                for f in missing:
                    print("  preflight missing  %s — %s"
                          % (f["what"], f["detail"]), flush=True)
                    if f.get("hint"):
                        print("      ↳ %s" % f["hint"], flush=True)
                print("refusing to run — fix the missing, "
                      "or --no-probe skips the gate", flush=True)
                return 1
        elif needs:
            # --no-probe escapes the refusal, not the truth: say it,
            # then run anyway.
            for f in needs:
                print("  preflight warning  %s — %s"
                      % (f["what"], f["detail"]), flush=True)
                if f.get("hint"):
                    print("      ↳ %s" % f["hint"], flush=True)
        if lang == "java":
            cmd = (["mvn", "-q", "-f", os.path.join(suite, "pom.xml"),
                    "test"] + list(extra))
        else:
            cmd = ([sys.executable, "-m", "pytest", "-q"] + list(extra)
                   + [suite])
        return _exec(cmd, env=child).returncode
    finally:
        if tmp and not keep:
            shutil.rmtree(tmp, ignore_errors=True)
