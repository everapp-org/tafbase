---
id: CONCEPT-istqb-v1-005-01-test-types
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
---

# Test Types: Functional, Non-Functional, Black-Box, and White-Box

## Definition

Test types characterize testing activities according to their specific quality objectives and basis of test derivation, as defined in CTFL v4.0 §2.2.2:

- **Functional Testing**: Evaluates functions that the system performs ("what" the system does). Tests evaluate correctness, completeness, and appropriateness against functional specifications, user stories, and business requirements.
- **Non-Functional Testing**: Evaluates quality characteristics of system behavior ("how well" the system does it). Categories include performance efficiency (load, stress, latency), security (vulnerability, authorization), reliability (fault tolerance, recoverability), usability, accessibility, and maintainability.
- **Black-Box Testing (Specification-Based)**: Test design techniques derived from analyzing documentation, requirements, or behavior without knowledge of internal program structure or code implementation.
- **White-Box Testing (Structure-Based)**: Test design techniques derived from analyzing internal code structure, architecture, statements, control-flow branches, and data flows.

```text
                     +----------------------------------------------+
                     |                 Test Types                   |
                     +----------------------------------------------+
                                     /             \
                       [Objective]  /               \  [Derivation]
                                   v                 v
           +-----------------------------+     +-----------------------------+
           | Functional vs Non-Functional|     |   Black-Box vs White-Box    |
           +-----------------------------+     +-----------------------------+
           | Functional: "What it does"  |     | Black-Box: Spec-based,      |
           |   - User journeys           |     |   internal code hidden      |
           |   - Business rules          |     | White-Box: Structure-based, |
           | Non-Functional: "How well"  |     |   statement & branch paths  |
           |   - Latency, load, security |     |                             |
           +-----------------------------+     +-----------------------------+
```

## Why it exists

Test types provide a multi-dimensional taxonomy that prevents teams from over-indexing on simple functional happy-paths:

1. **Orthogonal Coverage**: A system may be 100% functionally correct according to black-box requirements while failing catastrophically under concurrent load (non-functional failure) or containing dead, unreachable code branches (white-box structural gap).
2. **Technique Selection**: Identifying whether a test is black-box or white-box dictates the applicable design techniques (e.g., Equivalence Partitioning and Boundary Value Analysis for black-box vs. Statement/Branch Coverage for white-box).
3. **Comprehensive Quality Assurances**: Production readiness requires verifying functional correctness, architectural execution paths, and operational performance metrics across every release.
