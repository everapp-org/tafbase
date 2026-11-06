---
id: CONCEPT-junit-v1-005-01-tag-filtering-and-parallel-execution
status: accepted
subproject: junit
layer: L2-tool
since: JUnit 5.10
standing: recommended
realizes: CONCEPT-istqb-v1-013-01-confirmation-vs-regression-testing, CONCEPT-prog-v1-007-01-parallel-fan-out
---

# Tag Filtering and Parallel Execution

## Definition

JUnit Jupiter provides `@Tag` for categorizing test classes and methods, combined with an integrated parallel execution engine:
- **Filtering via `@Tag`**: Tests are annotated with tags (e.g. `@Tag("smoke")`, `@Tag("regression")`, `@Tag("slow")`). Build tools like Maven Surefire or Gradle filter executions using boolean expressions (e.g., `-Dgroups="smoke & !slow"`).
- **Concurrent Execution**: Configured in `junit-platform.properties` (`junit.jupiter.execution.parallel.enabled = true`), Jupiter executes test classes and methods concurrently using a configurable fork-join thread pool. Method synchronization can be controlled via `@Execution(ExecutionMode.CONCURRENT)` and `@ResourceLock`.

```java
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.parallel.Execution;
import org.junit.jupiter.api.parallel.ExecutionMode;
import static org.junit.jupiter.api.Assertions.assertTrue;

@Tag("regression")
@Execution(ExecutionMode.CONCURRENT)
class PaymentGatewayTest {

    @Test
    @Tag("smoke")
    void processesCreditCardDirectly() {
        assertTrue(PaymentService.charge(100.00));
    }

    @Test
    @Tag("nightly")
    void processesInternationalWire() {
        assertTrue(PaymentService.transferWire(5000.00));
    }
}
```

## Why it exists

Realizes `CONCEPT-istqb-v1-013-01-confirmation-vs-regression-testing` and `CONCEPT-prog-v1-007-01-parallel-fan-out`. Running an entire comprehensive regression suite on every developer commit causes CI bottlenecks. Tag filtering allows executing fast smoke tests on PR checks while deferring extensive regressions to nightly scheduled pipelines.

Concurrent execution parallelizes independent test threads across available multi-core CPU architectures, drastically reducing total execution wall-clock time while ensuring test isolation via per-thread contexts or `ThreadLocal` storage.
