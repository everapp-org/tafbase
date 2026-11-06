---
id: CONCEPT-istqb-v1-008-01-boundary-value-analysis
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
requires: CONCEPT-istqb-v1-007-01-equivalence-partitioning
---

# Boundary Value Analysis

## Definition

Boundary Value Analysis (BVA) is a black-box test design technique defined in CTFL v4.0 §4.2.2 that focuses on testing the boundaries of equivalence partitions. BVA is based on the empirical observation that software defects cluster heavily at the edges of input and output domains due to off-by-one errors (such as `<` versus `<=`, or `>` versus `>=`).

CTFL v4.0 recognizes two boundary value approaches:

- **2-Value BVA**: For each boundary, test two values:
  1. The boundary value itself.
  2. Its closest neighbor on the other side of the boundary (the value just across the threshold).
- **3-Value BVA**: For each boundary, test three values:
  1. The boundary value itself.
  2. Its closest neighbor inside the valid partition.
  3. Its closest neighbor outside the valid partition.

```text
Partition: Valid range from 1 to 100 inclusive.

2-Value BVA Test Set:
  Lower boundary:  0 (invalid),  1 (valid)
  Upper boundary: 100 (valid), 101 (invalid)
  Total tests: 4

3-Value BVA Test Set:
  Lower boundary:  0 (invalid),  1 (valid boundary),  2 (valid interior)
  Upper boundary: 99 (valid interior), 100 (valid boundary), 101 (invalid)
  Total tests: 6
```

```python
import pytest

# 2-Value BVA on range [1, 100]
@pytest.mark.parametrize("quantity,is_valid", [
    (0, False),    # Just below min boundary
    (1, True),     # At min boundary
    (100, True),   # At max boundary
    (101, False),  # Just above max boundary
])
def test_order_quantity_bva(quantity, is_valid):
    result = validate_order_quantity(quantity)
    assert result.is_valid == is_valid
```

## Why it exists

Boundary value analysis maximizes defect detection density per executed test case:

1. **Targeting Off-By-One Logic Bugs**: Developers frequently confuse strict inequalities (`>`) with inclusive inequalities (`>=`), or miscalculate array bounds and loop terminators. Testing middle values (e.g., 50 in a [1, 100] range) rarely catches these errors, whereas testing 0, 1, 100, and 101 exposes them immediately.
2. **Deterministic Coverage Standards**: Specifying 2-value or 3-value BVA gives teams an unambiguous, measurable completion metric for parameter validation.
3. **Synergy with Equivalence Partitioning**: While EP verifies general domain behavior, BVA stresses the precision of domain demarcation lines.
