---
id: CONCEPT-qa-v1-005-01-page-object-model
status: accepted
subproject: qa
layer: L1-archetype
standing: recommended
requires: CONCEPT-qa-v1-002-01-the-locator-ladder
---

# Page Object Model and Screenplay Encapsulation

## Definition

The Page Object Model (POM) and its evolution, the Screenplay Pattern, are architectural patterns that encapsulate the technical mechanics of interacting with web pages and UI components behind clean, business-oriented object interfaces.

In the Page Object Model:
- **UI Structure & Selectors**: HTML elements, locators, and interaction protocols are encapsulated within dedicated Page or Component classes (e.g., `LoginPage`, `NavigationHeader`, `CheckoutModal`).
- **Domain Intent Methods**: Page objects expose high-level semantic methods representing user interactions (`login_as(user)`, `submit_order()`, `search_catalog(query)`).
- **Assertions**: Assertions generally remain inside the test scripts, or page objects expose state query methods and locators for assertions. The test case acts as a readable orchestrator of domain activities without mentioning raw DOM selectors.

```text
+-----------------------------------------------------------------+
|                           Test Case                             |
|  def test_checkout(checkout_page):                             |
|      checkout_page.fill_shipping_details(address)               |
|      checkout_page.submit_payment()                             |
|      expect(checkout_page.confirmation_heading).to_be_visible() |
+-----------------------------------------------------------------+
                                |
                                v
+-----------------------------------------------------------------+
|                    Page Object (CheckoutPage)                   |
|  - Encapsulates: get_by_role("button", name="Pay")              |
|  - Encapsulates: get_by_label("Street Address")                 |
|  - Exposes: fill_shipping_details(), submit_payment()           |
+-----------------------------------------------------------------+
```

```python
class LoginPage:
    def __init__(self, page):
        self.page = page
        self.username_input = page.get_by_label("Username")
        self.password_input = page.get_by_label("Password")
        self.submit_button = page.get_by_role("button", name="Sign in")
        self.error_banner = page.get_by_role("alert")

    def login(self, username, password):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()

# Test script consumes the clean domain interface:
def test_invalid_login_shows_alert(page):
    login_page = LoginPage(page)
    page.goto("/login")
    login_page.login("alex", "wrong-password")
    assert login_page.error_banner.is_visible()
```

## Why it exists

The Page Object Model is the primary defense against UI test automation code duplication:

1. **Single Source of Truth for Locators**: When a button ID or accessibility label changes, updating the locator in the single Page Object class automatically fixes all 50 test cases that interact with that button.
2. **Separation of Concerns**: Test scripts focus on expressing business logic and verifying test oracles; Page Objects handle the underlying DOM traversal, synchronization, and driver mechanics.
3. **Reusability and Composability**: Page Objects and Component Objects can be composed into complex page hierarchies (e.g., embedding a `NavbarComponent` inside multiple pages).
