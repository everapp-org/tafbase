---
id: CONCEPT-testing-v1-001-01-arrange-act-assert
status: draft
subproject: testing
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# Arrange–Act–Assert

## Definition

The shape of a readable test: **arrange** the preconditions, **act** once,
**assert** the outcome. Three phases, in that order, visible in the code.

```python
def test_ticket_moves_to_triage(board_page):
    ticket = board_page.new_ticket("the report")   # arrange
    ticket.move_to("triage")                        # act
    expect(board_page.ticket("the report")).to_be_in("triage")  # assert
```

## Why it exists

A test is documentation that runs. When the three phases are separated,
a reader sees *what* is tested before *how*; when they interleave, the
intent drowns in mechanics. In tafbase the phases come from the model:
a journey's setup is its `start` state, the act is its `steps`, and the
assertions are the state markers and `expect-final` the emitter writes
for every arrival — so generated tests are AAA by construction.

## In this repo

Generated suites under `tools/` (lane B-2). Emitted tests carry
`@concept CONCEPT-testing-v1-001-01-arrange-act-assert`.
