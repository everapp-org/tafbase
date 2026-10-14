---
id: CONCEPT-taf-v1-002-01-the-sut-model
status: draft
subproject: taf
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# The SUT model

## Definition

One JSON document that declares a system under test: its states (places a
journey can be, each with a marker that proves arrival), its elements
(named locators), its actions (steps the SUT offers — the edges of the
graph), its journeys (named paths through the actions) and its endpoints
(the API surface). The contract is SPEC-taf-v1-001-01.

## Why it exists

A test suite is usually a pile of files that *encode* knowledge of the
SUT invisibly. Here the knowledge is written down once, as data: the same
model generates the Python suite and the Java suite, refuses broken input
with named reasons, and later is the graph that model-based walks run on.
Change the model, regenerate, and the suite's diff *is* the change —
visible in a pull request.

## In this repo

`sut.model.json` per SUT (none yet — lane A-1 builds the loader). Read
SPEC-taf-v1-001-01 for the clauses and the nine refusals.
