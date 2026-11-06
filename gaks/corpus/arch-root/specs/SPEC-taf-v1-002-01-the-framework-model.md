---
id: SPEC-taf-v1-002-01-the-framework-model
status: draft
subproject: taf
authored: 2026-10-27
authors:
  - George Petrov
  - Devin
---

# The framework model (PRD)
## One line

A test automation framework's semantics are declared once — as a
model — and working framework implementations are generated from it
in each target language. Python+Playwright and Java+Playwright are
the first two outputs, not the design center.

## The object

The product is the **model**, not a framework: a language-neutral
declaration of what a test automation framework is — its step
vocabulary, locator ladder, journey semantics, auth model,
environment contract, evidence format, reporting protocol — plus a
generator that spells those declarations as compilable, reviewable
framework code per target language.

Anything a practitioner would otherwise hand-code three times is a
model clause; anything that differs per language is only a spelling.
The generator is handwritten and stays that way — it is not the
product; the model is.

## Layers

```
dsl/                    the framework model (the artifact)
  forms.dsl.json        step forms: arg shapes, captions, per-language spellings
  locators.dsl.json     ladder rungs + per-language spellings
  contract.dsl.json     env contract, refusal table, evidence/rerun/report formats
taf/
  ops.py                canonical IR — what a journey IS, language-free
  emit_python.py        model → Python+Playwright/pytest framework
  emit_java.py          model → Java+Playwright/JUnit5 framework
```

A generated framework then does what it was modeled to do: load SUT
models (its own input DSL), refuse ambiguity, emit or run journeys,
produce evidence. The SUT model and the framework model are different
objects — the second generates the programs that read the first.

## Requirements

1. **Grammar as data.** Step forms, locator rungs, their arg shapes
   and their per-language spellings live in declared tables. Adding a
   step form is one row, not three code changes. Validation and all
   emitters read the same table — divergence is impossible by
   construction, not just tested for.
2. **Named refusals.** Every invalid clause refuses with a named
   reason the spec lists. Never guess, never die on the first.
3. **Language parity.** Generated frameworks carry a canonical
   manifest; targets must produce identical semantics. Parity is
   proven, not promised.
4. **Environment contract.** Effective values resolve
   flag > env > model; needs (`env:`, `env-pool:`) derive from
   declared use and gate before a browser opens. Secrets are named,
   never stored.
5. **Session semantics.** `auth` declares sign-in-once: run it in a
   bootstrap context, keep the session as storage state, every test's
   fresh context inherits it. Isolation kept, one credential per run.
6. **Evidence.** Every test leaves a journal, timed `.srt` narration
   paired with `.webm` video, failure screenshot + DOM, a rerun
   manifest, and a printed artifact dir. Captions name steps, never
   values.
7. **Reporting.** Fault reports file on failure — through the SUT's
   own surface or an adapter — and never twice: a fingerprint ledger
   dedups an unchanged error across runs.
8. **Authoring aids.** `record` drafts model clauses from live
   driving (secrets redacted by locator); `walk` derives journeys by
   seeded graph traversal; `dry-run` reports what a run would do and
   lacks; `env` prints the contract for the console.

## Non-goals

- No runtime interpreter of step semantics — semantics compile to
  code; a human reads the model, the grammar, the generator and the generated framework
- No GUI test runner — the console narration + journal are the feed
- The generator itself is not model-driven (the bootstrap must end
  somewhere; it ends at handwritten emitters reading the tables)
- As DSL First teaches, the model should be the source of truth and is used for onboarding new developers

## Status

| Requirement | Evidence today |
|---|---|
| SUT DSL + refusals | `model.py`, SPEC-taf-v1-001-04 |
| Canonical IR + parity | `ops.py`, byte-identical manifests |
| env contract, needs, gate | `env:`/`env-pool:`, `env_needs`, preflight |
| auth/storage-state | `sut.auth`, `auth-state.json` |
| Evidence | journal, `.srt`, video, setup/ artifacts |
| Reporting + dedup | `sink_ikc3`, `results/filed.json` |
| **Grammar as data** | **missing — forms/rungs are imperative code** |

The open row is the product: today's emitters hand-write each form
per language; the model would make the grammar the artifact.

## Milestones

- **M1 Forms table** — step forms + spellings declared; emitters
  read it; one row adds a step in both languages
- **M2 Contract table** — env contract + refusal table as data;
  `taf env`, dry-run, and the gate derive from it
- **M3 Third spelling** — a second spell target per clause proves the
  model isn't Python-shaped by accident (JS/TS or .NET)
- **M4 Sinks as model** — reporting backends declared like forms

## Risks

- **Parity drift** — mitigated by manifests; table-driven emission
  reduces it further
- **Scope creep toward a programming language** — the vocabulary is
  deliberately finite; `maybe`, `dwell`, `wait-any` mark the boundary
- **Divergence inside the tables** — a spelling per clause per
  language is honest only while the model stays small; complexity
  belongs in the clause semantics, not per-target branches
