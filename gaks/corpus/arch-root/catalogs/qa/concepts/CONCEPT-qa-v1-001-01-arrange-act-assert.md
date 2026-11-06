---
id: CONCEPT-qa-v1-001-01-arrange-act-assert
status: accepted
subproject: qa
layer: L1-archetype
standing: recommended
realizes: CONCEPT-istqb-v1-012-01-test-oracle, CONCEPT-istqb-v1-014-01-entry-and-exit-criteria
---

# Arrange-Act-Assert Pattern

## Definition

The Arrange-Act-Assert (AAA) pattern is the canonical structural architecture for automated test cases. It partitions each test into three distinct, non-overlapping phases executed in strict chronological order:

1. **Arrange**: Set up all preconditions, system states, test data, mocks, and environment fixtures required for the scenario.
2. **Act**: Execute the single, specific behavior, user interaction, command, or method invocation being tested.
3. **Assert**: Verify that the actual outcomes, state mutations, and returned values match the expected results defined by the test oracle.

This pattern is isomorphic to the **Given-When-Then** structure used in Behavior-Driven Development (BDD): Given the arranged state, When an action is taken, Then assert the observable outcome.

```python
def test_user_can_promote_ticket_to_triage(board_fixture):
    # 1. Arrange: Create initial preconditions and seed ticket in backlog
    ticket = board_fixture.create_ticket(title="Fix CSS layout", status="BACKLOG")
    
    # 2. Act: Execute the single action under test
    ticket.promote_to("TRIAGE")
    
    # 3. Assert: Verify the postcondition state matches expectation
    updated = board_fixture.fetch_ticket(ticket.id)
    assert updated.status == "TRIAGE"
    assert updated.transition_history[-1].to_state == "TRIAGE"
```

## Why it exists

The Arrange-Act-Assert pattern establishes structural discipline across automated test suites:

1. **Failure Diagnosis Isolation**: Clear separation pinpoints test failure etiology. A failure during the Arrange phase indicates broken test fixtures, stale data, or environment infrastructure issues. A failure during Act indicates interface or runtime execution errors. A failure during Assert indicates a functional defect or regression.
2. **Single-Action Focus**: Enforcing a single Act phase prevents tests from sprawling into multi-action integration odysseys where a failure in the middle leaves subsequent actions unexecuted and unverified.
3. **Readability and Cognitive Load**: Any engineer or reviewer reading the test can immediately identify the target behavior (the Act line) without getting lost in boilerplate setup code.
