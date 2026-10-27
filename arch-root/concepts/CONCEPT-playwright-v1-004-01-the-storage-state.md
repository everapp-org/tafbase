---
id: CONCEPT-playwright-v1-004-01-the-storage-state
status: draft
subproject: playwright
authored: 2026-10-27
authors:
  - George Petrov
  - Devin
---

# The storage state

## Definition

A file that holds everything a browser context owns: cookies, local
storage, session storage. `context.storage_state(path=…)` writes it;
`browser.new_context(storage_state=…)` reads it into a **new**
context — a second context that carries the first one's session.
Java spells it `storageState(options)` / `setStorageStatePath(path)`.

The subtlety: what is shared is the *state*, not the context. Each
test still gets its own context — its own pages, its own failures —
but it begins already signed in, because the session is in the file.

## Why it exists

Authentication is a browser-context property, so the default rule —
a fresh context per test — means a fresh login per test. When the
credential spends once per use (a one-time code), per-test login is
unaffordable. Storage state serializes the session once and seeds
every context with it: sign in once per run, keep per-test isolation.

## In this project

`sut.auth` is the clause that uses it — the emitted suite runs the
auth action once in a bootstrap context, writes
`results/<runId>/auth-state.json`, and the `page` fixture /
`BaseTest.fresh()` opens every test context from that file. See
[[CONCEPT-dsl-v1-016-01-the-auth-clause]] for the model surface.

## Touch it

```python
ctx = browser.new_context()                  # bootstrap, once per run
ctx.storage_state(path="auth-state.json")    # the session, serialized
t = browser.new_context(storage_state="auth-state.json")  # per test
```

`results/<runId>/auth-state.json` after any `taf run` on the tracker
model — open it; cookies are data, not magic.

## Neighbors

[[CONCEPT-playwright-v1-002-01-the-browser-context]] — the thing being
replicated. [[CONCEPT-dsl-v1-015-01-the-env-value]] — the credential
spent once instead of per test.
