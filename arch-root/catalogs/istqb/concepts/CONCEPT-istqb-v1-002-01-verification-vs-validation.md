---
id: CONCEPT-istqb-v1-002-01-verification-vs-validation
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
---

# Verification vs. Validation

## Definition

Verification and validation represent two complementary evaluation processes defined in CTFL v4.0 §1.1.1:

- **Verification ("Building the system right")**: The confirmation through objective evidence that specified requirements have been fulfilled. It evaluates whether a work product conforms to its inputs, design specifications, standards, and regulatory rules.
- **Validation ("Building the right system")**: The confirmation through objective evidence that the requirements for a specific intended use or application have been fulfilled. It evaluates whether the system satisfies genuine operational needs, business goals, and user expectations in its operational environment.

```python
# Verification: Asserting system conforms strictly to technical specification
def test_verify_discount_calculation():
    # Spec: "When total > 100, apply 10% discount"
    cart = ShoppingCart(total=150)
    cart.apply_rules()
    assert cart.discount == 15.0

# Validation: Evaluating fitness for actual operational use
def test_validate_checkout_workflow_satisfies_user_need(user_session):
    # User need: "A shopper must be able to complete checkout with one click"
    user_session.add_saved_item("widget-1")
    user_session.one_click_buy()
    assert user_session.order_status == "CONFIRMED"
    assert user_session.total_steps == 1
```

## Why it exists

Differentiating verification from validation prevents the failure mode of delivering a technically flawless system that solves the wrong problem:

1. **Specification Flaws**: A system can pass 100% of automated unit and integration verification tests while remaining entirely useless if the underlying specification was flawed or obsolete.
2. **Layered Test Strategy**: Automated unit and component tests primarily verify structural code correctness against detailed design. Higher-level acceptance tests, user journeys, and exploratory testing validate whether workflows deliver the intended business value.
3. **Traceability**: Verification traces code upwards to written requirements; validation traces systems outward to user workflows, customer feedback, and business operational realities.
