---
id: CONCEPT-dsl-v1-010-01-the-fixture
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The fixture block

## Definition

Arrange through the API, act through the UI: a `fixture:` block of
backend calls a journey runs before its browser steps — the old
framework's SOAP/XML command templates that prepared a trader account
before the UI test ever opened a page.

## Why it exists

Driving setup through the UI is slow and brittle — the journey then
tests the login screen when it meant to test the ticket board. An API
fixture is fast, precise, and honest about what is under test. It is
also where test data comes from: create the account, seed the ticket,
*then* open the browser.

## In this project

The mechanism half exists — `api` steps already call endpoints and
`save` response values. The declared `fixture:` arrangement (runs once
before the act, clearly separated from steps under test) is planned;
see RESEARCH-taf-v1-002-01, item 24.

## Touch it

```json
{"api": "list-tickets"}   // already runs mid-journey; a fixture block is the planned home
```

## Neighbors

[[CONCEPT-testing-v1-001-01-arrange-act-assert]] — the fixture is the
arrange; [[CONCEPT-dsl-v1-007-01-the-step-language]].
