"""taf — the tafbase command line.

    python -m taf emit-tests --lang python <sut.model.json> -o <suite-dir>
    python -m taf emit-framework --lang python -o <framework-dir>
    python -m taf run <suite-dir>
    python -m taf check <sut.model.json>
    python -m taf dry-run <sut.model.json>
    python -m taf promote --results <run> --goldens <dir>
"""

import argparse
import glob
import json
import os
import shutil
import sys
import urllib.parse

from taf import dryrun, graph, model, runner


_CMDS = ("check", "walk", "emit", "emit-tests", "emit-framework",
         "dry-run", "env", "run", "record", "studio", "promote")

_EPILOG = """\
the cycle: emit-tests → run → promote
  the vendor ships the framework once; the user emits a suite per SUT
  against it; `taf run` executes the emitted suite — it never emits.

examples:
  taf emit-framework --lang python -o taf-runtime
  taf emit-tests <model> --lang python -o generated/<sut>
  taf run generated/<sut>                execute the emitted suite
  taf run generated/<sut> -- -m smoke    after -- : args for the runner
  taf promote --results results/<run> --goldens generated/<sut>/goldens
  taf emit <model> --lang ts -o out/     compat: suite + framework nested
  eval "$(taf env <model> --video --sink)"
  taf walk <model> --from <state> --seed 7
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # `taf <model>` is `taf dry-run <model>` — the report is the default.
    if argv and argv[0] not in _CMDS and argv[0] not in ("-h", "--help"):
        argv = ["dry-run"] + argv
    if not argv:
        argv = ["-h"]
    # `run` splits at `--` itself: argparse REMAINDER would swallow the
    # command's own flags.
    extra = []
    if argv[0] == "run" and "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(
        prog="taf", epilog=_EPILOG,
        description="default command: dry-run — `taf <model>`",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="validate a model, print its refusals")
    c.add_argument("model")

    w = sub.add_parser("walk", help="derive a journey by seeded graph walk")
    w.add_argument("model")
    w.add_argument("--from", dest="start", required=True, help="start state")
    w.add_argument("--seed", type=int, default=1)
    w.add_argument("--steps", type=int, default=5)
    w.add_argument("--name", help="journey name (default: walk-<from>-<seed>)")
    w.add_argument("--cover", action="store_true",
                   help="prefer edges this walk has not taken yet")

    e = sub.add_parser("emit", help="generate suite + framework into one "
                                    "dir (the compat single shot)")
    e.add_argument("model")
    e.add_argument("--lang", choices=["python", "java", "ts", "js"], required=True)
    e.add_argument("-o", "--outdir", required=True)
    e.add_argument("--journeys",
                   help="JSON of extra journeys to merge in (e.g. `taf walk` output)")

    et = sub.add_parser("emit-tests",
                        help="generate the SUT test suite against an "
                             "emitted framework (the user command)")
    et.add_argument("model")
    et.add_argument("--lang", choices=["python", "java", "ts", "js"], required=True)
    et.add_argument("-o", "--outdir", required=True)
    et.add_argument("--framework", default="../taf-runtime",
                    help="the emitted framework dir this suite binds to "
                         "(default: ../taf-runtime)")
    et.add_argument("--journeys",
                    help="JSON of extra journeys to merge in (e.g. `taf walk` output)")

    ef = sub.add_parser("emit-framework",
                        help="generate the vendor framework — no model "
                             "(the vendor command)")
    ef.add_argument("--lang", choices=["python", "java", "ts", "js"], required=True)
    ef.add_argument("-o", "--outdir", required=True)

    d = sub.add_parser("dry-run",
                       help="report what a run would do and what it lacks")
    d.add_argument("model")
    d.add_argument("--suite",
                   help="an emitted suite dir — checks goldens and freshness")
    d.add_argument("--journeys",
                   help="JSON of extra journeys to merge in (e.g. `taf walk` output)")
    d.add_argument("--lang", choices=["python", "java", "ts", "js"], default="python",
                   help="which toolchain to check (default: python)")
    d.add_argument("--probe", action="store_true",
                   help="also touch the network: SUT, ikc3 bus, browsers")
    d.add_argument("--json", action="store_true",
                   help="print the report as JSON")

    v = sub.add_parser("env",
                       help="print TAF_* export lines — eval \"$(taf env ...)\"")
    v.add_argument("model")
    v.add_argument("--base-url", help="override the model's base-url")
    v.add_argument("--results", help="artifacts root (default: results)")
    v.add_argument("--headless", action="store_true")
    v.add_argument("--slowmo", type=int, metavar="MS")
    v.add_argument("--arrive-ms", type=int, metavar="MS")
    v.add_argument("--video", action="store_true",
                   help="record .webm into each test's results dir")
    v.add_argument("--debug", action="store_true",
                   help="pause at a failure, browser stays open")
    v.add_argument("--rerun", action="store_true",
                   help="replay only the last failed.txt")
    v.add_argument("--sink", nargs="?", const=True, metavar="URL",
                   help="file fault reports; bare --sink derives "
                        "ws://<sut-host>/bus-ws")
    v.add_argument("--shell", choices=["sh", "fish"],
                   help="default: detected from $SHELL")
    v.add_argument("--unset", action="store_true",
                   help="print lines that clear the TAF_* contract")

    r = sub.add_parser("run",
                       help="execute an emitted suite — the run never emits")
    r.add_argument("suite",
                   help="the emitted suite dir (taf emit-tests output)")
    r.add_argument("--lang", choices=["python", "java", "ts", "js"],
                   help="which runner to call (default: taf.suite.json's "
                        "recorded lang, else inferred)")
    r.add_argument("--probe", dest="probe", action="store_true",
                   default=True,
                   help="preflight before running (default: on)")
    r.add_argument("--no-probe", dest="probe", action="store_false",
                   help="skip the gate: probes never run, env needs "
                        "warn instead of refusing")
    # the run profile — inline TAF_* contract, no shell exports needed
    r.add_argument("--base-url", help="override the suite's base-url")
    r.add_argument("--results", help="artifacts root (default: results)")
    r.add_argument("--headless", action="store_true",
                   help="headless browser (headed is the default)")
    r.add_argument("--slowmo", type=int, metavar="MS",
                   help="ms between Playwright actions — watchable runs")
    r.add_argument("--arrive-ms", type=int, metavar="MS",
                   help="marker arrival timeout in ms (default: 15000)")
    r.add_argument("--video", action="store_true",
                   help="record .webm into each test's results dir")
    r.add_argument("--debug", action="store_true",
                   help="pause at a failure, browser stays open")
    r.add_argument("--rerun", action="store_true",
                   help="replay only the last failed.txt")
    r.add_argument("--set", dest="setenv", action="append",
                   metavar="NAME=VALUE", default=[],
                   help="inject any var into the run's env — "
                        "--set TAF_SUT_CODES=XXXX-XXXX")
    r.add_argument("--sink", nargs="?", const=True, metavar="URL",
                   help="file fault reports; bare --sink derives "
                        "ws://<sut-host>/bus-ws")

    rc = sub.add_parser("record", help="drive the SUT by hand; drafts "
                                     "model clauses to a file")
    rc.add_argument("model")
    rc.add_argument("--out", default=None,
                    help="draft path (default: recorded-<name>.json; "
                         "an existing file earns a timestamp)")
    rc.add_argument("--name", default="recorded",
                    help="the draft's title — the journey name to merge as")
    rc.add_argument("--base-url", help="override the model's base-url")
    rc.add_argument("--workbench", action="store_true",
                    help="launch with the unified Browser Workbench "
                         "(Dashboard + Reader + Security Watchdog)")
    rc.add_argument("--security-mode", choices=list(model.SECURITY_MODES),
                    help="override security posture (shield|audit|raw|off)")
    rc.add_argument("--hud", choices=list(model.SECURITY_HUDS),
                    help="override HUD display (docked|toast-on-alert|detached)")

    st = sub.add_parser("studio",
                        help="launch the Browser Workbench "
                             "(TAF Studio + Standalone Reader + Page Watchdog)")
    st.add_argument("model")
    st.add_argument("--out", default=None,
                    help="draft path (default: recorded-<name>.json)")
    st.add_argument("--name", default="studio",
                    help="session draft title")
    st.add_argument("--base-url", help="override the model's base-url")
    st.add_argument("--security-mode", choices=list(model.SECURITY_MODES),
                    help="security posture (shield|audit|raw|off)")
    st.add_argument("--hud", choices=list(model.SECURITY_HUDS),
                    help="HUD display (docked|toast-on-alert|detached)")
    st.add_argument("--library-dir", default=None,
                    help="standalone library root (default: TAF_LIBRARY_DIR or reader-library)")
    st.add_argument("--cdp", default=None,
                    help="attach to an existing Chrome via CDP URL (e.g. http://127.0.0.1:9222)")

    p = sub.add_parser("promote",
                       help="approve *_Actual.png shots as the new "
                            "*_Expected.png baselines")
    p.add_argument("--results",
                   help="a run dir or results root to scan "
                        "(default: latest under TAF_RESULTS/results)")
    p.add_argument("--goldens",
                   help="the baselines dir (default: TAF_GOLDENS or "
                        "<results>/../goldens or ./goldens)")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "promote":
            return _promote(args)

        if args.cmd == "emit-framework":
            written = runner._emitter_for(args.lang).emit_framework(
                args.outdir)
            for f in written:
                print("wrote %s" % f)
            return 0

        if args.cmd == "run":
            if os.path.isfile(args.suite) or args.suite.endswith(".json"):
                print("refuse: `taf run` executes an emitted suite dir, "
                      "not a model — emit first:\n"
                      "  taf emit-tests %s --lang %s -o %s"
                      % (args.suite, args.lang or "python",
                         os.path.splitext(args.suite)[0] + "-suite"))
                return 2
            return runner.run(
                args.suite, lang=args.lang, extra=extra,
                probe=args.probe, setenv=_run_env(args))

        m = model.load(args.model)

        if args.cmd == "check":
            print("model ok: %s" % m["sut"]["name"])
            return 0

        if args.cmd == "walk":
            name = args.name or f"walk-{args.start}-{args.seed}"
            j = graph.walk(m, args.start, args.seed, args.steps, args.cover)
            print(json.dumps({"journeys": {name: j}}, indent=2))
            return 0

        if getattr(args, "journeys", None):
            with open(args.journeys, encoding="utf-8") as f:
                m = graph.with_journeys(m, json.load(f)["journeys"])

        if args.cmd == "dry-run":
            rep = dryrun.report(m, suite=args.suite, lang=args.lang,
                                probe=args.probe)
            print(json.dumps(rep, indent=2) if args.json
                  else dryrun.render(rep))
            return 0

        if args.cmd == "env":
            print(dryrun.env_lines(
                m, shell=args.shell, base_url=args.base_url,
                results=args.results, headless=args.headless,
                slowmo=args.slowmo, arrive_ms=args.arrive_ms,
                video=args.video, debug=args.debug,
                rerun=args.rerun, sink=args.sink, unset=args.unset))
            return 0

        if args.cmd == "studio" or (args.cmd == "record" and getattr(args, "workbench", False)):
            from taf import workbench as taf_wb
            base = (args.base_url or os.environ.get("TAF_BASE_URL")
                    or m["sut"]["base-url"])
            out = args.out or "recorded-%s.json" % args.name
            taf_wb.launch_studio(
                m, base_url=base, out=out, title=args.name,
                security_mode=getattr(args, "security_mode", None),
                hud_mode=getattr(args, "hud", None),
                library_dir=getattr(args, "library_dir", None),
                cdp_url=getattr(args, "cdp", None))
            return 0

        if args.cmd == "record":
            from taf import record as taf_record
            base = (args.base_url or os.environ.get("TAF_BASE_URL")
                    or m["sut"]["base-url"])
            out = args.out or "recorded-%s.json" % args.name
            taf_record.record(base, out, title=args.name,
                              needs=model.env_needs(m), m=m)
            return 0

        if args.cmd == "emit-tests":
            written = runner._emitter_for(args.lang).emit_tests(
                m, args.outdir, framework=args.framework)
            for f in written:
                print("wrote %s" % f)
            return 0

        # emit — the compat single dir
        written = runner._emitter_for(args.lang).emit(m, args.outdir)
        for f in written:
            print("wrote %s" % f)
        return 0
    except model.ModelRefusal as err:
        for r in getattr(err, "refusals", []):
            print("%-40s %-16s %s" % (r["clause"], r["reason"], r["message"]))
        return 1


def _run_env(args):
    """The run profile flags → TAF_* variables for the suite's env."""
    setenv = {}
    if args.base_url:
        setenv["TAF_BASE_URL"] = args.base_url
    if args.results:
        setenv["TAF_RESULTS"] = args.results
    if args.headless:
        setenv["TAF_HEADLESS"] = "1"
    if args.slowmo is not None:
        setenv["TAF_SLOWMO"] = str(args.slowmo)
    if args.arrive_ms is not None:
        setenv["TAF_ARRIVE_MS"] = str(args.arrive_ms)
    if args.video:
        setenv["TAF_VIDEO"] = "1"
    if args.debug:
        setenv["TAF_DEBUG"] = "1"
    if args.rerun:
        setenv["TAF_RERUN"] = "1"
    if args.sink:
        if args.sink is True:
            meta = runner.suite_meta(args.suite) or {}
            base = meta.get("base-url", "")
            u = urllib.parse.urlparse(base)
            host = u.hostname or "localhost"
            port = ":%s" % u.port if u.port else ""
            args.sink = "ws://%s%s/bus-ws" % (host, port)
        setenv["TAF_IKC3_WS"] = args.sink
    setenv.update(dict(s.split("=", 1) for s in args.setenv))
    return setenv


def _promote(args):
    """Copy every <name>_Actual.png found under the results dir to
    <goldens>/<name>_Expected.png — the human approval step."""
    results = args.results or _latest_run()
    if not results or not os.path.isdir(results):
        print("refuse: no results dir — pass --results <run-dir or root>")
        return 2
    goldens = (args.goldens or os.environ.get("TAF_GOLDENS")
               or os.path.join(os.path.dirname(results.rstrip("/")),
                               "goldens"))
    os.makedirs(goldens, exist_ok=True)
    moved = []
    for actual in sorted(glob.glob(
            os.path.join(results, "**", "*_Actual.png"), recursive=True)):
        name = os.path.basename(actual)[:-len("_Actual.png")]
        dst = os.path.join(goldens, name + "_Expected.png")
        shutil.copyfile(actual, dst)
        moved.append(dst)
    if not moved:
        print("no *_Actual.png under %s — nothing to promote" % results)
        return 0
    for dst in moved:
        print("promoted → %s" % dst)
    return 0


def _latest_run():
    """The newest results dir under TAF_RESULTS (or ./results)."""
    root = os.environ.get("TAF_RESULTS", "results")
    dirs = sorted(glob.glob(os.path.join(root, "*")))
    return dirs[-1] if dirs else None


if __name__ == "__main__":
    sys.exit(main())
