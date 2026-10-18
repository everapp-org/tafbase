---
id: CONCEPT-dsl-v1-014-01-the-two-inputs
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The two inputs — declared and derived

## Definition

A model has two authors: a **black-box** declaration — a person writes
`suts/*.sut.model.json` from what they know of the SUT — and a
**white-box** derivation — a tool computes the draft model from SUT
artifacts (source declarations, route tables, API specs, a crawl).
`taf derive` produces a model; the loader cannot tell which author
wrote it.

## Why it exists

"Describe your app in JSON" is a tax. The honest promise is: *say what
you know, derive what the SUT already declares.* IKC3's `workflow.edn`
and `support.edn` already enumerate command surfaces; an OpenAPI spec
already lists endpoints; a running app's routes already list states.
Deriving the draft and letting the author *refine* it removes the
blank-page problem while keeping the model the single hub — derivation
is another way to write JSON, not a second pipeline.

And a derived model feeds **coverage**: `taf walk` explores; systematic
traversal generates a journey for every edge — the FSM's transitions
become the test set.

## In this project

Today: black-box only — `suts/*.sut.model.json` is hand-authored; `taf
walk` is the seeded start of traversal. Planned: `taf derive` and
edge-coverage journey generation. Lane N-13.

The input sources, by what feeds them:

| source | mode | example |
|---|---|---|
| the author | black-box | the JSON model today; BDD/Gherkin notation later |
| documents | grey | `taf derive --from-spec prd.md` — assisted extraction, never silent guessing |
| SUT artifacts | white-box | IKC3's `workflow.edn`/`support.edn`, route tables, OpenAPI → `endpoints` |
| the live SUT | white-box | a crawl: links/forms → states + edges, confidence-marked |
| existing tests | white-box | mine an old suite's locators and actions |

A derived draft carries its ignorance honestly — `underived:` for what
the source couldn't classify, `openQuestions:` for what needs a human —
never an empty field pretending confidence (the honesty schema from
RESEARCH-taf-v1-003-01's qaiq findings).

**Provenance and deviation.** The model is one; the sources are many —
so each fact's origin lives in a sidecar (`*.sut.provenance.json`), not
in the model itself: `{path: {source, confidence, last-seen}}`.
Re-derivation then **reports deviation, never overwrites and never
hides**: a deriver-owned fact that changed upstream updates the model
with a `changed:` note; a human-authored fact that now disagrees with
the source is *surfaced* (`deviates: human says X, source says Y`),
not suppressed; a human fact absent from the source is `not-in-source`.
The person reconciles; the framework only names what each side claims —
the same honesty as the refusals, applied to drift.

## Touch it

```bash
.venv/bin/python -m taf walk suts/ikc3-tracker.sut.model.json --from board --seed 7 --steps 4
```

## Neighbors

[[CONCEPT-dsl-v1-001-01-the-sut-model]],
[[CONCEPT-dsl-v1-002-01-the-seeded-walk]],
[[CONCEPT-dsl-v1-013-01-the-absorption-loop]] — derivation is how the
model absorbs the SUT's own declarations.
