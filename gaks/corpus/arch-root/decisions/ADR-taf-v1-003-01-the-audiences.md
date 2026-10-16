---
id: ADR-taf-v1-003-01-the-audiences
status: accepted
subproject: taf
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# ADR-taf-v1-003-01 — three audiences, and who decides what

Decided: 2026-10-16 · George Petrov + Devin

## Context

The harvest debate surfaced a recurring confusion: a fork between
Playwright's native screenshot compare and a hand-rolled filename grammar
was put to a stakeholder whose interest is *what a run produces*, not
*how the diff engine works*. Asking it conflated roles — the same mixing
CONCEPT-taf-v1-007-01 names for artifacts must hold for *decisions* too.

## Decisions

Three audiences, and a decision belongs to whoever's surface it changes:

- **Framework creator** — owns internals: how the generator works, which
  library diffs pixels, the journal's format, schema mechanics.
  Surface: `taf/`, `tests/`, this ADR log, CONTRIBUTING.md. Rulings are
  made here, by whoever writes the code, and recorded as ADRs — reviewable
  after the fact, not adjudicated before it.
- **Test creator (model author)** — owns the vocabulary: which clauses a
  model may declare. Surface: `suts/`, SPEC-taf-v1-001-04 Parts 1–2, the
  `dsl` concepts. A decision only reaches this audience when it adds,
  removes, or renames something the model can *say*.
- **Results consumer** — owns what a run shows: the report, the
  artifacts, the narration. Surface: `generated/` output, manifests,
  video + `.srt`, fault reports. A decision reaches this audience when it
  changes what a run leaves behind.

**The rule:** put no internal fork to a creator or consumer. Put no
vocabulary or visibility question to a creator without naming the surface
it changes. An ADR is the record of a creator decision; a spec clause is
the record of a vocabulary one; a release note is the record of a visible
one.

## Consequences

- The evidence-stack fork is settled by its owner, not escalated:
  Playwright's native compare (`to_have_screenshot`/`hasScreenshot`) under
  tafbase's own artifact layout — we do not rebuild a diff engine to keep
  a filename.
- A per-test `taf.journal.jsonl` is the shared timestamped substrate —
  `.srt`, rerun manifests, and fault reports read it; it is designed once.
- The journey name *is* the test id; `test-id` is a naming rule, not a
  new field.
- `targets:` becomes a declared model section — a vocabulary change, so
  it is a spec clause, not an emitter detail.
