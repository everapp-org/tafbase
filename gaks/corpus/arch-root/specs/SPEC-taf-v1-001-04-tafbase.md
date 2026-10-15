---
id: SPEC-taf-v1-001-04-tafbase
status: draft
subproject: taf
authored: 2026-10-15
authors:
  - George Petrov
  - Devin
supersedes:
  - "[[SPEC-taf-v1-001-03-the-sut-language]]"
---

# SPEC-taf-v1-001-04 — tafbase

## Purpose

tafbase is a test automation framework. You describe a system under test
(SUT) once — its screens, its controls, the journeys that matter — and
tafbase generates runnable browser and API test suites: pytest +
Playwright for Python, JUnit 5 + Playwright for Java.

The description is a small DSL — but using tafbase needs no knowledge of
languages or code generation. You fill in a JSON form; the framework
turns it into tests you can read, run, and review. Everything in this
document is about what you declare and what you get.

This document stands alone. Keywords **must**, **must not**, **should**,
and **may** are normative in the RFC 2119 sense. Clauses carry
identifiers (`TAF-n`) so a test, a review, or a refusal names what it
verifies.

Related:
  - [[PLAN-taf-v1-001-01-tafbase]]
  - [[ADR-taf-v1-001-01-tafbase-stands-alone]]
  - [[ADR-taf-v1-002-01-the-learning-surface]]

## Terms

| term | meaning |
|---|---|
| SUT | the system under test — the application a generated suite exercises |
| model | your declaration of a SUT, written in tafbase's DSL |
| state | a recognizable place in the SUT, proven by its marker |
| marker | a locator a generated test asserts visible on arrival |
| locator | one way to find an element — role+name, label, text, placeholder, testid, css, xpath |
| action | a named step the SUT offers; with `from`/`to` it is an edge |
| journey | a named path through the SUT; compiled to one test |
| refusal | a named rejection `{clause, reason, message}`; a rejected model emits nothing |
| emitter | a generator: a model in, a runnable suite out |
| manifest | `taf.manifest.json` — maps each generated test to your model's elements |
| walk | a journey the tool derives by traversing the graph, replayable by seed |

# Part 1 — What you declare

## TAF-1 · States are recognized, not assumed

A state is where a journey can be — a page, a dialog, a verified
condition. It declares a `marker`: the visible proof. A test arrives at
a state only when the SUT shows that proof. A state may also declare a
`route`, the address that reaches it directly.

## TAF-2 · Locators form a ladder

A locator takes exactly one form. The forms are ordered by what a user
perceives, and the order is a rule of the framework, not a style guide:

| rung | form | standing |
|---|---|---|
| 1 | `role` + `name` | how a user names a control — preferred |
| 2 | `label` / `text` / `placeholder` | what a user reads |
| 3 | `testid` | a deliberate testing hook |
| 4 | `css` / `xpath` | structure, fragile — flagged in the manifest |

The shape of a locator chooses its rung; you never declare one. Named
locators are declared once in `elements` and used by name everywhere.

## TAF-3 · Actions are edges

An action is a step the SUT offers. An action with `from` and `to` is an
edge of the SUT's graph — which is also what `taf walk` traverses, so a
model serves journeys, walks, and coverage without being written twice.
An action's `do` list composes steps: act (`click`, `fill`, `check`,
`select`), move (`navigate`), observe (`wait-for`, `expect`), call the
API (`api`, `save`).

## TAF-4 · Journeys are paths

A journey is a path through the SUT: a `start` state, then named actions
that chain — each action's `to` is the next action's `from` — or inline
steps in the same step language. `expect-final` names the state the
journey must end in. One journey becomes exactly one test.

## TAF-5 · Endpoints declare the API surface

An endpoint names an HTTP call — `method`, `path`, expected `status`.
An `api` step invokes it inside a journey: one test can drive the UI and
verify the API. `{name}` markers in a path bind from the step's `args`;
`save` captures a response value for a later `expect`.

# Part 2 — What you write

A model is one JSON document, `*.sut.model.json` by convention:

```json
{
  "sut":       {"name": "ikc3-tracker", "base-url": "http://127.0.0.1:4856"},
  "states":    {"board": {"route": "/index.html?island=board",
                          "marker": {"css": ".ikc-dock-theme"}}},
  "elements":  {"new-ticket-button": {"role": "button", "name": "New ticket"}},
  "actions":   {"open-tot": {"from": "board", "to": "tot",
                             "do": [{"navigate": "tot"}]}},
  "journeys":  {"board-to-tot": {"start": "board", "steps": ["open-tot"],
                                 "expect-final": {"state": "tot"}}},
  "endpoints": {"move-ticket": {"method": "POST",
                                "path": "/api/tickets/{id}/move",
                                "expect": {"status": 200}}}
}
```

- `sut.name` and `sut.base-url` are required; `elements`, `actions`,
  `endpoints` may be absent or empty.
- Step forms: `click`/`check`/`select` take an element name; `fill`
  takes `{element, value}`; `navigate` and `wait-for` take a state or
  element name; `api` takes an endpoint name plus optional `args`;
  `save` takes `{name: "$.json.path"}`; `expect` takes `{element,
  assertion}` or `{saved, assertion}`.
- A journey's `steps` is either all action names or all inline step
  objects — the two forms do not mix.

# Part 3 — What tafbase guarantees

## TAF-6 · Honest refusals

A broken model is refused, in full, with named reasons — tafbase never
guesses and never half-emits. Each refusal is `{clause, reason,
message}`:

| reason | the framework refuses when |
|---|---|
| `:not-json` | the document is not a JSON object |
| `:missing-field` | a required key is absent |
| `:empty-model` | no states and no journeys |
| `:duplicate-name` | a name is declared twice in one clause |
| `:bad-locator` | a locator matches no rung of TAF-2 |
| `:unknown-state` | `from`/`to`/`start`/`expect-final`/`navigate`/`wait-for` declares no state |
| `:unknown-element` | a step declares no element |
| `:unknown-endpoint` | an `api` step declares no endpoint |
| `:unknown-action` | a journey step declares no action |
| `:unknown-step` | a step's key is no form of TAF-3 |
| `:edge-gap` | named actions in a journey do not chain |
| `:mixed-steps` | a journey mixes named actions and inline steps |
| `:unreachable` | a state lies on no path from any journey's `start` |

## TAF-7 · Real, reviewable suites

Generation must produce code a person reviews: one test per journey —
arrange the start state, run the steps in order, assert each arrival's
marker, assert `expect-final` last — plus page objects, fixtures, and a
manifest, in the target language's own idiom. Emitted suites are
committed artifacts; you read the diff, not a generator's promise.

## TAF-8 · Both languages, one meaning

Every emitter agrees on one model: same tests modulo language idiom,
same step order, same assertions, byte-identical manifest — and the same
refusals for a broken model. Divergence is a defect of the emitters,
never of the model.

## TAF-9 · The suite knows where it came from

Every generated file must carry `@concept` citations to the corpus, and
the manifest must map each test to the model elements that produced it.
A failing test names its model element; the result sink files the fault
report against it.

## Verification

| clause | verified by |
|---|---|
| TAF-1…TAF-6 | `tests/test_model.py` — the accept path and every refusal |
| TAF-7 | `tests/test_emit_python.py`, generated `taf.manifest.json` |
| TAF-8 | `tests/test_parity.py` — T-taf-003, byte-identical manifest |
| live run | `tests/test_live.py` — T-taf-004/005, opt-in `TAF_LIVE=1` |
| walks | `tests/test_graph.py` — T-taf-006 |

## Out of scope in v1

Test data management, authentication flows, multi-environment `env`
indirection, screenshot/video configuration, visual assertions, and
walk-generation strategies beyond the seeded walk — each is a declared
lane in [[PLAN-taf-v1-001-01-tafbase]], none is guessed here.
