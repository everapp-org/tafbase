---
id: CONCEPT-istqb-v1-006-01-static-vs-dynamic-testing
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
requires: CONCEPT-istqb-v1-001-01-error-defect-failure
---

# Static Testing vs. Dynamic Testing

## Definition

Testing approaches are divided into static and dynamic methods based on whether code execution is required, as defined in CTFL v4.0 §3.1:

- **Static Testing**: Evaluates software work products (source code, schemas, architecture designs, user stories, requirements) without executing the software. Techniques include informal reviews, walkthroughs, inspections, linters, abstract syntax tree (AST) analyzers, and compiler type-checking. Static testing discovers defects directly in the artifacts themselves.
- **Dynamic Testing**: Evaluates software by executing the program on a machine with defined test inputs and observing its dynamic execution behavior, state transformations, outputs, and performance metrics. Dynamic testing discovers failures caused by executed defects.

```python
# Static Testing: Analyzed by a linter/type-checker WITHOUT running code
def calculate_tax(amount: float, rate: float) -> float:
    # Static analyzer flags unreachable code, unassigned variables, or type mismatches:
    if rate < 0:
        raise ValueError("Rate must be non-negative")
    return amount * rate
    unreachable_value = 42  # Static check flags: Unreachable code defect

# Dynamic Testing: Evaluates runtime behavior by executing the compiled/interpreted program
def test_calculate_tax_runtime_execution():
    result = calculate_tax(100.0, 0.05)
    assert result == 5.0  # Dynamic check: asserts expected output on executed inputs
```

## Why it exists

Static and dynamic testing find different kinds of flaws and serve different economic roles:

1. **Defect vs. Failure Detection**: Static testing finds defects directly (e.g., syntax errors, uncalled functions, security vulnerabilities, missing requirements) without needing a test harness. Dynamic testing detects failures that emerge only during execution, such as concurrency race conditions, memory leaks, and distributed network latency.
2. **Economic Shift-Left**: Running static linters and semantic validators takes milliseconds and costs virtually nothing, catching defects before compilation or container deployment.
3. **Complementary Coverage**: Static verification cannot confirm runtime environmental behavior, database query performance, or third-party service integration; dynamic automated tests remain indispensable for runtime verification.
