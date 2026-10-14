---
id: SPEC-taf-v1-001-01-the-sut-model
status: draft
subproject: taf
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# SPEC-taf-v1-001-01 — the SUT model

Related:
  - [[PLAN-taf-v1-001-01-tafbase]]
  - [[ADR-taf-v1-001-01-tafbase-stands-alone]]

The design input of lane TAF/PLAN-taf-v1-001-01/A-1. This document is the
contract: a loader and an emitter are correct together when each refusal and
each generated behavior below holds.

## Purpose

A system under test (SUT) is declared once, as one JSON document. The
declaration is the model. From it, emitters write runnable suites
(Python+Playwright, later Java+Playwright) that follow Playwright's own
rules: semantic locators, auto-waiting assertions, one journey per test.
The same document is the graph the MBT lanes walk later — states and
transitions are first-class from v1, so no model is written twice.

## The document

One file per SUT, `sut.model.json` by convention. Top level:

```json
{
  "sut":       {"name": "ikc3-tracker", "base-url": "http://127.0.0.1:4855"},
  "states":    {},
  "elements":  {},
  "actions":   {},
  "journeys":  {},
  "endpoints": {}
}
```

### `sut`

`name` (string, required) names the SUT in refusals and the manifest.
`base-url` (string, required) is where journeys begin. No environment
indirection in v1: a different deployment is a different file, or a later
lane adds `env`.

### `states`

A state is a place a journey can be — a page, a dialog, a verified
condition. A state is recognized, not assumed:

```json
"states": {
  "board": {
    "route": "/index.html?island=board",
    "marker": {"role": "heading", "name": "Board"}
  }
}
```

`route` (optional) is the path under `base-url` that reaches the state
directly. `marker` (required) is a locator that a generated test asserts
visible after every arrival — a state is entered only when the SUT proves
it. That one rule is what makes generated tests self-verifying instead of
hopeful.

### `elements`

Named locators, declared once, reused everywhere:

```json
"elements": {
  "new-ticket-button": {"role": "button", "name": "New ticket"},
  "title-field":       {"label": "Title"},
  "report-card":       {"testid": "report-card"},
  "legacy-panel":      {"css": ".panel--legacy"}
}
```

THE LOCATOR LADDER is the "proper use" clause, encoded, not documented:

1. `role` + `name` — the accessibility query, preferred
2. `label` / `text` / `placeholder` — user-visible queries
3. `testid` — the deliberate escape (`data-testid`)
4. `css` / `xpath` — the last resort, allowed and flagged `fragile` in the
   manifest

A locator with no usable form is refused `:bad-locator`. The ladder is the
emitter's only ordering; a model does not say which rung a locator sits on,
the shape does.

### `actions`

An action is a step the SUT offers — the transitions of the graph:

```json
"actions": {
  "move-to-triage": {
    "from": "backlog",
    "to":   "triage",
    "do":   [
      {"click": "new-ticket-button"},
      {"fill":  {"element": "title-field", "value": "the report"}},
      {"click": "save-button"},
      {"api":   "move-ticket", "args": {"category": "triage"}}
    ]
  }
}
```

`from` and `to` name states and are optional per action, required for the
graph to be a graph: an action with both is an edge. `do` is an ordered
list of steps:

- `click` / `fill` / `check` / `select` — on a named element
- `navigate` — to a state's `route`
- `wait-for` — on an element or state marker
- `api` — a named endpoint, with `args`; asserts the declared status
- `expect` — an assertion on an element (`visible`, `hidden`,
  `text`, `count`, `attr`) or on a saved value

### `journeys`

A journey is a named path — the v1 test:

```json
"journeys": {
  "file-and-triage": {
    "start": "board",
    "steps": ["open-ticket", "fill-what", "save", "see-in-backlog"],
    "expect-final": {"state": "triage"}
  }
}
```

`steps` name actions; the emitter emits one test per journey, asserting
each action's `to` marker on arrival and `expect-final` at the end. A
journey may inline a step list of the same step forms as `do` — a journey
is a path, whichever way it is written, but the two forms are not mixed.

### `endpoints`

The API-testing surface, declared like the rest:

```json
"endpoints": {
  "list-tickets": {"method": "GET",  "path": "/api/tickets",
                   "expect": {"status": 200}},
  "move-ticket":  {"method": "POST", "path": "/api/tickets/{id}/move",
                   "expect": {"status": 200}}
}
```

A journey's `api` step calls one; the emitted code asserts `expect.status`
and may `save` a JSON path (`"save": {"count": "$.length"}`) for a later
`expect` step. Deeper response assertions are an MBT-era lane, not v1.

## Refusals

A broken model is refused, named, and silent elsewhere — the loader gives
every refusal as `{clause, reason, message}` and emits nothing:

| reason | when |
|---|---|
| `:empty-model` | no states and no journeys |
| `:bad-locator` | an element matches no rung of the ladder |
| `:unknown-state` | `from`/`to`/`start`/`expect-final` names no state |
| `:unknown-element` | a step names no element |
| `:unknown-endpoint` | an `api` step names no endpoint |
| `:unknown-action` | a journey names no action |
| `:edge-gap` | a journey's steps do not chain (`to` of one ≠ `from` of next) |
| `:unreachable` | a state has no path from any journey's `start` |
| `:duplicate-name` | a name declared twice in one clause |

Both emitters must produce the identical refusal list for the identical
broken model — refusal parity is tested, per the discipline of
PLAN-ikc-v3-079-01.

## The manifest

Every emitted suite writes `taf.manifest.json` beside the tests: for each
test id, the model elements it came from (journey → actions → elements →
state markers → endpoints). This is the traceability clause — a failing
test names its model element, and the tracker adapter files the fault
report against it.

## The parity contract

Two emitters agree when, for the same valid model: same test names, same
step order, same assertions, same manifest contents (byte-identical),
same file tree modulo language idioms (imports, casing). For the same
broken model: the same refusal list. Divergence is a defect of the
emitters, never of the model.

## Out of scope in v1

Test data management, authentication flows, multi-environment `env`,
screenshot/video configuration, visual assertions, and the graph walks
themselves (random, coverage-directed, journal-replay) — each is a
declared lane in the plan, none is guessed at here.
