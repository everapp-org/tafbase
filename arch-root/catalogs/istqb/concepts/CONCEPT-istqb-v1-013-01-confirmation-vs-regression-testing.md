---
id: CONCEPT-istqb-v1-013-01-confirmation-vs-regression-testing
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
---

# Confirmation Testing vs. Regression Testing

## Definition

Confirmation testing and regression testing are change-related testing activities defined in CTFL v4.0 §2.2.3 performed after software modifications (bug fixes, enhancements, refactorings, or environment upgrades):

- **Confirmation Testing (Re-Testing)**: Confirms that a specific reported defect has been successfully fixed. It executes the exact test cases and steps that previously failed, verifying that the defect is no longer reproducible.
- **Regression Testing**: Confirms that code modifications have not introduced unintended side effects, broken existing functionality, or exposed new defects in unchanged areas of the software.

```text
Change Event: Bug #402 fixed in Payment Gateway Module
======================================================================
1. Confirmation Testing (Targeted & Narrow):
   Re-run Bug #402 reproducer:
   --> Verify payment with prepaid card now completes successfully.

2. Regression Testing (Broad & Comprehensive):
   Run full automated regression suite:
   --> Verify standard credit card checkout is not broken.
   --> Verify shopping cart balance calculations remain accurate.
   --> Verify order fulfillment notifications are still sent.
```

## Why it exists

Understanding the dichotomy between confirmation testing and regression testing shapes continuous integration and release validation:

1. **High Risk of Fix Collateral Damage**: Empirical software engineering demonstrates that a significant percentage of bug fixes inadvertently introduce new defects into adjacent code. Passing confirmation tests is necessary but never sufficient for release readiness.
2. **Regression as Primary Target for Automation**: Because confirmation testing is typically performed once or twice per bug fix, it is often initiated interactively. In contrast, regression test suites are executed hundreds of times across builds, making regression testing the highest-return investment for automated testing.
3. **Optimizing CI Feedback Loops**: Modern test pipelines partition test suites into fast smoke/PR regression packs and comprehensive nightly regression runs, balancing fast feedback on immediate changes with thorough protection against collateral regressions.
