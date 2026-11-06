---
id: CONCEPT-junit-v1-001-01-per-method-test-instance-lifecycle
status: accepted
subproject: junit
layer: L2-tool
since: JUnit 5.10
standing: recommended
realizes: CONCEPT-prog-v1-006-01-scoped-test-fixture, CONCEPT-qa-v1-004-01-session-and-context-isolation
contrasts-with: CONCEPT-pytest-v1-001-01-dependency-injected-fixtures, CONCEPT-pwtest-v1-001-01-test-extend-fixtures
---

# Per-Method Test Instance Lifecycle and Fixtures

## Definition

JUnit Jupiter adheres by default to the `TestInstance.Lifecycle.PER_METHOD` lifecycle model. For every individual test method annotated with `@Test`, `@RepeatedTest`, or `@ParameterizedTest`, JUnit creates a brand new instance of the test class.

Under this model:
- Instance fields are freshly instantiated for each test execution, eliminating mutable state leakage between methods.
- `@BeforeEach` methods execute prior to each test method on the freshly constructed instance.
- `@AfterEach` methods execute after each test method completes (even if the test throws an exception), guaranteeing teardown.
- Class-level setup (`@BeforeAll`, `@AfterAll`) requires `static` methods unless class-level lifecycle (`@TestInstance(Lifecycle.PER_CLASS)`) is explicitly declared.

```java
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class CartServiceTest {

    private CartService cartService; // Fresh reference created per test method

    @BeforeEach
    void setUp() {
        cartService = new CartService();
        cartService.initialize();
    }

    @AfterEach
    void tearDown() {
        cartService.clear();
    }

    @Test
    void addsItemSuccessfully() {
        cartService.addItem("item-1", 2);
        assertEquals(2, cartService.getItemCount());
    }

    @Test
    void startsWithZeroItems() {
        // Safe from contamination: cartService is a brand new instance here
        assertEquals(0, cartService.getItemCount());
    }
}
```

## Why it exists

Realizes `CONCEPT-prog-v1-006-01-scoped-test-fixture` and `CONCEPT-qa-v1-004-01-session-and-context-isolation`. Reusing object state across multiple test methods is a primary cause of test order dependencies and intermittent test failures. Creating a distinct object instance per test method guarantees clean slate isolation.

Contrasts with `CONCEPT-pytest-v1-001-01-dependency-injected-fixtures` and `CONCEPT-pwtest-v1-001-01-test-extend-fixtures`. In JUnit Jupiter, fixture scoping is tied directly to Java object orientation and method annotation lifecycles (`@BeforeEach`/`@AfterEach`). In contrast, pytest and Playwright Test use functional dependency injection where tests declare named fixtures as parameters, allowing arbitrary multi-level fixture composition without class hierarchy inheritance.
