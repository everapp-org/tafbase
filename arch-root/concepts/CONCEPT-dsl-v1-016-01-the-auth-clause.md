---
id: CONCEPT-dsl-v1-016-01-the-auth-clause
status: draft
subproject: dsl
authored: 2026-10-27
authors:
  - George Petrov
  - Devin
---

# The auth clause

## Definition

`sut.auth` names the action that signs in — `{"auth": {"action":
"log-in-with-code"}}`. The emitted suite runs it **once per run** in a
bootstrap context at the action's `from` state, saves the session as
storage state, and every test's fresh context inherits it. Python:
`context.storage_state(path=…)` into `results/<runId>/auth-state.json`,
then `browser.new_context(storage_state=…)`. Java: `signInOnce()` and
`setStorageStatePath(…)` in `BaseTest`.

## Why it exists

Each test gets a fresh context — isolation by construction. But a
credential that spends once per sign-in (a one-time code) cannot
afford per-test logins: two tests would need two codes. Storage state
splits the difference — the *session* is shared, the *context* still
isn't. One code spent per run; no test's state bleeds into another's.

## In this project

The clause is `sut.auth` in `SPEC-taf-v1-001-04`; the loader requires
the named action to exist and to have a `from` state (the page the
run navigates to so it can sign in) — refusals `:unknown-action` and
`:bad-auth`. The action's `env:`/`env-pool:` needs join `env_needs`,
so an unset `TAF_SUT_CODES` gates the run before a browser opens.

## Touch it

```json
"sut": {"auth": {"action": "log-in-with-code"}}
```

```bash
export TAF_SUT_CODES="code-1"
taf run suts/ikc3-tracker.sut.model.json --slowmo 500 --video
# results/<runId>/auth-state.json — the session every test reused
```

## Neighbors

[[CONCEPT-dsl-v1-015-01-the-env-value]] — the credential the action
reads. [[CONCEPT-playwright-v1-002-01-the-browser-context]] — the
isolation storage state shares *into* rather than around.
