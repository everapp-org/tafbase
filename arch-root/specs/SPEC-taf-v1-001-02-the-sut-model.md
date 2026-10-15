---
id: SPEC-taf-v1-001-02-the-sut-model
status: draft
subproject: taf
authored: 2026-10-15
authors:
  - George Petrov
  - Devin
supersedes:
  - "[[SPEC-taf-v1-001-01-the-sut-model]]"
---

# SPEC-taf-v1-001-02 — the SUT model

## Purpose

tafbase is a test automation framework: a web application is described
once, as one JSON document, and that document is compiled into runnable
browser and API test suites — Playwright for Python and Java today.

This document specifies that JSON document. It is the contract between
a model author and the emitters: the implementation is correct when all
clauses in this document hold. Read this document on its own — it uses
no other document of this project.

Keywords **must**, **must not**, **should**, and **may** are normative,
in the RFC 2119 sense. Clauses carry identifiers (`SM-n`) so a test, a
review, or a refusal can name what it verifies.

Related:
  - [[PLAN-taf-v1-001-01-tafbase]]
  - [[ADR-taf-v1-001-01-tafbase-stands-alone]]
  - [[ADR-taf-v1-002-01-the-learning-surface]]

## Terms

| term | meaning |
|---|---|
| SUT | the *system under test* — the application the generated suite exercises |
| model | one JSON document declaring a SUT's states, elements, actions, journeys, endpoints |
| state | a recognizable place in the SUT — a page, a dialog — proven by its marker |
| marker | a locator a generated test asserts visible on arrival at a state |
| locator | one form of finding an element — role+name, label, text, placeholder, testid, css, xpath |
| action | a named step the SUT offers; with `from`/`to` it is an edge of the graph |
| journey | a named path through the graph; emitted as one test |
| refusal | a named rejection `{clause, reason, message}`; a broken model emits nothing |
| emitter | a code generator: a model in, a runnable suite out |
| manifest | `taf.manifest.json` — emitted beside the tests, mapping each test to its model elements |

## SM-1 · One file, JSON

A SUT is declared in one file, `*.sut.model.json` by convention. It
**must** be a JSON object; a document that is not is refused
`:not-json`. A name declared twice in one clause is refused
`:duplicate-name` — JSON's silent last-write-wins is not accepted.

Top level:

```json
{
  "sut":       {"name": "ikc3-tracker", "base-url": "http://127.0.0.1:4856"},
  "states":    {},
  "elements":  {},
  "actions":   {},
  "journeys":  {},
  "endpoints": {}
}
```

`sut.name` and `sut.base-url` are required (`:missing-field`). A model
with no states and no journeys is refused `:empty-model`. `elements`,
`actions`, and `endpoints` **may** be absent or empty.

## SM-2 · States are recognized, not assumed

```json
"states": {
  "board": {"route": "/index.html?island=board",
            "marker": {"role": "heading", "name": "Board"}}
}
```

A state **must** declare `marker`, a locator (SM-3); a generated test
**must** assert it visible on every arrival — the SUT proves the state,
the test does not assume it (`:missing-field` without one). `route` is
optional; when present it is the path under `base-url` that reaches the
state directly.

A state no journey can reach is refused `:unreachable` — a declared
state with no path to it is a dead declaration.

## SM-3 · The locator ladder

A locator **must** take exactly one preferred form, in order:

| rung | form | standing |
|---|---|---|
| 1 | `role` + `name` | the accessibility query — preferred |
| 2 | `label` / `text` / `placeholder` | user-visible queries |
| 3 | `testid` | the deliberate escape, `data-testid` |
| 4 | `css` / `xpath` | the last resort; the manifest **must** flag it `fragile` |

The ladder is encoded, not documented: the shape of a locator chooses
its rung; a model never declares one. A locator matching no rung is
refused `:bad-locator`. Elements are named locators declared once in
`elements` and referenced by name everywhere else; a reference to a name
that is not declared is refused `:unknown-element`.

## SM-4 · Actions are edges

```json
"actions": {
  "move-to-triage": {
    "from": "backlog", "to": "triage",
    "do": [{"click": "new-ticket-button"},
           {"fill": {"element": "title-field", "value": "the report"}},
           {"api": "move-ticket", "args": {"category": "triage"}}]
  }
}
```

`from`/`to` name states (`:unknown-state` otherwise). An action with
both is an edge of the graph — the same declaration the MBT lanes walk
(`taf walk`), so no model is written twice. `do` is an ordered list of
steps, each exactly one of:

| step | argument | semantics |
|---|---|---|
| `click` / `check` / `select` | element name | act on the element |
| `fill` | `{element, value}` | set the element's value |
| `navigate` | state name | go to the state's `route` |
| `wait-for` | element name or state name | wait for visibility |
| `api` | endpoint name + optional `args` | call it; assert its `expect.status` (SM-6) |
| `save` | `{name: "$.json.path"}` | remember a response value |
| `expect` | `{element, assertion…}` or `{saved, …}` | assert on element or saved value |

A step key that is none of these is refused `:unknown-step`.

## SM-5 · Journeys are paths, one per test

```json
"journeys": {
  "file-and-triage": {"start": "board",
                      "steps": ["open-ticket", "fill-what", "save"],
                      "expect-final": {"state": "triage"}}
}
```

A journey **must** declare `start`, a state (`:missing-field`,
`:unknown-state`). `steps` **must** be either a list of action names or
a list of inline step objects — never both in one journey
(`:mixed-steps`); a name that is no action is refused `:unknown-action`.
Named-action steps **must** chain: the `to` of one is the `from` of the
next, and the first starts at `start` (`:edge-gap`). `expect-final` is
optional; its `state` is asserted at the end of the emitted test.

The emitter **must** emit exactly one test per journey, in which the
journey's start state is arranged, each action's `to` marker is asserted
on arrival, and `expect-final` is asserted last.

## SM-6 · Endpoints — the API surface

```json
"endpoints": {
  "move-ticket": {"method": "POST", "path": "/api/tickets/{id}/move",
                  "expect": {"status": 200}}
}
```

`method` and `path` are required (`:missing-field`); `{name}` markers in
`path` are substituted from the step's `args`. An `api` step **must**
name a declared endpoint (`:unknown-endpoint`), and the emitted test
**must** assert the response status equals `expect.status` (default
200). A `save` step **may** capture a dotted JSON path for a later
`expect` step.

## SM-7 · Refusals

A broken model is refused, named, and silent: the loader returns the
complete list of `{clause, reason, message}` and no emitter runs.

| reason | clause |
|---|---|
| `:not-json` | the document is not a JSON object |
| `:missing-field` | a required key is absent |
| `:empty-model` | no states and no journeys |
| `:bad-locator` | a locator matches no rung of SM-3 |
| `:unknown-state` | a name in `from`/`to`/`start`/`expect-final`/`navigate`/`wait-for` declares no state |
| `:unknown-element` | a step names no element |
| `:unknown-endpoint` | an `api` step names no endpoint |
| `:unknown-action` | a journey names no action |
| `:unknown-step` | a step's key is no form of SM-4 |
| `:edge-gap` | a journey's named actions do not chain |
| `:mixed-steps` | a journey mixes named actions and inline steps |
| `:unreachable` | a state has no path from any journey's `start` |
| `:duplicate-name` | a name declared twice in one clause |

## SM-8 · The manifest

Every emitted suite **must** contain `taf.manifest.json`: for each test,
its journey, the actions and states it crosses. The manifest names no
language — it describes the suite's semantics, so two emitters' copies
are byte-identical (SM-9). This is the traceability clause: a failing
test names its model element, and a result sink files the fault report
against it.

## SM-9 · Parity

Every emitter agrees on the same model. For a valid model: the same test
names modulo language idiom, the same step order, the same assertion
sequence, a byte-identical manifest, the same file tree modulo language
idiom. For a broken model: the identical refusal list — in v1 this holds
by construction, because all emitters run behind the shared loader.
Divergence is a defect of the emitters, never of the model.

## SM-10 · Citations

Each emitted file **must** carry `@concept CONCEPT-taf-v1-NNN-NN-*`
comment lines naming the corpus concepts it demonstrates, and the corpus
checker's `code-link-unresolved` **must** refuse a citation with no
document. (ADR-taf-v1-002-01 — generated code is teaching material.)

## Verification

| clause | verified by |
|---|---|
| SM-1…SM-7 | `tests/test_model.py` — the accept path and every refusal |
| SM-5, SM-8 | `tests/test_emit_python.py`, generated `taf.manifest.json` |
| SM-9 | `tests/test_parity.py` — T-taf-003, byte-identical manifest |
| live run | `tests/test_live.py` — T-taf-004, opt-in `TAF_LIVE=1` |
| walks | `tests/test_graph.py` — T-taf-006 |

## Out of scope in v1

Test data management, authentication flows, multi-environment `env`
indirection, screenshot/video configuration, visual assertions, and the
graph walks' generation strategies beyond the seeded walk — each is a
declared lane in [[PLAN-taf-v1-001-01-tafbase]], none is guessed here.
