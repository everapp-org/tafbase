# Modeling a SUT

You are the **model author** — the middle level of
[CONCEPT-taf-v1-007-01](../arch-root/concepts/CONCEPT-taf-v1-007-01-the-three-levels.md).
You need no knowledge of emitters, metaprogramming, or codegen. You
declare; the framework does the rest.

## The loop

```bash
# 1. Write your model — copy the tracker as a starting shape
cp suts/ikc3-tracker.sut.model.json suts/my-app.sut.model.json

# 2. Check it — every problem is named, all of them at once
.venv/bin/python -m taf check suts/my-app.sut.model.json

# 3. Emit the suites
.venv/bin/python -m taf emit --lang python suts/my-app.sut.model.json -o generated/python/my-app
.venv/bin/python -m taf emit --lang java   suts/my-app.sut.model.json -o generated/java/my-app

# 4. Run them
.venv/bin/python -m pytest generated/python/my-app -q
```

## What you declare

Read the [model spec](../arch-root/specs/SPEC-taf-v1-001-04-tafbase.md)
for the contract; in short:

- `states` — pages, each with a `route` and a `marker` that proves
  arrival (a locator).
- `elements` — named locators; prefer the ladder's upper rungs
  (`role`, `label`, `text`, `testid`), not `css`/`xpath`.
- `actions` — the SUT's steps, `from`/`to` edges with a `do` list of
  steps (`navigate`, `click`, `fill`, `wait-for`, `expect`, `api`,
  `dwell`, `wait-any`, `maybe`), plus a `title` the run narrates.
- `journeys` — paths through states; `expect-final` names where a
  journey must end.
- `endpoints` — HTTP calls an `api` step can make mid-journey.

## Rules that keep the model honest

- A broken model is refused, with every reason named — never guessed.
- One journey becomes exactly one test.
- `states` must all be journey-reachable.
- A journey's `steps` are all action names or all inline steps — not
  mixed.

The concepts are under `dsl` in the corpus — the step language, the
locator ladder, waits, the walk — each one page, each runnable.
