---
id: CONCEPT-taf-v1-007-01-the-three-levels
status: draft
subproject: taf
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The three levels

## Definition

tafbase is three activities, not one — and the reader is always only
one of them at a time:

- **Build** — the framework itself: the loader, the emitters, the
  parity contract. Artifact: `taf/`, `tests/`.
- **Model** — applying the DSL to one SUT: declaring its states,
  elements, actions, journeys. Artifact: `suts/*.sut.model.json`.
- **Use** — the generated suite running under the framework. Artifact:
  `generated/`.

## Why it exists

The DSL First promise is a level boundary: the model author benefits
without knowing the machinery — no metaprogramming, no emitters, no
compiler mechanics. The promise is kept by keeping the levels apart:
`suts/` is data to level 1, authored input to level 2, and invisible to
level 3 (who only ever sees generated code).

## In this project

The repo layout *is* the separation: `taf/` is Build, `suts/` is
Model, `generated/` is Use. SPEC-taf-v1-001-04 mirrors it — Parts 1–2
are the model author's surface, Part 3 the framework's contract.
CONTRIBUTING.md is the Build level's handbook; `suts/` and `generated/`
each carry their own doc.

## Touch it

```bash
python -m taf check suts/ikc3-tracker.sut.model.json   # Model level
.venv/bin/python -m pytest tests -q                     # Build level
.venv/bin/python -m pytest generated/python/ikc3-tracker -q  # Use level
```

## Neighbors

[[CONCEPT-dsl-v1-001-01-the-sut-model]] (level 2's subject),
[[CONCEPT-taf-v1-001-01-the-learning-path]] (which personas take which
path).
