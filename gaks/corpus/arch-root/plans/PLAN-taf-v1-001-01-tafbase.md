---
id: PLAN-taf-v1-001-01-tafbase
subproject: taf
status: in-progress
type: implementation-plan
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# PLAN-taf-v1-001-01 — tafbase: a DSL First test automation framework

Status: in progress

tafbase declares a system under test (SUT) once, as data, and generates real
test suites from the declaration. Python+Playwright is the first emitter;
Java is the second, and the second exists to make the parity claim true.
Generated suites report into pluggable tracker adapters; the first adapter
is IKC3's fault reports, so a red test files a bug into the very platform
the tests exercise.

## Release note (draft)

- New: a SUT declared once in JSON runs as a Python+Playwright suite; the
  same declaration refuses the same broken model the same way.
  Accepted by: T-taf-001 (parity of refusal, `env -i`, python3 only)
- New: a failed generated test files a fault report into a configured
  tracker through a declared adapter; the IKC3 adapter is the first.
  Accepted by: T-taf-002
- Internal: the Java+Playwright emitter proves the same declaration
  generates equivalent suites in two languages.
  Accepted by: T-taf-003 (Python and Java emitters agree on the suite)

### What this does not do

v1 generates static journeys only. Model-based generation — walks of the
SUT graph, coverage-directed paths, journal replay — is declared in
ADR-taf-v1-001-01 and arrives by lanes, not all at once.

## Lanes

### ▶ Lane TAF/PLAN-taf-v1-001-01/A-1 — the SUT model is JSON

The contract: [[SPEC-taf-v1-001-01-the-sut-model]].

A SUT declares states, transitions and journeys in one JSON document. The
loader validates shape, refusals name the broken clause, and no ambiguous
form is guessed — one form only.

**Release note (draft)**

- New: `sut.model.json` declares pages, actions and journeys; a broken
  model names its fault.
  Accepted by: T-taf-001

### ▶ Lane TAF/PLAN-taf-v1-001-01/B-2 — the Python+Playwright emitter

From a valid model, `taf emit --lang python` writes a runnable
Playwright+pytest suite: page objects, journey tests, and a manifest
mapping each test back to the model element that produced it.

**Release note (draft)**

- New: one declaration produces a committed, reviewable pytest suite.
  Accepted by: T-taf-004

### ▶ Lane TAF/PLAN-taf-v1-001-01/C-3 — tracker adapters and fault reports

A test outcome flows to a declared sink. The IKC3 adapter files a fault
report and links it to the test's model element; adapters are a declared
kind so JIRA or GitHub Issues are additions, not rewrites.

**Release note (draft)**

- New: a red test files a fault report into IKC3, named for its model
  element; the report repairs when the fix lands.
  Accepted by: T-taf-002

### ▶ Lane TAF/PLAN-taf-v1-001-01/D-4 — the Java emitter proves parity

`--lang java` emits the equivalent Playwright-Java + JUnit suite. Parity
means: same model, same refusal text, same test names, same journey steps —
the discipline measured in PLAN-ikc-v3-079-01 applied to a second axis.

**Release note (draft)**

- New: the same declaration generates the Java suite; both emitters agree
  or both refuse.
  Accepted by: T-taf-003

### ▶ Lane TAF/PLAN-taf-v1-001-01/E-5 — the tracker is the first SUT

IKC3's tracker is the demo SUT: real UI (reader/tot islands), real API
(the bus), and a fault report in it is a live record. Its own DSL
declarations (`workflow.edn`, `support.edn`) later feed the white-box model.

**Release note (draft)**

- New: tafbase runs journeys over a live IKC3 tracker and files its
  findings into it.
  Accepted by: T-taf-005 (a full loop: fail → report → fix → repaired)

### ▶ Lane TAF/PLAN-taf-v1-001-01/F-6 — the SUT graph (MBT)

The model grows from journeys to a graph: states and transitions as data,
black-box first, then white-box — a DSL First SUT carries its own model,
so the declared command/event surface becomes the test oracle. Static
routes → random walks with seed replay → coverage-directed paths →
journal replay as generated tests.

**Release note (draft)**

- New: the emitter can walk the SUT graph; a walk with a seed replays a
  found failure exactly.
  Accepted by: T-taf-006

### ▶ Lane TAF/PLAN-taf-v1-001-01/G-7 — the corpus teaches

tafbase is a learning surface (ADR-taf-v1-002-01): every concept the
generated code embodies is a CONCEPT document — Python and pytest,
Playwright, test design, and the DSL itself — and generated files cite
them with `@concept` lines the corpus checker enforces. A guided index
(CONCEPT-taf-v1-001-01-the-learning-path) orders them junior-first. Every
other lane ships the concepts its code cites; this lane seeds the corpus
and the rule.

**Release note (draft)**

- New: every generated file names the concepts it demonstrates, and each
  names a corpus page a learner can open; a citation with no page fails
  the corpus check. A page may precede its code — the index says which
  lane embodies it.
  Accepted by: T-taf-007 (code-link-unresolved refuses a dead citation)
