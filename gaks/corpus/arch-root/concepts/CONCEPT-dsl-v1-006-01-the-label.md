---
id: CONCEPT-dsl-v1-006-01-the-label
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The label

## Definition

A human name on an element, action, or step that emitted code narrates
as it runs — the old framework's `canonicalName` + `parentName` that
made every action announce itself: `Clicking 'Sign In button' on
'Login Pom'`.

## Why it exists

A run's output should read as a story, not as selectors. The label is
what a watcher hears; it is what a fault report can quote; and with a
timestamp it is the raw material of
[[CONCEPT-taf-v1-006-01-the-subtitle-track]]. The old framework pushed
the same narration into `document.title` — progress visible even inside
remote-session videos, a trick worth keeping because it is free.

## In this project

Planned — lane H-8. Today an action narrates only by its model name
(`open-tot`); `label` makes it prose. Emitted code prints the label
before each step — cheap in generated code, invisible when absent.

## Touch it

Not yet runnable — see lane H-8 in `PLAN-taf-v1-001-01`.

## Neighbors

[[CONCEPT-taf-v1-006-01-the-subtitle-track]],
[[CONCEPT-testing-v1-002-01-the-failure-funnel]].
