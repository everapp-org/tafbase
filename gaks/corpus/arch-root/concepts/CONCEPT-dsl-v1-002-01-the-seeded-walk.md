---
id: CONCEPT-dsl-v1-002-01-the-seeded-walk
status: draft
subproject: dsl
authored: 2026-10-15
authors:
  - George Petrov
  - Devin
---

# The seeded walk

## Definition

A random test is only useful if it can fail twice. A seeded walk drives a
pseudo-random number generator with a recorded seed, so the "random"
journey it derived is exactly reproducible: same model, same start, same
seed — the same steps. The walk's output is a journey declaration in the
model's own JSON shape, so the replay is data you can commit, review, and
emit — not a log file only a runner understands.

```
python -m taf walk model.json --from board --seed 42 --steps 6 > walk.json
python -m taf emit --lang python model.json -o suite --journeys walk.json
```

## Why it exists

MBT without replay is a bug report that says "it failed once." Seed
replay turns exploration into a regression asset: commit the seed (or the
derived journey), and the failure is a named test forever. `--cover`
prefers untaken edges — the first step toward coverage-directed
generation.

## In this repo

`taf/graph.py` — `edges` derives adjacency from declared `from`/`to`;
`walk` traverses it under `random.Random(seed)`; `with_journeys` merges
derived journeys into a copy of the model. T-taf-006 proves determinism,
coverage, and the merge path.
