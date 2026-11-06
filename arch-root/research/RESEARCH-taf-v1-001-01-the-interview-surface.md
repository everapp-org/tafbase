---
id: RESEARCH-taf-v1-001-01-the-interview-surface
status: draft
subproject: taf
authored: 2026-10-15
authors:
  - George Petrov
  - Devin
---

# The interview surface

## What this is

A coverage map: the corpus's concepts against the questions the market
actually asks. Source: a widely-shared "Top 25 Playwright interview
questions" list (LinkedIn, 2026 SDET interview prep). The corpus's
stated job is to serve as a learning surface and interview prep — this
document measures that promise against an external yardstick and names
the gaps as work.

## The map

| # | interview asks | covered by | state |
|---|---|---|---|
| 1 | Playwright vs Selenium | [[CONCEPT-playwright-v1-001-01-browser-context-page-hierarchy]], [[CONCEPT-selenium-v1-001-01-webdriver-session-lifecycle]] | covered |
| 2 | Project setup (TypeScript assumed) | [[CONCEPT-ts-v1-006-01-typed-test-fixture-extension]], [[CONCEPT-pwtest-v1-001-01-test-extend-fixtures]] | covered |
| 3 | Browser / BrowserContext / Page | [[CONCEPT-playwright-v1-001-01-browser-context-page-hierarchy]] | covered |
| 4 | Auto-waiting, actionability | [[CONCEPT-playwright-v1-003-01-auto-waiting-and-actionability]] | covered |
| 5 | locator() vs page.$() | [[CONCEPT-playwright-v1-002-01-semantic-locators]] | covered |
| 6 | Dynamic elements, flaky tests | [[CONCEPT-qa-v1-009-01-deterministic-replay-and-flakiness]] | covered |
| 7 | getByRole vs getByText vs css/xpath | [[CONCEPT-qa-v1-002-01-the-locator-ladder]], [[CONCEPT-playwright-v1-002-01-semantic-locators]] | covered |
| 8 | Dropdowns, checkboxes, alerts, iframes | [[CONCEPT-playwright-v1-009-01-frame-and-shadow-dom-piercing]] | covered |
| 9 | File upload/download | — | gap |
| 10 | Screenshots/videos on failure | [[CONCEPT-taf-v1-002-01-the-result-sink]], [[CONCEPT-playwright-v1-006-01-trace-viewer-and-artifacts]] | covered |
| 11 | API testing via request context | [[CONCEPT-playwright-v1-005-01-api-request-context]] + the model's `api`/`save`/`expect` steps | covered |
| 12 | Authentication reuse | [[CONCEPT-dsl-v1-016-01-the-auth-clause]] | covered |
| 13 | storageState | [[CONCEPT-playwright-v1-008-01-storage-state-reuse]] | covered |
| 14 | Parallel execution, workers | [[CONCEPT-pwtest-v1-005-01-projects-matrix-and-sharding]], [[CONCEPT-pytest-v1-005-01-markers-and-xdist-parallelism]] | covered |
| 15 | Sharding | [[CONCEPT-pwtest-v1-005-01-projects-matrix-and-sharding]] | covered |
| 16 | Retries, flaky-test investigation | [[CONCEPT-qa-v1-009-01-deterministic-replay-and-flakiness]] | covered |
| 17 | beforeEach/afterEach | [[CONCEPT-java-v1-001-01-junit-lifecycle-annotations]], [[CONCEPT-pytest-v1-001-01-dependency-injected-fixtures]], [[CONCEPT-pwtest-v1-001-01-test-extend-fixtures]] | covered (in four idioms) |
| 18 | Framework architecture: POM + fixtures | [[CONCEPT-qa-v1-005-01-page-object-model]], [[CONCEPT-pom-v1-001-01-the-page-object]] + the whole generated layout | covered — our strongest answer |
| 19 | HTML reports | the manifest + sink | part — ours is better (traceable), say so |
| 20 | CI/CD integration | — | gap |
| 21 | Cross-browser (chromium/firefox/webkit) | — | gap — model has no browser clause yet |
| 22 | API mocking, network interception | — | gap |
| 23 | Debugging: trace viewer, headed, inspector | — | gap |
| — | *not asked but we answer it* | seeded walks, parity contracts, checked citations, refusals | our differentiators |

## What the map says

**Seven covered outright, ~4 partial, 14 gaps.** The gaps cluster into
themes, each of which is a lane, not just a page:

- **Flakiness & resilience** (6, 16): retry policy, quarantine — a real
  feature lane, not only docs.
- **Element dynamics** (8, 9): dropdowns/iframes/uploads — the step
  language grows (`select` exists; `frame`, `upload`, `dialog` don't).
- **Auth & state reuse** (12, 13): `storageState` maps cleanly to a
  model clause — declared once, applied to journeys that need it.
- **Execution control** (14, 15, 20, 21): workers, shards, CI matrix,
  browsers — belongs in a `run` clause or per-suite config.
- **Observability** (10, 19, 22, 23): screenshots on failure,
  Playwright trace, API mocking — lanes of their own.

## The TypeScript question

The market's assumed Playwright language is TypeScript (the question
list presumes it). A third emitter is the right move — and cheap:
`taf/ops.py` already carries the canonical plan, so `emit_ts.py` renders
syntax only, and the parity tests generalize to three suites with the
same byte-identical manifest. TypeScript also demos Playwright's native
API surface (`test()`/`expect` fixtures via `test.extend`) — arguably
the most idiomatic target of the three.

Worth doing, ordered: (a) the flaky/auth/execution gaps are product
substance; (b) `emit_ts.py` is visibility — it makes the parity claim
three-legged and lands in the market's assumed idiom. Both are lanes;
the concept pages for each land as they're implemented, per ADR-002.
