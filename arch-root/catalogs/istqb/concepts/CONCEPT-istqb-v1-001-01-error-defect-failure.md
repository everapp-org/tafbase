---
id: CONCEPT-istqb-v1-001-01-error-defect-failure
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
---

# Error, Defect, and Failure Causal Chain

## Definition

The causal chain of software flaws distinguishes between human actions, flaws in artifacts, and runtime discrepancies as defined in CTFL v4.0 §1.2.3:

1. **Error (Mistake)**: A human action that produces an incorrect result (e.g., a software developer misinterpreting a requirement or typing a wrong comparison operator).
2. **Defect (Fault / Bug)**: An imperfection or deficiency in a work product where it does not meet its requirements or specifications (e.g., an off-by-one boundary in code or an omitted case in a design document).
3. **Failure**: An event in which a component or system does not perform a required function within specified limits during runtime execution (e.g., an unhandled exception thrown or an incorrect calculation displayed to a user).

A human makes an error, introducing a defect into the codebase. When the affected code path is executed with triggering inputs, that defect causes a runtime failure. Environmental conditions (such as hardware faults or network timeouts) can also cause failures without a code defect.

```text
+----------------+       introduces       +-----------------+       triggers       +-----------------+
|  Human Error   | ---------------------> | Defect (Fault)  | -------------------> | Runtime Failure |
| (Mental lapse) |                        | (Static artifact)                      | (Dynamic event) |
+----------------+                        +-----------------+                      +-----------------+
  e.g. Logic error                          e.g. if (x > 10)                         e.g. Crash at x=10
```

## Why it exists

Understanding the error-defect-failure chain is foundational for quality engineering:

1. **Defects Can Remain Dormant**: A defect in static code only produces a runtime failure when execution reaches that path under specific input conditions. Automated testing systematically forces execution through dormant paths to trigger failures before production.
2. **Failures Are Symptoms, Not Causes**: Automated test suites report failures (assertion errors, crashes). Effective debugging requires tracing backwards from the dynamic failure to the static defect, and root-cause analysis investigates the human or procedural error that introduced it.
3. **Guiding Static vs. Dynamic Testing**: Static analysis and code reviews detect defects directly in work products without execution, preventing defects from ever manifesting as runtime failures. Dynamic automated tests detect failures during execution, proving whether defect fixes were successful.
