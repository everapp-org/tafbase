"""taf — the tafbase command line.

    python -m taf emit --lang python <sut.model.json> -o <outdir>
    python -m taf check <sut.model.json>
"""

import argparse
import sys

from taf import emit_python, model


def main(argv=None):
    ap = argparse.ArgumentParser(prog="taf")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="validate a model, print its refusals")
    c.add_argument("model")

    e = sub.add_parser("emit", help="generate a test suite from a model")
    e.add_argument("model")
    e.add_argument("--lang", choices=["python"], required=True)
    e.add_argument("-o", "--outdir", required=True)

    args = ap.parse_args(argv)
    try:
        m = model.load(args.model)
    except model.ModelRefusal as err:
        for r in getattr(err, "refusals", []):
            print("%-40s %-16s %s" % (r["clause"], r["reason"], r["message"]))
        return 1

    if args.cmd == "check":
        print("model ok: %s" % m["sut"]["name"])
        return 0

    if args.lang == "python":
        written = emit_python.emit(m, args.outdir)
    for p in written:
        print("wrote %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
