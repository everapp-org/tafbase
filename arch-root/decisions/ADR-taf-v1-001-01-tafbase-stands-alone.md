# ADR-taf-v1-001-01 — tafbase stands alone

Status: accepted · 2026-10-14

## Decisions

1. **tafbase is its own repository and its own corpus.** It does not live
   inside IKC3. `gaks.project.json` declares it; the static GAKS bundle of
   PLAN-ikc-v3-079-01 delivers the corpus tools. This is the first real
   consumer of the foreign-project path.

2. **The DSL is JSON, not EDN.** The SUT model must be readable and writable
   from Java and Python with no Clojure dependency — the same reason
   `gaks.project.json` replaced the EDN declaration in IKC3.

3. **Generate, don't interpret.** Emitters write committed, reviewable test
   files (`test_login.py`, `LoginJourneyTest.java`). A generic runtime
   interpreter was considered and refused: generated code diffs in a PR are
   legible; hidden magic is not.

4. **Tracker integrations are declared adapters, not a hard dependency.**
   tafbase core runs with no IKC3. The IKC3 adapter (fault reports,
   repaired-on-merge) is the first sink and the demo loop; JIRA and GitHub
   Issues adapters are additions of the same kind.

5. **The IKC3 tracker is the first SUT**, not a component of tafbase.
   Dogfooding means tests exercise the real platform and file reports into
   it — not that tafbase embeds it.

6. **MIT license.** The goals are exposure and adoption; copyleft and
   dual-licensing are refused.

## Consequences

- Doc ids take the `taf` subproject prefix (`PLAN-taf-v1-NNN-NN`); numbering
  is this repository's own.
- The IKC3 deployment tracker can file tickets for tafbase work only if
  this corpus is registered as a vault of the deployment — an open
  question, deferred to the first lane.
