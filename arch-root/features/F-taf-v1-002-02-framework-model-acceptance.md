---
id: F-taf-v1-002-02-framework-model-acceptance
status: draft
subproject: taf
authored: 2026-10-28
authors:
  - George Petrov
  - Devin
---

# F-taf-v1-002-02 — the framework model: acceptance

## Summary

The framework model must be a real DSL artifact, consumed by every
tool that needs its semantics — emitters, validator, dry-run —
with conformance gates that make drift loud. Each criterion below
is testable: a command, a test name, or a diff.

## Acceptance criteria

Each item is testable: a command, a test name, or a diff.

## The model

- [ ] AC-1 `dsl/framework-spec.dsl` parses via `FrameworkSpec.g4` with
      zero syntax errors — proven by any consumer load
- [x] AC-2 Every `form` and `rung` carries a `description` — the model
      reads as documentation
- [x] AC-3 The grammar file is the artifact; the parser is generated,
      never hand-edited (Python3 target in `taf/_antlr/`, Java target
      via `antlr4-maven-plugin`)

## The consumers

- [x] AC-4 `codegen/java` derives from the spec — regenerated suite is
      byte-identical to the checked-in `generated/java/ikc3-tracker`
- [x] AC-5 `codegen/python` derives the same way — byte-identical
      `generated/python/ikc3-tracker`
- [x] AC-6 `model.py` derives `STEP_FORMS`/`LOCATOR_RUNGS` and
      `ops.locator_rung` derives preference order from the spec
- [ ] AC-7 `dryrun.py` derives its env table from `contract.env` —
      add a var in the spec, see it in `taf env` without code changes
- [ ] AC-8 `model.py` refusal names import from the contract —
      `_refusal` sites take names from spec, not literals

## Governance (§3.5)

- [x] AC-9 `test_spec_coverage` — every form variant and rung variant
      emits real output in both languages, or the build fails
- [x] AC-10 `test_spec_contract` — every refusal name used in code is
      declared in the spec
- [ ] AC-11 Adding a form to the spec without implementations fails a
      test (coverage gate catches unspellable coordinates)

## The frameworks

- [x] AC-12 `pytest tests/` — 91+ pass, 4 live skips
- [x] AC-13 `mvn test-compile` in a generated Java suite — BUILD SUCCESS
- [ ] AC-14 `mvn test` runs the Java suite live against the SUT
      (auth bootstrap + storage state, parity with the Python run)
- [ ] AC-15 `codegen-java` emits at least Elements.java from the spec —
      the Java-target generator produces a real artifact
- [ ] AC-16 A generated suite's pom regenerates itself when the model
      or spec changes (`generate-sources` wired)

## The discipline

- [x] AC-17 Feature lanes live on `feature/*` branches, not master
- [ ] AC-18 `env:`/`env-pool:` — no secret value appears in any
      generated file, draft, caption, or journal entry (grep-able)
- [ ] AC-19 `.interp`/`.tokens` ANTLR byproducts gitignored or removed
- [ ] AC-20 SPEC-002-02 updated: contract section documented in the
      metamodel table
