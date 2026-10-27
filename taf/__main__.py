"""taf — the tafbase command line.

    python -m taf emit --lang python <sut.model.json> -o <outdir>
    python -m taf check <sut.model.json>
    python -m taf dry-run <sut.model.json>
"""

import argparse
import json
import sys

from taf import dryrun, emit_java, emit_python, graph, model, runner


_CMDS = ("check", "walk", "emit", "dry-run", "env", "run")

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
    r.add_argument("--probe", action="store_true",
                   help="preflight: refuse to start while a probe finding "
                        "is missing")
    r.add_argument("--keep", action="store_true",
                   help="keep the emitted temp suite")

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

        if args.cmd == "run":
            return runner.run(m, suite=args.suite, lang=args.lang,
                              extra=extra, probe=args.probe,
                              keep=args.keep)

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
