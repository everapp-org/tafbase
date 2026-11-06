---
id: CONCEPT-qa-v1-006-01-api-fixture-seeding
status: accepted
subproject: qa
layer: L1-archetype
standing: recommended
realizes: CONCEPT-istqb-v1-004-01-test-levels, CONCEPT-istqb-v1-014-01-entry-and-exit-criteria
requires: CONCEPT-qa-v1-001-01-arrange-act-assert
---

# Out-of-Band API State Seeding

## Definition

Out-of-Band API State Seeding is an architectural pattern for UI and end-to-end testing where preconditions and test data are created directly via backend REST/GraphQL APIs, database fixtures, or state injection endpoints, completely bypassing the user interface during the Arrange phase.

In this pattern:
- **Preconditions via API (Out-of-Band)**: Creating users, populating inventory, creating shopping carts, or setting permissions is executed via direct HTTP API requests or database scripts. This takes a few milliseconds.
- **Session Injection**: Authentication tokens or cookies are injected directly into the browser context (`storageState`), bypassing the multi-step UI login form.
- **UI Reserved for the Act Phase**: The browser UI is loaded only at the exact page and state required to exercise the specific interaction under test.

```text
Anti-pattern (UI-only):
[Open Browser] -> [UI Register Form] -> [UI Login Form] -> [UI Catalog Search] -> [UI Add to Cart] -> [TEST CHECKOUT UI]
  (Slow: 35s, 5 potential failure points before test even starts)

Archetype (Out-of-Band API Seeding):
[POST /api/seed/cart] (15ms) -> [Inject Auth Cookie] (2ms) -> [Open /checkout] -> [TEST CHECKOUT UI]
  (Fast: 1.2s, 0 UI flakiness in setup)
```

```python
def test_checkout_submission_with_api_seeding(api_client, browser_context):
    # Arrange (Out-of-Band): Seed state directly via backend APIs
    token = api_client.create_authenticated_user("qa_user@example.com")
    order_id = api_client.seed_cart_with_items(user_token=token, items=["SKU-1", "SKU-2"])
    
    # Inject auth state directly into browser context
    browser_context.add_cookies([{
        "name": "session_token",
        "value": token,
        "domain": "localhost",
        "path": "/"
    }])
    
    # Act: Navigate directly to the checkout page under test
    page = browser_context.new_page()
    page.goto(f"/checkout/{order_id}")
    page.get_by_role("button", name="Place Order").click()
    
    # Assert
    assert page.get_by_text("Order Confirmed").is_visible()
```

## Why it exists

Out-of-band state seeding is essential for scaling end-to-end test suites:

1. **Massive Speedup**: A test that sets up data through the UI takes 20 to 45 seconds; setting up the same data via direct API calls takes 50 to 200 milliseconds, resulting in a 10x-50x speedup of the test suite.
2. **Defect Localization**: If the login UI has a bug, a traditional suite of 200 tests will fail 200 times even though only one test was supposed to test login. With API seeding, only the single login test fails, while the other 199 tests seed their state out-of-band and continue testing their respective features.
3. **Resilience Against UI Churn**: Preconditions are shielded from front-end styling and form refactorings, making tests far more stable over time.
