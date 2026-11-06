---
id: CONCEPT-istqb-v1-011-01-statement-and-branch-coverage
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
---

# White-Box Statement and Branch Coverage

## Definition

Statement coverage and branch coverage are structural (white-box) test metrics defined in CTFL v4.0 §4.3 that evaluate the thoroughness of test suites by measuring which parts of the source code are exercised during dynamic execution:

- **Statement Coverage**: The percentage of executable statements in the code that have been exercised by the test suite:
  $$\text{Statement Coverage} = \frac{\text{Number of executed statements}}{\text{Total number of executable statements}} \times 100\%$$
- **Branch Coverage**: The percentage of control-flow branches (decision outcomes, such as the `True` and `False` branches of an `if` statement or cases in a `switch` block) that have been exercised by the test suite:
  $$\text{Branch Coverage} = \frac{\text{Number of executed decision outcomes}}{\text{Total number of decision outcomes}} \times 100\%$$

**Subsumption Relationship**: 100% branch coverage strictly subsumes 100% statement coverage. Traversing every branch outcome guarantees that every statement on those branches is executed. However, 100% statement coverage does **not** guarantee 100% branch coverage. If an `if` block has no explicit `else` clause, executing the `True` branch executes 100% of statements while leaving the `False` branch outcome completely unexercised (50% branch coverage).

```python
def process_refund(amount: float, is_vip: bool) -> float:
    fee = 5.0
    if is_vip:             # Decision: True or False
        fee = 0.0          # Statement executed only on True branch
    return amount - fee

# A single test with is_vip=True achieves 100% Statement Coverage:
def test_vip_refund():
    assert process_refund(100.0, is_vip=True) == 100.0
    # Every statement in process_refund was reached!
    # But the False branch (is_vip=False) was NEVER tested.
    # Branch coverage is only 50%.

# To achieve 100% Branch Coverage, we must also exercise the False branch:
def test_standard_refund():
    assert process_refund(100.0, is_vip=False) == 95.0
```

## Why it exists

Statement and branch coverage provide objective, quantified insights into automated test suite thoroughness:

1. **Exposing Blind Spots**: Relying solely on passing tests creates a false sense of security; code coverage tools pinpoint unexecuted error handlers, missed fallback conditions, and unexercised branches.
2. **Subsumption Rigor**: Because 100% statement coverage misses entire control paths where no code was written (the implicit `else`), engineering standards require branch coverage as the stronger quality baseline.
3. **Refactoring Safety**: High branch coverage ensures that legacy code refactorings are guarded by tests that exercise all decision logic, preventing regression defects when control flow is reorganized.
