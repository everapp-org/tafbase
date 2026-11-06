---
id: CONCEPT-istqb-v1-007-01-equivalence-partitioning
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
requires: CONCEPT-istqb-v1-003-01-seven-testing-principles
---

# Equivalence Partitioning

## Definition

Equivalence Partitioning (EP) is a black-box test design technique defined in CTFL v4.0 §4.2.1 in which input data and output values are divided into partitions (equivalence classes) such that all members of a given partition are expected to be processed in the same way by the system under test.

- **Valid Partitions**: Values that must be accepted and processed normally by the application according to specifications.
- **Invalid Partitions**: Values that must be rejected, ignored, or handled with explicit error handling routines.

If a test case uncovers a defect using one representative value from a partition, other values from that same partition are assumed to uncover the same defect. Conversely, if one representative value passes, other values within that partition are assumed to pass.

```text
Specification: Age must be an integer between 18 and 65 (inclusive) to register.

Partitions:
  Invalid Partition 1: age < 18        --> Representative: 12  --> Expected: Rejection error
  Valid Partition:     18 <= age <= 65 --> Representative: 35  --> Expected: Registration success
  Invalid Partition 2: age > 65        --> Representative: 72  --> Expected: Rejection error
  Invalid Partition 3: Non-numeric     --> Representative: "a" --> Expected: Format error
```

```python
import pytest

@pytest.mark.parametrize("age,expected_status", [
    (12, "ERROR_TOO_YOUNG"),   # Invalid partition 1
    (35, "REGISTERED"),         # Valid partition
    (72, "ERROR_TOO_OLD"),     # Invalid partition 2
])
def test_user_registration_age_partitions(age, expected_status):
    result = register_account(name="Alex", age=age)
    assert result.status == expected_status
```

## Why it exists

Equivalence partitioning solves the fundamental impossibility of exhaustive testing:

1. **Test Suite Minimization**: Rather than testing thousands of arbitrary integers, EP systematically compresses an infinite input domain into a finite, provably representative set of test cases.
2. **Eliminating Redundancy**: Testing inputs 31, 32, 33, 34, and 35 provides zero additional defect-detection capability when all belong to the same linear valid partition; EP avoids wasted test execution cycles.
3. **Structured Negative Testing**: EP forces explicit identification of invalid partitions, ensuring automated test suites verify negative error paths and edge validations alongside happy paths.
