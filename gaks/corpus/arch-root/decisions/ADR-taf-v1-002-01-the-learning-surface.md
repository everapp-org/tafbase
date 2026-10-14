---
id: ADR-taf-v1-002-01-the-learning-surface
status: accepted
subproject: taf
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# ADR-taf-v1-002-01 — the delivered project is a learning surface

Decided: 2026-10-14 · George Petrov + Devin

## Context

The precedent is `Python-Selenium-Chrome-Demo/v.0.1/docs/concepts.md`: a
hand-written glossary of ~60 concepts — Python, Selenium, pytest, design
patterns, testing — each with a definition, an example, and a "Used in"
pointer. It was good teaching material and it could rot: the pointers were
prose, checked by nobody.

## Decisions

7. **The corpus teaches.** CONCEPT documents in `arch-root/concepts/`
   cover the implicit and explicit concepts the project embodies, across
   four domains: the language and runner (Python: fixtures, `yield`,
   dataclasses; pytest/JUnit: discovery, markers, parametrize), the tool
   (Playwright/Selenium: locators, auto-waiting, browser contexts), test
   design (AAA, page object, isolation, flaky tests), and the DSL itself
   (model, emitter, manifest, parity, refusal). A concept is a page — a
   definition, a small example, where it lives in this repo — never a
   reference manual.

8. **Citations are checked, not promised.** Generated code carries
   `@concept CONCEPT-taf-v1-NNN-NN-*` comment lines, the form the GAKS
   `code.annotation-pattern` already checks (`code-link-unresolved` fails
   when a cited concept has no document). The emitter decides which
   concepts each generated file demonstrates and writes the annotations;
   the manifest records the concept ids per test. An annotation with no
   document is a defect the checker refuses. A document nothing cites is
   not: a concept may be written before the code that embodies it — the
   learning path marks such pages as waiting on their lane, and a corpus
   report may list them, but the check does not fail on them.

9. **A guided path orders the glossary.** The corpus is flat and
   wiki-linked, but a learner needs a sequence. One concept document —
   `CONCEPT-taf-v1-001-01-the-learning-path` — is the ordered index:
   what a test is → AAA → locators → fixtures → the model → the emitters.
   Junior-first; each entry names its prerequisites.

10. **PRINCIPLE documents join the corpus.** tafbase's `gaks.project.json`
    declares the PRINCIPLE kind so the platform's own rules (DSL First,
    release-note-first, one-form-only) are corpus documents that code and
    plans can cite, not folklore in a README.

## Consequences

- Every emitter lane ships the concept documents its generated code cites;
  the corpus check is the gate — a lane that emits an uncited concept does
  not pass.
- The learning surface is a property of the delivered bundle, not of
  ikc3: `gaks/site/` renders the concepts and their backlinks with no
  server, on tafbase.com or off a disk.
