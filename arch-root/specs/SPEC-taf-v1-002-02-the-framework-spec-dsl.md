---
id: SPEC-taf-v1-002-02-the-framework-spec-dsl
status: draft
subproject: taf
authored: 2026-10-27
authors:
  - George Petrov
  - Devin
---

# The framework-spec DSL

A project-specific, grammar-hosted DSL (DSL-First §2.4 — ANTLR — the family
member Kernel/Behavior/Verification/Catalog cannot express: spellings
as data). The model `dsl/framework-spec.dsl.json` declares what the
framework is; emitters derive framework code from it.

## Metamodel

| Clause | Shape | Meaning |
|---|---|---|
| `dsl` | `{name, version, binding}` | language identity + version |

The grammar is `dsl/FrameworkSpec.g4`; the parser is ANTLR-generated
into `taf/_antlr/` (regenerate on grammar change — see
`taf/dsl_parse.py` docstring); `dsl_parse` walks the tree to the
model dict.
| `vocabulary` | `{form: entry}` | step forms of the SUT language |
| `locators` | `{rung: entry}` | locator-ladder rungs |

**Form entry**: `arg` (shape doc), `caption` (`.srt` template),
`spell` (`{python, java}` templates or a line list), optional
`variants` (keyed by `when` = arg keys present) or `wrap`
(`pre`/`post` lines for `maybe`).

**Rung entry**: `key` (locator arg), `spell` or `variants`.

**Spelling templates**: `${key}` placeholders; emitters substitute
escaped values and computed fragments (`${state_class}`, `${value_expr}`,
`${loc_chain}`, `${save_key}`…). Values pass through `_py`/`_j` name
transforms and per-language escaping.

## Well-formedness

- Every form/rung spells both `python` and `java` (parity is the point)
- Every `when` list matches arg keys exactly; variants are exhaustive
- `${value}` never appears in a `caption` — captions name, never leak
- Consumers emit byte-identical output to the last handwritten emitter
  (the conformance test until all consumers derive)

## Semantics

- `emit_java` → `Elements`/`assertThat`/`page.*` Java+Playwright lines
- `emit_python` → `elements.`/`expect`/`page.*` Python+Playwright lines
- `model.py` → `_check_step` arg-shape validation (pending M1)
- Adding a form or rung = one model row, all consumers derive

## Versioning

`dsl.version` bumps on clause shape changes; additive forms/rungs are
backward-compatible by construction.
