---
id: CONCEPT-istqb-v1-012-01-test-oracle
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
---

# Test Oracle and Expected Result Determination

## Definition

A Test Oracle is an authoritative source or mechanism used to determine whether the observed runtime outcome of a software execution matches the expected outcome, as defined in CTFL v4.0 §1.4.

An oracle provides the criteria for evaluating the correctness of test execution. Sources of test oracles include:
- **Specifications and Requirements**: Formal requirement documents, user story acceptance criteria, API specifications (e.g., OpenAPI schemas), and domain standards.
- **Reference Implementations and Pre-existing Systems**: An older verified system, a mathematical model, or a high-level reference implementation used as a benchmark.
- **Golden Files and Historical Baselines**: Previously recorded and human-validated outputs (e.g., golden snapshots or serialized database dumps).
- **Property-Based Oracles**: Invariants and algebraic properties that must hold true for all inputs (e.g., sorting an array produces an array of the same length whose elements are in monotonic non-decreasing order).
- **Domain Experts**: Human users or subject matter experts verifying business nuances.

```python
# API schema and deterministic calculation serving as test oracles
def test_invoice_calculation_against_oracle(tax_oracle_table):
    invoice = create_invoice(subtotal=100.0, region="EU-DE")
    
    # Oracle Source 1: Strict mathematical calculation from regulatory tax law
    expected_tax = tax_oracle_table.lookup(region="EU-DE", amount=100.0) # 19.00
    expected_total = 119.00
    
    # Oracle Source 2: Contractual schema validation
    assert invoice.is_valid_schema()
    assert invoice.tax == expected_tax
    assert invoice.total == expected_total
```

## Why it exists

The test oracle is the core distinguishing feature between running code and actually testing it:

1. **No Oracle, No Test**: Executing a workflow without an assertion or oracle check is merely exercising code (a smoke or stress execution), not testing it; it only catches unhandled crashes or process exit codes.
2. **The Oracle Problem**: In complex domains (such as machine learning, computer graphics, or scientific calculations), determining the exact expected result is computationally expensive or ambiguous. Explicitly declaring the oracle mechanism allows teams to choose between exact-value matching, property verification, and metamorphic relations.
3. **Automated Verification**: In automated CI/CD pipelines, oracles must be encoded deterministically into assertions and schemas to eliminate ambiguous or subjective pass/fail judgments.
