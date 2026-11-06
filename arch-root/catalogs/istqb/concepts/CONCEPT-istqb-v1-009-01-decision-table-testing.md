---
id: CONCEPT-istqb-v1-009-01-decision-table-testing
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
---

# Decision Table Testing

## Definition

Decision Table Testing is a black-box test design technique defined in CTFL v4.0 §4.2.3 used to specify and test complex business rules that depend on combinations of multiple input conditions and yield specific actions.

A decision table organizes logic into four quadrants:
1. **Conditions**: Inputs, states, or prerequisites that evaluate to boolean (True/False) or discrete values.
2. **Condition Alternatives**: Rows specifying combinations of condition states.
3. **Actions**: Outcomes, state updates, or outputs produced by the system.
4. **Action Entries**: Marks (X or True/False) indicating which actions must occur for each combination of conditions.

Each column in the table represents a distinct business rule and corresponds to at least one concrete test case. Tables can be collapsed by merging columns where certain conditions are "don't care" (`-`), while preserving coverage of business permutations.

```text
Decision Table: Loan Application Approval
============================================================
Conditions / Rules             | R1 | R2 | R3 | R4 | R5
-------------------------------+----+----+----+----+-----
Credit score >= 700?           | Y  | Y  | N  | N  | -
Income >= 50,000?              | Y  | N  | Y  | N  | -
Existing default on file?      | N  | N  | N  | N  | Y
-------------------------------+----+----+----+----+-----
Actions                        |    |    |    |    |
-------------------------------+----+----+----+----+-----
Approve automatically (X)      | X  |    |    |    |
Send for manual review (X)     |    | X  | X  |    |
Reject loan application (X)    |    |    |    | X  | X
```

```python
import pytest

@pytest.mark.parametrize("credit_score,income,has_default,expected_decision", [
    (750, 60000, False, "APPROVE"),       # Rule 1
    (720, 35000, False, "MANUAL_REVIEW"), # Rule 2
    (650, 80000, False, "MANUAL_REVIEW"), # Rule 3
    (580, 30000, False, "REJECT"),        # Rule 4
    (780, 95000, True,  "REJECT"),        # Rule 5: Default trumps score
])
def test_loan_decision_table(credit_score, income, has_default, expected_decision):
    decision = evaluate_loan(credit_score, income, has_default)
    assert decision == expected_decision
```

## Why it exists

Decision table testing eliminates ambiguity and combinatorial blindness in multi-condition business logic:

1. **Systematic Completeness**: Complex prose specifications often omit edge cases (e.g., what happens when condition A is true but condition B is false and condition C is missing). Tabular formalization exposes gaps in specifications before code is written.
2. **Direct Mapping to Parameterized Tests**: Each column maps directly to a parameterized automated test row, ensuring 100% rule coverage with zero guesswork.
3. **Clarity on Rule Interaction**: When multiple business rules interact, decision tables clearly delineate precedence, override rules, and default behaviors.
