---
id: CONCEPT-java-v1-001-01-junit-lifecycle-annotations
status: accepted
subproject: java
layer: L3-tooling
since: JUnit 5.0
standing: recommended
realizes: CONCEPT-prog-v1-006-01-scoped-test-fixture
---

# JUnit 5 Lifecycle Annotations

## Definition

JUnit 5 (Jupiter) defines scoped lifecycle annotations (`@BeforeEach`, `@AfterEach`, `@BeforeAll`, `@AfterAll`, `@Test`, `@Nested`) that structure test execution, fixture setup, and state teardown per test method or per container.

```java
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class OrderProcessorTest {

    private OrderProcessor processor;

    @BeforeEach
    void setUp() {
        processor = new OrderProcessor();
    }

    @AfterEach
    void tearDown() {
        processor.close();
    }

    @Test
    void processesValidOrder() {
        OrderResult result = processor.process(new Order("item-42", 1));
        assertEquals(OrderStatus.SUCCESS, result.status());
    }

    @Nested
    class WhenInventoryIsLow {
        @Test
        void rejectsExcessOrder() {
            OrderResult result = processor.process(new Order("item-rare", 999));
            assertEquals(OrderStatus.OUT_OF_STOCK, result.status());
        }
    }
}
```

## Why it exists

Replaces JUnit 4's runner model and less expressive lifecycle naming (`@Before`, `@After`, `@BeforeClass`, `@AfterClass`). JUnit 5 makes fixture lifecycle explicit and enables hierarchical context testing via `@Nested`. By creating a fresh test instance per `@Test` method (the default `PER_METHOD` lifecycle), tests remain isolated and avoid shared mutable state leakage. `@BeforeAll` and `@AfterAll` allow initialization across the test container when required. Use scoped lifecycle annotations to ensure deterministic fixture allocation and clean resource teardown.
