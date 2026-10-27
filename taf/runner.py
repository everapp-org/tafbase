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


def _exec(cmd, cwd=None):
    """The runner subprocess — patched out in tests."""
    return subprocess.run(cmd, cwd=cwd)


def run(m, suite=None, lang="python", extra=(), probe=False, keep=False,
        env=None):
    """check -> emit -> execute; returns the runner's exit code."""
    env = os.environ if env is None else env
    base = env.get("TAF_BASE_URL") or m["sut"]["base-url"]
    tmp = None
    if suite is None:
        tmp = tempfile.mkdtemp(prefix="taf-run-")
        suite = tmp
        (emit_python if lang == "python" else emit_java).emit(m, suite)
        origin = "emitted (%s)" % ("kept" if keep else "temp")
    else:
        origin = "committed"
    print("taf run — %s @ %s · %d test(s) · suite: %s (%s)"
          % (m["sut"]["name"], base, len(m["journeys"]), suite, origin),
          flush=True)
    try:
        if probe:
            missing = [f for f in dryrun._probe_findings(m, env)
                       if f["level"] == "missing"]
            if missing:
                for f in missing:
                    print("  preflight missing  %s — %s"
                          % (f["what"], f["detail"]), flush=True)
                print("refusing to run — fix the missing, or drop --probe",
                      flush=True)
                return 1
        if lang == "java":
            cmd = (["mvn", "-q", "-f", os.path.join(suite, "pom.xml"),
                    "test"] + list(extra))
        else:
            cmd = ([sys.executable, "-m", "pytest", "-q"] + list(extra)
                   + [suite])
        return _exec(cmd).returncode
    finally:
        if tmp and not keep:
            shutil.rmtree(tmp, ignore_errors=True)
