---
id: CONCEPT-istqb-v1-014-01-entry-and-exit-criteria
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
---

# Entry Criteria and Exit Criteria

## Definition

Entry criteria and exit criteria are governance gates defined in CTFL v4.0 §5.1.3 that establish objective preconditions for starting and completing a test activity or project phase:

- **Entry Criteria (Definition of Ready / DoR)**: The set of conditions that must be formally satisfied before a testing phase, test suite execution, or development iteration can legitimately begin. Typical entry criteria include:
  - Testable requirements or user stories available.
  - Test environment provisioned, configured, and accessible.
  - Test data seeded and fixtures loaded.
  - Build deployed successfully and passing automated smoke/health-check tests.
  - Test tools and licenses configured.
- **Exit Criteria (Definition of Done / DoD)**: The set of conditions that must be fulfilled to declare a testing activity, test level, or release phase successfully complete. Typical exit criteria include:
  - Planned test execution completed (e.g., 100% of critical tests executed).
  - Defined coverage thresholds reached (e.g., 90% branch coverage, 100% acceptance criteria covered).
  - No open unresolved defects with severity Critical or High.
  - Residual risk assessed and accepted by product stakeholders.
  - All automated regression test suites green.

```text
+-----------------------+     Entry Criteria Met      +------------------------+
| Requirements, Code,   | --------------------------> |     Test Execution     |
| and Target Build      |       (Preflight / DoR)     |   (Automated Suites)   |
+-----------------------+                             +------------------------+
                                                                  |
                                                                  | Exit Criteria Met
                                                                  | (Gate / DoD)
                                                                  v
                                                      +------------------------+
                                                      |   Release / Sign-off   |
                                                      +------------------------+
```

```python
# Automated Preflight enforcing Entry Criteria in CI runner
def test_preflight_entry_criteria(env_client, database_pool):
    # 1. Environment reachable
    assert env_client.get_health_status() == "UP"
    # 2. Database migrated to target revision
    assert database_pool.get_schema_version() == "v2.14.0"
    # 3. Test fixtures seeded
    assert database_pool.count_seed_users() > 0
```

## Why it exists

Entry and exit criteria establish clear boundaries that protect engineering velocity and product quality:

1. **Preventing Flaky Pipeline Churn**: Attempting to run hundreds of end-to-end tests against an environment that has not passed basic entry criteria (e.g., database unavailable, backend unauthenticated) wastes pipeline resources and generates massive noise.
2. **Objective Release Gatekeeping**: Exit criteria replace subjective opinions ("it feels ready to ship") with verifiable metrics, preventing unverified code from reaching production.
3. **Continuous Alignment**: In modern CI/CD, entry criteria are codified into automated preflight checks and smoke gates, while exit criteria are codified into deployment pipeline branch protection policies.
