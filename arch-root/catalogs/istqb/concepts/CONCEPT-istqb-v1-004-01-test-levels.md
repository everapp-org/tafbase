---
id: CONCEPT-istqb-v1-004-01-test-levels
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
---

# Test Levels

## Definition

Test levels are structured groups of test activities that are organized and managed together, defined in CTFL v4.0 §2.2.1. Each level targets a specific test object, utilizes specific test bases, detects characteristic defect types, and runs in an appropriate test environment:

1. **Component Testing (Unit Testing)**: Focuses on components (functions, classes, modules) in isolation. Test doubles (mocks, stubs, fakes) eliminate external dependencies. Goal: verify internal algorithmic logic, boundary conditions, and state transitions.
2. **Component Integration Testing**: Focuses on interactions and communication interfaces between internal components, packages, or services. Goal: identify protocol mismatches, serialization errors, and parameter ordering defects.
3. **System Testing**: Focuses on the overall behavior and capabilities of the complete integrated product or application. Goal: verify end-to-end business functional workflows and non-functional requirements (performance, security).
4. **System Integration Testing**: Focuses on interactions between the system under test and external third-party systems, external APIs, microservice boundaries, hardware platforms, or database tiers.
5. **Acceptance Testing**: Focuses on determining whether the system satisfies acceptance criteria and is ready for operational deployment or user sign-off (e.g., User Acceptance Testing / UAT, Operational Acceptance Testing / OAT, regulatory compliance).

```text
+-----------------------------------------------------------------+
|                       Acceptance Testing                        |  User readiness, business fit
+-----------------------------------------------------------------+
|                    System Integration Testing                   |  External APIs, payment gateways
+-----------------------------------------------------------------+
|                         System Testing                          |  End-to-end product workflows
+-----------------------------------------------------------------+
|                  Component Integration Testing                  |  Internal package/service boundaries
+-----------------------------------------------------------------+
|                    Component (Unit) Testing                     |  Isolated classes, functions
+-----------------------------------------------------------------+
```

## Why it exists

Organizing automated test suites into distinct levels prevents architectural antipatterns such as the "ice-cream cone" (where all tests run end-to-end through the UI):

1. **Feedback Speed and Isolation**: Component unit tests execute in milliseconds and pinpoint the exact line containing a defect. System tests take seconds or minutes and detect emergent integration defects across layers.
2. **Failure Attribution**: When a test fails at the component integration level, engineers immediately know the defect lies in the interface contract, avoiding deep system-level debugging.
3. **Cost and Stability**: Running tests at the lowest viable level dramatically reduces flakiness, execution time, and infrastructure costs across continuous delivery pipelines.
