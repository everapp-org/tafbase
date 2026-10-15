---
id: CONCEPT-taf-v1-009-01-the-junit-lifecycle
status: draft
subproject: taf
authored: 2026-10-14
authors:
  - George Petrov
  - Devin
---

# The JUnit lifecycle

## Definition

JUnit 5's fixture mechanism: annotated methods JUnit runs around tests.
`@BeforeAll`/`@AfterAll` run once per class (static, expensive setup like
launching a browser); `@BeforeEach`/`@AfterEach` bracket every `@Test`
(fresh context, fresh page). It is the same idea as the pytest fixture —
setup and guaranteed teardown — expressed as annotations on a base class.

```java
@BeforeAll  static void launch()   { browser = playwright.chromium().launch(); }
@BeforeEach void fresh()           { context = browser.newContext();
                                     page = context.newPage(); }
@AfterEach  void closeContext()    { context.close(); }
@AfterAll   static void shutdown() { browser.close(); }
```

## Why it exists

Generated Java tests get the same isolation contract as the pytest ones
(session browser, per-test context) through a different mechanism —
proof that the model's semantics survive the language change and only
the idiom moves.

## In this repo

`generated-java/*/src/test/java/taf/generated/BaseTest.java` — every
generated JUnit suite inherits its lifecycle from this class.
