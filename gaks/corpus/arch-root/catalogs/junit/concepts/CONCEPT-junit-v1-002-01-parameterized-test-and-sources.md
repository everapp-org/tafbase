---
id: CONCEPT-junit-v1-002-01-parameterized-test-and-sources
status: accepted
subproject: junit
layer: L2-tool
since: JUnit 5.10
standing: recommended
realizes: CONCEPT-istqb-v1-007-01-equivalence-partitioning, CONCEPT-istqb-v1-008-01-boundary-value-analysis
contrasts-with: CONCEPT-pytest-v1-002-01-mark-parametrize, CONCEPT-pwtest-v1-002-01-data-driven-test-loop
---

# Parameterized Tests and Value Sources

## Definition

JUnit Jupiter's `@ParameterizedTest` executes a single test method multiple times with different arguments. It pairs with various argument source annotations:
- `@ValueSource`: Supplies arrays of literal primitives, strings, or classes.
- `@CsvSource`: Supplies comma-delimited strings parsed into method parameters with automatic type conversion.
- `@CsvFileSource`: Loads tabular test vectors from external CSV classpath resources.
- `@MethodSource`: References a static factory method that returns a `Stream<Arguments>`, `Collection`, or `Iterable`.

Each parameter set is executed as an independent test invocation in test reports with configurable display names (`name = "[{index}] {arguments}"`).

```java
import java.util.stream.Stream;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.MethodSource;
import static org.junit.jupiter.api.Assertions.assertEquals;

class DiscountCalculatorTest {

    @ParameterizedTest(name = "Tier {0} with quantity {1} gives discount {2}")
    @CsvSource({
            "STANDARD, 1, 0.00",
            "STANDARD, 10, 0.05",
            "VIP,      1, 0.10",
            "VIP,      5, 0.15"
    })
    void computesDiscount(String tier, int quantity, double expectedDiscount) {
        DiscountCalculator calc = new DiscountCalculator();
        assertEquals(expectedDiscount, calc.calculate(tier, quantity), 0.001);
    }

    @ParameterizedTest
    @MethodSource("boundaryScenarios")
    void checksBoundaries(int inputAge, boolean expectedEligibility) {
        EligibilityService service = new EligibilityService();
        assertEquals(expectedEligibility, service.isEligible(inputAge));
    }

    static Stream<Arguments> boundaryScenarios() {
        return Stream.of(
                Arguments.of(17, false), // Boundary: just below minimum
                Arguments.of(18, true),  // Boundary: minimum eligible age
                Arguments.of(65, true),  // Boundary: maximum working age
                Arguments.of(66, false)  // Boundary: above maximum
        );
    }
}
```

## Why it exists

Realizes `CONCEPT-istqb-v1-007-01-equivalence-partitioning` and `CONCEPT-istqb-v1-008-01-boundary-value-analysis`. Testing equivalence classes and boundary values by duplicating identical `@Test` methods creates maintenance overhead and visual clutter. Using parameterized tests ensures comprehensive coverage of input partitions while retaining distinct reporting per input vector.

Contrasts with `CONCEPT-pytest-v1-002-01-mark-parametrize` and `CONCEPT-pwtest-v1-002-01-data-driven-test-loop`. JUnit provides strongly typed argument conversion and rich annotation-driven sources integrated directly into the Java type system. In pytest, parameterization is achieved via decorators on functions, while in Playwright Test, parameterization is achieved through native JavaScript iteration loops.
