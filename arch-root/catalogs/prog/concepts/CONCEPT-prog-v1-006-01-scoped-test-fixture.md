---
id: CONCEPT-prog-v1-006-01-scoped-test-fixture
status: accepted
subproject: prog
layer: L1-archetype
requires: CONCEPT-prog-v1-005-01-scoped-resource-cleanup
---

# Scoped Test Fixture Lifecycle

## Definition

A scoped test fixture provides a controlled, isolated execution environment for automated test cases. It encapsulates the prerequisite setup (such as seeding test databases, starting mock servers, or spinning up browser contexts) and couples it with guaranteed teardown logic executed when the test or suite boundary completes. Fixtures are composable and can be scoped hierarchically (per-suite, per-file, per-worker, or per-test).

```
fixture temporaryDirectory(): Directory {
    setup:
        val dir = Files.createTempDirectory("test-run")
    yield dir
    teardown:
        Files.deleteRecursively(dir)
}
```

## Why it exists

Automated tests frequently suffer from test pollution, order-dependency, and flakiness when side effects from one test leak into subsequent tests. Manual setup and teardown methods (such as uncoordinated `beforeAll` / `afterAll` hooks) easily drift, skip cleanup on assertion failures, or accumulate global mutable state.

Scoped test fixtures establish isolated, reproducible test runs:
1. **Isolated environments:** Each test receives pristine state, preventing cascading failures across test suites.
2. **Deterministic teardown:** Cleanup runs reliably even when assertions fail or unexpected timeouts occur.
3. **Dependency injection:** Tests declare only the fixtures they need as parameters, keeping tests concise and decoupled from infrastructure orchestration.
