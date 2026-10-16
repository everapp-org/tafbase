---
id: CONCEPT-testing-v1-007-01-the-mail-oracle
status: draft
subproject: testing
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The mail oracle

## Definition

Verifying email: snapshot the inbox *before* the action, then poll
only messages that arrived after a marked timestamp, comparing the body
against a template whose volatile fields are masked
(`X_PLACEHOLDER_X`, regex-masked `Date:`/`Deposit ID:`).

## Why it exists

Mail is the canonical asynchronous oracle — you can't wait for it, you
can only look for what wasn't there before and verify it loosely
enough that volatile fields don't flake it. The old framework's tricks
were the reusable pearls: the *baseline snapshot* (only new messages
count), the *sparse poll schedule* ({2,15,25,43,...,179}s over a 182s
budget — early checks are cheap, patience grows), and the *masked
template* compare. It even scraped an MFA code back out of the mail
HTML and typed it into the page — closing a full verify-by-mail loop.

## In this project

Deferred — needs a mail-capable SUT. The pattern generalizes: any
async oracle (a webhook, a queued job) wants snapshot-then-poll-new.

## Touch it

Not implemented — RESEARCH-taf-v1-002-01, item 18.

## Neighbors

[[CONCEPT-dsl-v1-010-01-the-fixture]] (arrange via API),
[[CONCEPT-testing-v1-002-01-the-failure-funnel]].
