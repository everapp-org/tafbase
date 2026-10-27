"""taf — the tafbase command line.

    python -m taf emit --lang python <sut.model.json> -o <outdir>
    python -m taf check <sut.model.json>
    python -m taf dry-run <sut.model.json>
"""

import argparse
import json
import sys

from taf import dryrun, emit_java, emit_python, graph, model


def main(argv=None):
    ap = argparse.ArgumentParser(prog="taf")
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
