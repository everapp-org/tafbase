---
id: CONCEPT-pytest-v1-002-01-mark-parametrize
status: accepted
subproject: pytest
layer: L2-tool
since: pytest 8.0
standing: recommended
realizes: CONCEPT-istqb-v1-007-01-equivalence-partitioning, CONCEPT-istqb-v1-008-01-boundary-value-analysis
contrasts-with: CONCEPT-junit-v1-002-01-parameterized-test-and-sources, CONCEPT-pwtest-v1-002-01-data-driven-test-loop
---

# Parameterized Test Matrix via mark.parametrize

## Definition

Pytest's `@pytest.mark.parametrize` decorator defines multi-variable, data-driven test matrices. It accepts a comma-separated string of argument names, an iterable of test vectors (tuples), and optional custom test identifiers via `ids`.

When multiple `@pytest.mark.parametrize` decorators are stacked on a single test function, pytest calculates the Cartesian product of all argument sets, generating an isolated test execution for every combination.

```python
import pytest

@pytest.mark.parametrize(
    "tier,quantity,expected_discount",
    [
        ("STANDARD", 1, 0.00),
        ("STANDARD", 10, 0.05),
        ("VIP", 1, 0.10),
        ("VIP", 5, 0.15),
    ],
    ids=["std-single", "std-bulk", "vip-single", "vip-bulk"]
)
def test_discount_calculation(tier: str, quantity: int, expected_discount: float):
    discount = calculate_discount(tier, quantity)
    assert discount == pytest.approx(expected_discount, abs=1e-3)

@pytest.mark.parametrize(
    "age,expected_eligible",
    [
        pytest.param(17, False, id="boundary-below-min"),
        pytest.param(18, True,  id="boundary-exact-min"),
        pytest.param(65, True,  id="boundary-exact-max"),
        pytest.param(66, False, id="boundary-above-max"),
    ]
)
def test_age_eligibility_boundaries(age: int, expected_eligible: bool):
    assert check_eligibility(age) == expected_eligible
```

## Why it exists

Realizes `CONCEPT-istqb-v1-007-01-equivalence-partitioning` and `CONCEPT-istqb-v1-008-01-boundary-value-analysis`. Systematic quality assurance requires validating edge boundaries and partition classes thoroughly without code duplication.

Contrasts with `CONCEPT-junit-v1-002-01-parameterized-test-and-sources` and `CONCEPT-pwtest-v1-002-01-data-driven-test-loop`. In JUnit 5, parameterization relies on reflection-based value sources (`@CsvSource`, `@MethodSource`) and class annotations. In Playwright Test, parameterization is achieved by wrapping tests in native JavaScript loops. Pytest provides a declarative Pythonic decorator syntax with fine-grained control via `pytest.param` to attach specific markers or expectations (such as `marks=pytest.mark.xfail`) to individual test vectors.
