"""taf — the tafbase command line.

    python -m taf emit --lang python <sut.model.json> -o <outdir>
    python -m taf check <sut.model.json>
    python -m taf dry-run <sut.model.json>
"""

import argparse
import json
import os
import sys

from taf import dryrun, emit_java, emit_python, graph, model, runner


_CMDS = ("check", "walk", "emit", "dry-run", "env", "run", "record")

_EPILOG = """\
the cycle: check → emit → execute
  `taf run <model>` does it in one command; `taf <model>` alone is the
  dry-run report; the phases below run singly when you want them.

examples:
  taf <model>                          what would run, what it lacks
  taf run <model>                      emit + execute the suite
  taf run <model> --probe              refuse to start if the SUT is down
  taf run <model> -- -k board -v       after -- : args for the runner
  eval "$(taf env <model> --video --sink)"
  taf emit --lang java <model> -o generated/java/<sut>
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

    e = sub.add_parser("emit", help="generate a test suite from a model")
    e.add_argument("model")
    e.add_argument("--lang", choices=["python", "java"], required=True)
    e.add_argument("-o", "--outdir", required=True)
    e.add_argument("--journeys",
                   help="JSON of extra journeys to merge in (e.g. `taf walk` output)")

    d = sub.add_parser("dry-run",
                       help="report what a run would do and what it lacks")
    d.add_argument("model")
    d.add_argument("--suite",
                   help="an emitted suite dir — checks goldens and freshness")
    d.add_argument("--journeys",
                   help="JSON of extra journeys to merge in (e.g. `taf walk` output)")
    d.add_argument("--lang", choices=["python", "java"], default="python",
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
                       help="emit and execute the suite — the full cycle")
    r.add_argument("model")
    r.add_argument("--suite",
                   help="run a committed emitted suite instead of a fresh emit")
    r.add_argument("--journeys",
                   help="JSON of extra journeys to merge in (e.g. `taf walk` output)")
    r.add_argument("--lang", choices=["python", "java"], default="python",
                   help="which suite to emit and runner to call "
                        "(default: python → pytest; java → mvn test)")
    r.add_argument("--probe", dest="probe", action="store_true",
                   default=True,
                   help="preflight before running (default: on)")
    r.add_argument("--no-probe", dest="probe", action="store_false",
                   help="skip the gate: probes never run, env needs "
                        "warn instead of refusing")
    r.add_argument("--keep", action="store_true",
                   help="keep the emitted temp suite")
    # the run profile — inline TAF_* contract, no shell exports needed
    r.add_argument("--base-url", help="override the model's base-url")
    r.add_argument("--results", help="artifacts root (default: results)")
    r.add_argument("--headless", action="store_true",
                   help="headless browser (headed is the default)")
    r.add_argument("--slowmo", type=int, metavar="MS",
                   help="ms between Playwright actions — watchable runs")
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

    args = ap.parse_args(argv)
    try:
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
                slowmo=args.slowmo, video=args.video, debug=args.debug,
                rerun=args.rerun, sink=args.sink, unset=args.unset))
            return 0

        if args.cmd == "record":
            from taf import record as taf_record
            base = (args.base_url or os.environ.get("TAF_BASE_URL")
                    or m["sut"]["base-url"])
            out = args.out or "recorded-%s.json" % args.name
            taf_record.record(base, out, title=args.name,
                              needs=model.env_needs(m), m=m)
            return 0

        if args.cmd == "run":
            profile = {k: getattr(args, k) for k in
                       ("base_url", "results", "headless", "slowmo",
                        "video", "debug", "rerun", "sink")}
            return runner.run(m, suite=args.suite, lang=args.lang,
                              extra=extra, probe=args.probe,
                              setenv=dict(s.split("=", 1)
                                          for s in args.setenv),
                              keep=args.keep, profile=profile)

        written = (emit_python if args.lang == "python" else emit_java).emit(m, args.outdir)
        for p in written:
            print("wrote %s" % p)
        return 0
    except model.ModelRefusal as err:
        for r in getattr(err, "refusals", []):
            print("%-40s %-16s %s" % (r["clause"], r["reason"], r["message"]))
        return 1


if __name__ == "__main__":
    sys.exit(main())
