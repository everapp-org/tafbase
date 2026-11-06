---
id: CONCEPT-istqb-v1-010-01-state-transition-testing
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
---

# State Transition Testing

## Definition

State Transition Testing is a black-box test design technique defined in CTFL v4.0 §4.2.4 used when the behavior of a system is stateful—where the outcome of an event depends not only on current inputs but on past history and current system state.

The system is modeled as a Finite State Machine (FSM) comprising:
- **States**: Observable conditions or modes of existence of the system (e.g., `Draft`, `Submitted`, `Approved`, `Archived`).
- **Events (Triggers)**: Inputs or occurrences that stimulate the system (e.g., `click_submit`, `timeout_fired`).
- **Guard Conditions**: Boolean expressions that must evaluate to True for a transition to fire.
- **Actions**: Output effects or operations triggered by the transition.
- **Transitions**: State shifts from a source state to a target state.

Testing covers:
1. **Valid Transitions**: Verifying expected state changes when valid events fire. Standard coverage criteria include 0-switch coverage (all states and all individual transitions visited) and 1-switch coverage (all sequences of two consecutive transitions).
2. **Invalid Transitions**: Verifying that attempting an illegal event from a given state is rejected (e.g., trying to `pay` an order that is in `Cancelled` state) and does not corrupt the system state.

```text
       +-------+      submit()      +-----------+     approve()     +----------+
-----> | DRAFT | -----------------> | SUBMITTED | ----------------> | APPROVED |
       +-------+                    +-----------+                   +----------+
           |                              |                               |
           | cancel()                     | cancel()                      | refund()
           v                              v                               v
       +-----------------------------------------------------------------------+
       |                               CANCELLED                               |
       +-----------------------------------------------------------------------+
```

```python
def test_order_valid_state_progression(order_fsm):
    assert order_fsm.state == "DRAFT"
    order_fsm.submit()
    assert order_fsm.state == "SUBMITTED"
    order_fsm.approve()
    assert order_fsm.state == "APPROVED"

def test_order_invalid_transition_rejected(order_fsm):
    order_fsm.submit()
    order_fsm.cancel()
    assert order_fsm.state == "CANCELLED"
    # Attempting to approve a cancelled order must raise an exception without altering state
    import pytest
    with pytest.raises(IllegalStateTransitionError):
        order_fsm.approve()
    assert order_fsm.state == "CANCELLED"
```

## Why it exists

State transition testing is essential for testing event-driven, workflow-oriented, and interactive systems:

1. **State-Dependent Defects**: Many critical defects only surface when specific operations are performed in a specific chronological order (e.g., clicking 'Back' after payment authorization).
2. **Robustness Against Illegal Actions**: Systems frequently crash or corrupt database state when users or clients execute out-of-order API calls; testing invalid transitions guarantees system resilience.
3. **Foundation for Model-Based Testing**: Formalizing the state graph allows test generators to walk the graph and automatically synthesize deterministic test suites covering paths and edge transitions.
