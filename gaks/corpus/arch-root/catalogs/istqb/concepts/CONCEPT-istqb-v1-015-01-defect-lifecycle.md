---
id: CONCEPT-istqb-v1-015-01-defect-lifecycle
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
requires: CONCEPT-istqb-v1-001-01-error-defect-failure
---

# Defect Management and Defect Report Lifecycle

## Definition

Defect Management is the systematic process of identifying, logging, assessing, prioritizing, resolving, and closing defects as defined in CTFL v4.0 §5.5.

A complete **Defect Report** must capture unambiguous technical evidence:
- **Identification & Title**: Unique ID and concise descriptive summary.
- **Environment**: OS version, browser build, runtime environment, backend commit hash.
- **Steps to Reproduce**: Minimal, deterministic sequence of actions required to trigger the failure.
- **Observed (Actual) Result**: Exact failure state, error message, stack trace, or unexpected behavior.
- **Expected Result**: The behavior required by the specification or test oracle.
- **Severity vs. Priority**:
  - *Severity*: The degree of technical or operational impact the defect has on the system (e.g., Critical/Blocker, Major, Minor).
  - *Priority*: The business urgency of fixing the defect (e.g., P0-Immediate, P1-High, P2-Normal). A cosmetic typo on a company landing page has Low Severity but High Priority; a memory leak in an internal nightly batch job has High Severity but Normal Priority.
- **Diagnostic Artifacts**: Screenshots, network HAR logs, execution traces, DOM snapshots, and console outputs.

**The Defect Lifecycle State Transitions**:
```text
           +-------+       assign()       +------+       resolve()      +-------+
---------> |  NEW  | -------------------> | OPEN | -------------------> | FIXED |
           +-------+                      +------+                      +-------+
               |                             |                              |
               | reject()                    | defer()                      | verify()
               v                             v                              v
           +----------+                  +----------+                  +--------+
           | REJECTED |                  | DEFERRED |                  | CLOSED |
           +----------+                  +----------+                  +--------+
                                                                            |
                                                                            | re-fail()
                                                                            v
                                                                       +----------+
                                                                       | REOPENED |
                                                                       +----------+
```

```text
Defect Report Example:
ID: DEF-2026-0891
Title: Double-click on "Checkout" button creates duplicate order records
Environment: Linux x86_64, Chromium 128.0, Backend commit 4f9b8a2
Severity: Critical (Data corruption) | Priority: P0 (Immediate release blocker)
Steps to Reproduce:
  1. Authenticate with seeded user 'test-shopper'.
  2. Add item SKU-99 to cart.
  3. Navigate to /checkout.
  4. Rapidly double-click "Submit Order" button within 150ms.
Expected Result: Exactly one order is created; second click is ignored or button disabled.
Actual Result: Two identical orders generated with IDs #1041 and #1042; credit card billed twice.
Artifacts Attached: failure_trace.zip, network_har.json, screenshot_error.png
```

## Why it exists

Defect management provides transparency, accountability, and traceability across engineering workflows:

1. **Root-Cause Remediation**: Logging standardized defect reports allows quality teams to conduct defect cluster analysis and identify systemic engineering weaknesses.
2. **Preventing Information Loss**: Vague bug reports ("it doesn't work") cause friction and prolonged resolution times; requiring steps to reproduce and diagnostic artifacts enables rapid developer triage.
3. **Closing the Feedback Loop**: Automated test failures feed directly into defect management systems as reproducible artifacts, connecting automated test executions directly to resolution tracking.
