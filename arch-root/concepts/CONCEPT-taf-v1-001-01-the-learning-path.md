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
3. Knowing where you are → the state marker (SPEC-taf-v1-001-01, `states`)
4. The model → [[CONCEPT-taf-v1-002-01-the-sut-model]]
5. From model to suite → the emitter and the manifest (SPEC-taf-v1-001-01)
6. pytest mechanics — fixtures, `yield`, markers, parametrize (as the
   Python emitter lands)
7. Playwright mechanics — auto-waiting, contexts, isolation (same)
8. Java parity — what "equivalent suite" means (lane D-4)
9. The graph — walks, seeds, coverage (lane F-6)

Entries 6–9 are placeholders: the concept pages arrive with the lanes
that embody them, because the checker refuses a citation with no page and
a page nothing cites.
