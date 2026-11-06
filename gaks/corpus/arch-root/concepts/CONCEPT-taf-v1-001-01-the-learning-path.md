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

1. Foundations of testing (ISTQB CTFL v4.0) → [[CONCEPT-istqb-v1-001-01-error-defect-failure]],
   [[CONCEPT-istqb-v1-010-01-state-transition-testing]],
   [[CONCEPT-istqb-v1-012-01-test-oracle]]
2. What a test is → [[CONCEPT-qa-v1-001-01-arrange-act-assert]] &
   [[CONCEPT-testing-v1-001-01-arrange-act-assert]]
3. Finding things on a page → [[CONCEPT-qa-v1-002-01-the-locator-ladder]] &
   [[CONCEPT-playwright-v1-002-01-semantic-locators]]
4. Knowing where you are → the state marker (SPEC-taf-v1-001-04, `states`)
5. The model → [[CONCEPT-dsl-v1-001-01-the-sut-model]]
6. From model to suite → the emitter and the manifest (SPEC-taf-v1-001-04)
7. Language archetypes → [[CONCEPT-prog-v1-001-01-immutable-data-carrier]],
   [[CONCEPT-prog-v1-006-01-scoped-test-fixture]],
   [[CONCEPT-prog-v1-010-01-external-environment-binding]]
8. Python & pytest lane → [[CONCEPT-python-v1-001-01-frozen-dataclass]],
   [[CONCEPT-pytest-v1-001-01-dependency-injected-fixtures]]
9. Playwright mechanics → [[CONCEPT-playwright-v1-001-01-browser-context-page-hierarchy]],
   [[CONCEPT-playwright-v1-003-01-auto-waiting-and-actionability]]
10. Organizing a suite → [[CONCEPT-qa-v1-005-01-page-object-model]] &
    [[CONCEPT-pom-v1-001-01-the-page-object]]
11. Configuring a run → [[CONCEPT-taf-v1-003-01-the-environment]]
12. Closing the loop → [[CONCEPT-taf-v1-002-01-the-result-sink]]
13. Java 21++ & JUnit 5 lane →
    [[CONCEPT-java-v1-001-01-junit-lifecycle-annotations]],
    [[CONCEPT-java-v1-002-01-records]],
    [[CONCEPT-java-v1-019-01-jspecify-and-nullaway]]
14. TypeScript & JavaScript `@playwright/test` lanes →
    [[CONCEPT-ts-v1-006-01-typed-test-fixture-extension]],
    [[CONCEPT-js-v1-006-01-async-fixture-callback]],
    [[CONCEPT-pwtest-v1-001-01-test-extend-fixtures]]
15. The graph — walks, seeds, coverage →
    [[CONCEPT-dsl-v1-002-01-the-seeded-walk]] &
    [[CONCEPT-qa-v1-010-01-model-based-seeded-walk]]

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
