---
id: CONCEPT-qa-v1-002-01-the-locator-ladder
status: accepted
subproject: qa
layer: L1-archetype
standing: recommended
realizes: CONCEPT-istqb-v1-005-01-test-types
---

# The Locator Ladder

## Definition

The Locator Ladder is an architectural priority hierarchy for selecting UI elements in web and mobile test automation. It orders element locator strategies from most resilient, semantic, and user-facing down to the most brittle and implementation-dependent:

1. **Rung 1: User-Facing Accessibility Roles & Accessible Names (Highest Priority)**:
   - Queries based on accessibility attributes (`role="button"`, `name="Submit Order"`).
   - Mirrors how assistive technologies and actual human users perceive and navigate the interface.
2. **Rung 2: Semantic Labels and Visible Text**:
   - Queries based on form labels (`<label for="...">`), placeholder text, or prominent visible text.
3. **Rung 3: Explicit Test IDs (`data-testid`)**:
   - Dedicated testing attributes (`data-testid="submit-checkout"`) placed specifically for automation.
   - Decoupled from CSS class styling and DOM restructuring, though invisible to real users.
4. **Rung 4: CSS Selectors (Low Priority / Discouraged)**:
   - Queries relying on style classes or structure (`button.btn-primary.submit-v2`).
   - Fragile; frequently breaks during UI redesigns and CSS refactorings.
5. **Rung 5: Structural XPath / DOM Index Paths (Lowest Priority / Strictly Prohibited)**:
   - Hardcoded DOM hierarchy paths (`/html/body/div[2]/div/form/button[1]`).
   - Extremely brittle; breaks whenever any ancestor container, wrapper `div`, or layout element changes.

```text
  +-----------------------------------------------------------+  Resilient, User-Facing,
  | 1. Accessibility Role & Name: get_by_role("button", ...)  |  Verifies A11y
  +-----------------------------------------------------------+
  | 2. Label & Text: get_by_label("Username")                 |
  +-----------------------------------------------------------+
  | 3. Dedicated Test ID: get_by_test_id("submit-order")      |  Stable fallback
  +-----------------------------------------------------------+
  | 4. CSS Class Selectors: locator("button.btn-primary")     |  Brittle
  +-----------------------------------------------------------+
  | 5. Absolute XPath: xpath("/html/body/div[3]/button[1]")   |  Extremely fragile
  +-----------------------------------------------------------+  (PROHIBITED)
```

```python
# Preferred: Rung 1 (Accessibility Role and Name)
page.get_by_role("button", name="Submit Order").click()

# Preferred Fallback: Rung 3 (Explicit Test ID for complex visual canvases)
page.get_by_test_id("cart-total-badge").click()

# Anti-pattern: Rung 4 & 5 (Brittle CSS / Absolute XPath)
# page.locator(".css-1x84a .btn-wrap > button:nth-child(2)").click() # BREAKS ON NEXT SPRINT
```

## Why it exists

The Locator Ladder directly addresses the single largest cause of flakiness and maintenance overhead in UI test automation:

1. **Decoupling Tests from Implementation Detail**: Tests should verify what the user experiences, not the implementation trivia of CSS frameworks (like Tailwind or styled-components generated hashes).
2. **Promoting Web Accessibility**: By using accessibility roles and labels as the primary locator strategy, automated tests immediately fail if a UI component is inaccessible to screen readers, turning test automation into a continuous accessibility audit.
3. **Longevity Across Redesigns**: When designers redesign buttons from blue to green or rewrite CSS classes, tests rooted in role and name continue to pass without modification.
