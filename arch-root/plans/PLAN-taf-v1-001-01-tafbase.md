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

The contract: [[SPEC-taf-v1-001-04-tafbase]].

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

**Progress (2026-10-15).** The IKC3 sink exists and works live:
`taf/sink_ikc3.py` dispatches `:support/file-report` over `/bus-ws`
(EDN envelope, `ikc3-bus` subprotocol, no token needed where authz is
off). Emitted verbatim into each Python suite as `ikc3_sink.py`; the
generated `pytest_runtest_makereport` hook files on any red test when
`TAF_IKC3_WS` is set, carrying page URL + DOM. Proven against a probe
bus: a suite pointed at a dead SUT filed one report per red test
(`tests/test_live.py`, opt-in). Still open: the Java-side hook,
screenshot/attachment upload, auth-token support, a second
(JIRA-shaped) adapter.


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

**Progress (2026-10-15).** First half met: the generated suite ran green
against a live probe bus — `the-board-is-up` and `board-to-tot`, 2 passed
in ~4 s (T-taf-004, opt-in `TAF_LIVE=1`; `TAF_BASE_URL` retargets the
emitted suites without regenerating). The `.ikc-dock-theme` markers and
`?island=` routes verified as real. The filing half is lane C-3's.

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

**Progress (2026-10-15).** `taf/graph.py` + `taf walk` land: edges derive
from declared `from`/`to`, a seeded RNG walks them deterministically,
`--cover` prefers untaken edges. Output is a journey declaration —
`taf emit --journeys walk.json` merges it (duplicate-name refusal on
collision). Live-verified: a seed-7 walk on the tracker model emitted
`test_walked` and ran green on the probe bus. Still open: white-box
oracle from `workflow.edn`/`support.edn`, coverage-directed suite
generation, journal replay.


### ▶ Lane TAF/PLAN-taf-v1-001-01/H-8 — observation: dwell, waits, narration

From the qa-tafbase harvest (RESEARCH-taf-v1-002-01). `dwell` is a
declared pacing property — a `{"dwell": <ms>}` step emitted as a
literal for a watching human; it is not synchronization (markers and
auto-waiting own correctness). Steps may carry a human `label` the
emitted code logs — every action self-narrates, and narrated timestamps
make the run video captionable: a teardown writes a sidecar `.srt`
beside the video (the old framework wired five teardowns for exactly
this and never built the writer). Later: `wait`/`check` soft/hard
forms and `wait any (X|Y)`.

**Release note (draft)**
- New: a suite can be watched — declared dwell slows each step for a
  human eye, and generated logs narrate each action.
  Accepted by: T-taf-008

### ▶ Lane TAF/PLAN-taf-v1-001-01/I-9 — versioned locators

From the harvest: elements resolve against (app-version × language) —
`addLocator(515, SPANISH, xpath, …)` with nearest-lower-version and
English fallback. In tafbase: an element declares per-version variants;
the emitter writes the lookup as data, resolved at emit time.

**Release note (draft)**
- New: one element survives an app's versions and languages —
  `v515+/es:` variants resolve to the nearest known declaration.
  Accepted by: T-taf-009

### ▶ Lane TAF/PLAN-taf-v1-001-01/J-10 — visual regression

Screenshot grammar `TCID_run_res_step_{Expected,Actual,Diff}`, a
`compare screen` step, excluded regions per device, tolerance levels,
and `taf promote` applying a selection file — the approval loop, not
auto-rebaselining.

**Release note (draft)**
- New: visual regression — a `compare screen` step diffs against a
  baseline, and a person promotes Actual→Expected by file, not by flag.
  Accepted by: T-taf-010

### ▶ Lane TAF/PLAN-taf-v1-001-01/K-11 — targets: devices and envs

A `device:`/`env:` header — `Pixel9ProXL_chrome`, `qa` — resolves at
emit time into capabilities and base URL; compile-time-validated
vocabulary replaces a 300-line runtime factory.

**Release note (draft)**
- New: `device:` and `env:` in the model emit the exact capabilities
  block — no runtime dispatch.
  Accepted by: T-taf-011

### ▶ Lane TAF/PLAN-taf-v1-001-01/L-12 — runs: replay, debug, preflight

`taf run --last-failed` replays a rerun manifest; `--debug` keeps the
browser and breaks on failure; `requires:` declares suite preflight
(mail server, service up) that fails fast.

**Progress (2026-10-27).** The report form of the preflight lands first:
`taf dry-run` names the tests a run would execute, the `TAF_*` contract
as the shell sets it, and what the run lacks — video off, a missing
golden, a stale suite dir, a SUT that does not answer (`--probe`).
A report, not a gate: exit 0, the person decides
(CONCEPT-taf-v1-008-01). Still open: `taf run` itself, `requires:` —
the fail-fast form.

**Release note (draft)**
- New: a failed run replays only its failures; a debug run pauses at the
  broken step with the browser open.
  Accepted by: T-taf-012

## The harvest program — order and combination

Lanes H-8..L-12 are the harvest (RESEARCH-taf-v1-002-01); this is the
order, driven by what each unlocks and what a learner sees first.
Milestones, not lanes, are the unit of delivery:

**M1 · Watchable** (H-8). `dwell` ✅, then `label` narration, the wait
vocabulary (`check` soft, `wait-any`), the `maybe` step. Nothing else
depends on these; everything a demo or a learner touches benefits.
Small clauses, immediate payoff — the suite becomes *seeable*.

**M2 · Evidence** (J-10 head + L-12 head). Declared `test-id` → the
`results/<runId>/<testId>/` artifact layout → golden files (the naming
grammar needs both) → subtitle track (needs labels from M1 and the
layout) → rerun manifest → `--debug` keeps the browser. Ordered by
dependency: each artifact joins on the test id, the srt joins on the
labels, all of it lands in the layout.

**M3 · Reachable** (K-11 + `requires:` from L-12). `device:`/`env:`
headers and suite preflight — what makes a suite portable and a run
honest about prerequisites. Independent of M2; sized for when a second
target (a staging env, a second device) actually appears.

**M4 · Durable** (I-9). Versioned locators, then the locale dimension
and API `fixture:` blocks. The biggest model-surface changes; justified
by a real second version/language, not before.

**M5 · Niche** (deferred). The mail oracle, the image step, the living
spec — each waits for a SUT that demands it. The pages exist so the
ideas aren't lost; the lanes wait until they're needed.

### ▶ Lane TAF/PLAN-taf-v1-001-01/N-13 — derive the model (white-box)

`taf derive` computes a draft model from SUT artifacts and writes it
through the same loader — the author refines, never starts from a blank
page. First source: IKC3's declarations (workflow/support EDN → states,
endpoints). Later: OpenAPI → endpoints; a crawl → states and edges.
Coverage follows: `taf walk` gains systematic traversal — a journey per
FSM edge is the test set.

**Release note (draft)**
- New: `taf derive` writes a draft model from the SUT's own
  declarations — the author refines instead of transcribing.
  Accepted by: T-taf-013

Provenance: `*.sut.provenance.json` records each fact's source,
confidence and last-seen. Re-derivation reports deviation —
`changed:` / `deviates:` / `not-in-source:` — and never silently
overrides a human fact.

## The inputs — declared and derived

The model has two authors (CONCEPT-dsl-v1-014-01): black-box (a person
declares) and white-box (`taf derive` computes the draft from SUT
artifacts — IKC3's EDN surfaces first, OpenAPI and crawl later).
Derivation writes a model through the same loader, not a second
pipeline; and a derived graph feeds coverage — a journey per FSM edge.
Lane N-13 owns `derive`; edge-coverage traversal grows `taf walk`.

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
