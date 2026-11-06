---
id: CONCEPT-qa-v1-009-01-deterministic-replay-and-flakiness
status: accepted
subproject: qa
layer: L1-archetype
standing: recommended
realizes: CONCEPT-istqb-v1-013-01-confirmation-vs-regression-testing
---

# Deterministic Execution, Flakiness Quarantine, and Retry Discipline

## Definition

Deterministic Execution, Flakiness Quarantine, and Retry Discipline is a reliability governance architecture designed to eliminate intermittent non-deterministic test results ("flakiness") and maintain developer trust in automated test suites:

1. **Deterministic Execution**: Designing tests and test environments such that given the exact same source code commit, the test produces the identical pass or fail outcome 100% of the time. Non-deterministic sources (random data, system clock/timezones, animation timers, network latency, unordered async events) are mocked, seeded, or explicitly synchronized.
2. **Strict Retry Discipline**: Automated test retries (e.g., retrying a failing test up to 2 times in CI) are used solely as a temporary operational shock-absorber for deployment pipelines. A test that passes on retry is explicitly flagged as **Flaky** in telemetry, not as a normal clean pass. Retries must never be used to mask or normalize defects.
3. **Flakiness Quarantine**: Any test exhibiting non-deterministic behavior above a strict threshold is automatically or immediately moved into a non-blocking Quarantine suite. The test continues running to collect diagnostic data, but cannot block pull request merges until its root cause is diagnosed, fixed, and verified over multiple consecutive clean runs.

```text
Test Fails on Run 1
        |
        v
[ Retry Execution (Run 2) ]
        |
        +---- Passes? ----> Mark as FLAKY (Record Metric, Alert Team)
        |                   --> If Flakiness > 2%: Move to Quarantine Suite
        |
        +---- Fails?  ----> Mark as TRUE FAILURE (Block PR)
```

```python
# Flaky test quarantined out of the blocking PR pipeline
import pytest

@pytest.mark.quarantine(reason="Flaky race condition on payment webhook, DEF-1082")
def test_async_webhook_payment_confirmation(page):
    page.goto("/checkout")
    # ...
```

## Why it exists

Test flakiness is toxic to engineering organizations:

1. **The "Cry Wolf" Effect**: When automated tests fail intermittently due to flakiness, engineers begin ignoring CI test failures and re-running failed builds repeatedly, eventually allowing real defects and regressions into production.
2. **Protecting CI Velocity**: Quarantining flaky tests protects pull request throughput and prevents blocked developer pipelines while investigations proceed.
3. **Accountability via Telemetry**: Treating flakiness as a defect with dedicated metrics ensures that timing issues, unhandled asynchronous events, and fragile locators receive engineering attention rather than being swept under the rug of blind retries.
