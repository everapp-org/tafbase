"""The SUT graph — lane TAF/PLAN-taf-v1-001-01/F-6.

@concept CONCEPT-dsl-v1-002-01-the-seeded-walk

Actions already declare `from`/`to`, so the model IS a graph; nothing new
to declare. `walk` derives a journey by seeded traversal — deterministic,
so a found failure replays exactly (`--seed`). The output is a journey
declaration in the model's own shape: data to review, merge, and emit —
never an interpreter's private plan.
"""
import random

from taf.model import ModelRefusal


def _refuse(clause, reason, message):
    """One ModelRefusal in the loader's shape: message + .refusals list."""
    err = ModelRefusal(message)
    err.refusals = [{"clause": clause, "reason": reason, "message": message}]
    return err


def edges(m):
    """{from-state: [(action, to-state), ...] sorted}. An action with no
    `to` changes no state, so it is not an edge."""
    adj = {}
    for name, a in m["actions"].items():
        fr, to = a.get("from"), a.get("to")
        if fr and to:
            adj.setdefault(fr, []).append((name, to))
    for v in adj.values():
        v.sort()
    return adj


def walk(m, start, seed, steps, cover=False):
    """A seeded walk of `steps` actions from `start`; returns a journey
    dict {start, steps, expect-final}. `cover` prefers edges this walk
    has not taken yet (still seeded — ties break deterministically).
    Stops early at a state with no outgoing edges; refuses a walk that
    cannot take one step."""
    if start not in m["states"]:
        raise _refuse("walk", "unknown-state",
                      f"walk starts at undeclared state '{start}'")
    rng = random.Random(seed)
    adj = edges(m)
    seq, here, taken = [], start, set()
    for _ in range(steps):
        outs = adj.get(here, [])
        if not outs:
            break
        cand = outs
        if cover:
            fresh = [e for e in outs if e[0] not in taken]
            if fresh:
                cand = fresh
        name, to = cand[rng.randrange(len(cand))]
        seq.append(name)
        taken.add(name)
        here = to
    if not seq:
        raise _refuse("walk", "dead-end",
                      f"state '{start}' has no outgoing actions")
    return {"start": start, "steps": seq, "expect-final": {"state": here}}


def with_journeys(m, extra):
    """The model with generated journeys merged in — a copy, the model
    file untouched. A name a journey already uses is a duplicate-name
    refusal, the same clause the loader enforces."""
    merged = dict(m)
    merged["journeys"] = dict(m["journeys"])
    for name, j in extra.items():
        if name in merged["journeys"]:
            raise _refuse("journeys", "duplicate-name",
                          f"journey '{name}' is declared twice")
        merged["journeys"][name] = j
    return merged
