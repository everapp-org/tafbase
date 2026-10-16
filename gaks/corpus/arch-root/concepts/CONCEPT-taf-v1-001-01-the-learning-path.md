---
id: CONCEPT-taf-v1-001-01-the-learning-path
status: draft
subproject: taf
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# The learning path

## Definition

The ordered index of this corpus's concept documents, junior-first. The
corpus is flat and wiki-linked; this page is the sequence a reader new to
test automation can follow, each entry naming its prerequisites.

## Why it exists

ADR-taf-v1-002-01 makes the delivered project a learning surface: every
concept the generated code embodies is a page here, and generated files
cite their concepts with `@concept` lines the checker enforces. This page
answers "where do I start?"

## The path

1. What a test is → [[CONCEPT-testing-v1-001-01-arrange-act-assert]]
2. Finding things on a page → [[CONCEPT-playwright-v1-001-01-the-locator-ladder]]
3. Knowing where you are → the state marker (SPEC-taf-v1-001-04, `states`)
4. The model → [[CONCEPT-dsl-v1-001-01-the-sut-model]]
5. From model to suite → the emitter and the manifest (SPEC-taf-v1-001-04)
6. Your own toolchain → [[CONCEPT-python-v1-002-01-the-virtual-environment]]
7. pytest mechanics → [[CONCEPT-pytest-v1-001-01-the-pytest-fixture]]
8. Playwright mechanics → [[CONCEPT-playwright-v1-002-01-the-browser-context]],
   [[CONCEPT-playwright-v1-003-01-auto-waiting]]
9. Organizing a suite → [[CONCEPT-pom-v1-001-01-the-page-object]]
10. Configuring a run → [[CONCEPT-taf-v1-003-01-the-environment]]
11. Closing the loop → [[CONCEPT-taf-v1-002-01-the-result-sink]]
12. Java parity — what "equivalent suite" means →
    [[CONCEPT-java-v1-001-01-the-junit-lifecycle]]
13. The graph — walks, seeds, coverage →
    [[CONCEPT-dsl-v1-002-01-the-seeded-walk]]

Every entry is a checked citation — the corpus checker refuses a link to
a page that does not exist.

## The domains

The path is the on-ramp; the corpus is grouped by *what a page teaches*:

| domain | teaches |
|---|---|
| `python` | the language surface — venv, env-adjacent mechanics |
| `pytest` | the test runner — fixtures, hooks, scope |
| `playwright` | the browser library — locators, contexts, waiting |
| `java` | the second emitter's world — JUnit lifecycle, Maven |
| `pom` | the page-object model — organizing a suite |
| `testing` | the discipline — AAA, failure handling, goldens, flakes |
| `dsl` | the model language — steps, locators, targets, walks |
| `taf` | the framework itself — its contract, sinks, artifacts |

A concept files under the domain it teaches; language-neutral ideas —
the `TAF_*` contract, the run layout — live under `taf`, once, never
duplicated per language.

## Three readers, three entries

tafbase is three levels — build the framework, model a SUT, use the
suite ([[CONCEPT-taf-v1-007-01-the-three-levels]]). Each reads a
different subset:

| you are | read first |
|---|---|
| a **model author** | `dsl` — the model, the step language, waits, locators |
| a **test user** | `taf` + `testing` — the contract, the sink, failure handling |
| a **framework contributor** | `python` + `pytest` + `playwright` — the machinery |

A reader never needs all domains — that separation is the DSL First
promise itself.
