---
id: CONCEPT-istqb-v1-003-01-seven-testing-principles
status: accepted
subproject: istqb
layer: L0-theory
since: CTFL 4.0
standing: recommended
requires: CONCEPT-istqb-v1-001-01-error-defect-failure
---

# The Seven Testing Principles

## Definition

The seven testing principles defined in CTFL v4.0 §1.3 provide the universal rules governing all software testing activities:

1. **Testing shows the presence of defects, not their absence**: Testing proves that defects exist, but passing all tests can never prove that no defects remain in the software under test.
2. **Exhaustive testing is impossible**: Testing all possible combinations of inputs, preconditions, and execution paths is mathematically intractable for non-trivial software. Testing must use risk analysis, test techniques, and priorities to focus effort.
3. **Early testing saves time and money (Shift-Left)**: Defects discovered early in the lifecycle (requirements, architecture, code reviews) cost orders of magnitude less to fix than defects discovered in production or late integration phases.
4. **Defects cluster together (Pareto Principle)**: A small proportion of system components, modules, or features typically contains the majority of discovered defects and operational failures.
5. **Beware of the pesticide paradox**: Running the exact same automated tests repeatedly without modification causes them to lose defect-finding efficacy. Tests must be reviewed and evolved with new test cases and techniques to uncover new defects.
6. **Testing is context-dependent**: Testing is performed differently across different domains; testing a safety-critical medical device requires different techniques and rigor than testing an e-commerce website.
7. **Absence-of-defects fallacy**: Fixing all discovered defects and building a 100% bug-free system does not guarantee success if the software fails to meet user expectations or business goals.

```text
The Seven Principles at a Glance:
1. Presence != Absence    --> Passing tests != defect-free software
2. No Exhaustive Testing  --> Sample domains with EP, BVA, and risk analysis
3. Shift-Left Testing     --> Lint, review, and test at the earliest phase
4. Defect Clustering      --> Target testing where bugs historically cluster
5. Pesticide Paradox      --> Vary test paths, seed mutations, evolve suites
6. Context Dependent      --> Fit strategy to safety, scale, and domain risk
7. Absence Fallacy        --> Verifying bug fixes != delivering user value
```

## Why it exists

The seven principles form the philosophical foundation for all automated test design:

1. **Disciplined Automation Strategy**: Because exhaustive testing is impossible, test automation frameworks rely on rigorous input partitioning rather than brute-force loops.
2. **Managing Test Decay**: The pesticide paradox warns against static automated regression suites that never exercise novel paths; it justifies model-based testing, fuzzing, and continuous test refactoring.
3. **Combating False Confidence**: The first principle reminds engineering teams that green CI pipelines indicate the absence of *known tested regressions*, not absolute defect-free reliability.
