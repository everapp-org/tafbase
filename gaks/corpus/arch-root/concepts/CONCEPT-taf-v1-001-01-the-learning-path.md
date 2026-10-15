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

1. What a test is → [[CONCEPT-taf-v1-004-01-arrange-act-assert]]
2. Finding things on a page → [[CONCEPT-taf-v1-003-01-the-locator-ladder]]
3. Knowing where you are → the state marker (SPEC-taf-v1-001-02, `states`)
4. The model → [[CONCEPT-taf-v1-002-01-the-sut-model]]
5. From model to suite → the emitter and the manifest (SPEC-taf-v1-001-02)
6. pytest mechanics → [[CONCEPT-taf-v1-005-01-the-pytest-fixture]]
7. Playwright mechanics → [[CONCEPT-taf-v1-006-01-the-browser-context]],
   [[CONCEPT-taf-v1-007-01-auto-waiting]]
8. Organizing a suite → [[CONCEPT-taf-v1-008-01-the-page-object]]
9. Configuring a run → [[CONCEPT-taf-v1-012-01-the-environment]]
10. Closing the loop → [[CONCEPT-taf-v1-010-01-the-result-sink]]
11. Java parity — what "equivalent suite" means →
    [[CONCEPT-taf-v1-009-01-the-junit-lifecycle]]
12. The graph — walks, seeds, coverage →
    [[CONCEPT-taf-v1-011-01-the-seeded-walk]]

Every entry is a checked citation — the corpus checker refuses a link to
a page that does not exist.
