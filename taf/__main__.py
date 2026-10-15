"""taf — the tafbase command line.

    python -m taf emit --lang python <sut.model.json> -o <outdir>
    python -m taf check <sut.model.json>
"""

import argparse
import json
import sys

from taf import emit_java, emit_python, graph, model


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

        if args.journeys:
            with open(args.journeys, encoding="utf-8") as f:
                m = graph.with_journeys(m, json.load(f)["journeys"])

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
