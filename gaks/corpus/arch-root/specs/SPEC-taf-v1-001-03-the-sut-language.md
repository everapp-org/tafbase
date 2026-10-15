---
id: SPEC-taf-v1-001-03-the-sut-language
status: draft
subproject: taf
authored: 2026-10-15
authors:
  - George Petrov
  - Devin
supersedes:
  - "[[SPEC-taf-v1-001-02-the-sut-model]]"
---

# SPEC-taf-v1-001-03 — the SUT language

## Purpose

tafbase is a DSL First test automation framework. Its input is a small
language for declaring a system under test (SUT): the states a user can
reach, the actions that move between them, and the journeys a suite must
prove. From one declaration, emitters compile runnable browser and API
test suites — Playwright for Python and Java today.

This document specifies that language. Part 1 gives the language's
constructs and their meaning — the abstract syntax. Part 2 gives the JSON
form a model author writes — the concrete syntax. Part 3 gives the
contract every implementation must honor: loading, refusals, emission,
parity.

This document stands alone. Keywords **must**, **must not**, **should**,
and **may** are normative in the RFC 2119 sense. Clauses carry
identifiers (`SL-n`) so a test, a review, or a refusal names what it
verifies.

Related:
  - [[PLAN-taf-v1-001-01-tafbase]]
  - [[ADR-taf-v1-001-01-tafbase-stands-alone]]
  - [[ADR-taf-v1-002-01-the-learning-surface]]

## Terms

| term | meaning |
|---|---|
| DSL | domain-specific language — here, the language this document defines |
| SUT | the system under test — the application a generated suite exercises |
| model | a program in the SUT language: one declaration of a SUT |
| state | a recognizable place in the SUT, proven by its marker |
| marker | a locator a generated test asserts visible on arrival |
| locator | one way to find an element — role+name, label, text, placeholder, testid, css, xpath |
| action | a named step the SUT offers; with `from`/`to` it is an edge |
| journey | a named path through the graph; compiled to one test |
| refusal | a named rejection `{clause, reason, message}`; a rejected model emits nothing |
| emitter | a compiler backend: a model in, a runnable suite out |
| manifest | `taf.manifest.json` — maps each emitted test to its model elements |

# Part 1 — The constructs

## SL-1 · States are recognized, not assumed

A state is where a journey can be. It declares a `marker` — the proof —
and may declare a `route`, the address that reaches it directly. A test
arrives at a state only when the SUT shows the marker. This is the
language's core semantics: a state is proven, never presumed.

## SL-2 · Locators form a ladder

A locator takes exactly one form, and the forms are ordered by what a
user perceives:

| rung | form | standing |
|---|---|---|
| 1 | `role` + `name` | how a user names a control — preferred |
| 2 | `label` / `text` / `placeholder` | what a user reads |
| 3 | `testid` | a deliberate testing hook |
| 4 | `css` / `xpath` | structure, fragile — flagged in the manifest |

The ladder is a language rule, not a style guide: the shape of a locator
chooses its rung, and rung 4 carries a `fragile` mark into the manifest.

## SL-3 · Actions are edges

An action is a step the SUT offers. An action that declares `from` and
`to` is an edge of the SUT's graph — the same graph the MBT lanes walk
(`taf walk`), so a model is written once and serves journeys, walks, and
coverage. An action's `do` list composes steps: act (`click`, `fill`,
`check`, `select`), move (`navigate`), observe (`wait-for`, `expect`),
call the API (`api`, `save`).

## SL-4 · Journeys are paths

A journey is a path through the graph: a `start` state, then named
actions that chain — each action's `to` is the next action's `from` — or
inline steps in the same step language. `expect-final` names the state
the journey must end in. One journey compiles to exactly one test.

## SL-5 · Endpoints declare the API surface

An endpoint names an HTTP call — `method`, `path`, expected `status`.
An `api` step invokes it inside a journey, so a test can drive the UI
and verify the API in one path. `{name}` markers in a path bind from the
step's `args`; `save` captures a response value for a later `expect`.

# Part 2 — The JSON form

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
- Step forms in `do` and in inline journey steps: `click`/`check`/`select`
  take an element name; `fill` takes `{element, value}`; `navigate` and
  `wait-for` take a state or element name; `api` takes an endpoint name
  plus optional `args`; `save` takes `{name: "$.json.path"}`; `expect`
  takes `{element, assertion}` or `{saved, assertion}`.
- A journey's `steps` is either all action names or all inline step
  objects — the two forms do not mix.

# Part 3 — The contract

## SL-6 · Loading and refusals

The loader reads one JSON document and returns either a validated model
or the complete list of refusals, each `{clause, reason, message}`; a
refused model emits nothing.

| reason | the language refuses when |
|---|---|
| `:not-json` | the document is not a JSON object |
| `:missing-field` | a required key is absent |
| `:empty-model` | no states and no journeys |
| `:duplicate-name` | a name is declared twice in one clause |
| `:bad-locator` | a locator matches no rung of SL-2 |
| `:unknown-state` | `from`/`to`/`start`/`expect-final`/`navigate`/`wait-for` declares no state |
| `:unknown-element` | a step declares no element |
| `:unknown-endpoint` | an `api` step declares no endpoint |
| `:unknown-action` | a journey step declares no action |
| `:unknown-step` | a step's key is no form of SL-3 |
| `:edge-gap` | named actions in a journey do not chain |
| `:mixed-steps` | a journey mixes named actions and inline steps |
| `:unreachable` | a state lies on no path from any journey's `start` |

## SL-7 · Emission

An emitter must produce a runnable suite in which every journey becomes
exactly one test that: arranges the start state, runs each step in
order, asserts each action's `to` marker on arrival, and asserts
`expect-final` last. A suite must include `taf.manifest.json` mapping
each test to its journey, actions, and states.

## SL-8 · Parity

All emitters agree on the same model. For a valid model: the same tests,
step order, assertion sequence, and a byte-identical manifest — modulo
language idiom (naming, imports, file layout). For a broken model: the
identical refusal list. Divergence is a defect of the emitters, never of
the model.

## SL-9 · Citations

Each emitted file must carry `@concept CONCEPT-taf-v1-NNN-NN-*` comment
lines naming the corpus concepts it demonstrates; the corpus checker's
`code-link-unresolved` refuses a citation with no document.
(ADR-taf-v1-002-01 — generated code is teaching material.)

## Verification

| clause | verified by |
|---|---|
| SL-1…SL-6 | `tests/test_model.py` — the accept path and every refusal |
| SL-7 | `tests/test_emit_python.py`, generated `taf.manifest.json` |
| SL-8 | `tests/test_parity.py` — T-taf-003, byte-identical manifest |
| live run | `tests/test_live.py` — T-taf-004/005, opt-in `TAF_LIVE=1` |
| walks | `tests/test_graph.py` — T-taf-006 |

## Out of scope in v1

Test data management, authentication flows, multi-environment `env`
indirection, screenshot/video configuration, visual assertions, and
walk-generation strategies beyond the seeded walk — each is a declared
lane in [[PLAN-taf-v1-001-01-tafbase]], none is guessed here.
