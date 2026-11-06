---
id: CONCEPT-qa-v1-010-01-model-based-seeded-walk
status: accepted
subproject: qa
layer: L1-archetype
standing: recommended
realizes: CONCEPT-istqb-v1-010-01-state-transition-testing, CONCEPT-istqb-v1-003-01-seven-testing-principles
---

# Model-Based Testing and Seeded Random State-Machine Walk

## Definition

Model-Based Testing (MBT) with Seeded Random State-Machine Walks is an automated test generation architecture where tests are derived automatically from a formal behavioral model of the system under test (such as a directed state machine or labeled transition graph).

Instead of executing static, hand-written linear scripts, a test generator traverses the state graph using a pseudo-random walk algorithm initialized with a deterministic **integer seed**:
- **State Graph Model**: Nodes represent system states and views; edges represent user actions, API calls, or events, annotated with preconditions, actions, and expected assertions.
- **Seeded Walk Engine**: Given a fixed seed (e.g., `seed = 48291`), the generator computes a deterministic sequence of transitions across the model, asserting state invariants at each step.
- **Coverage Tracking**: The engine records visited states, transitions, and combinations (0-switch, 1-switch coverage), terminating when coverage goals or step budgets are reached.
- **Deterministic Replay**: If a walk encounters an assertion failure or crash at step 42, running the walk with the exact same seed (`--seed 48291`) reproduces the identical path and failure every time.

```text
               +--------------+   view_cart()   +-----------+
      +------> | CATALOG_VIEW | --------------> | CART_VIEW |
      |        +--------------+                 +-----------+
      |               |                               |
add_item()      search()                          checkout()
      |               v                               v
      +------- +--------------+                 +-----------+
               | SEARCH_VIEW  |                 |  PAYMENT  |
               +--------------+                 +-----------+
                      ^                               |
                      +------- [Seeded Random Walk] --+
```

```python
import random

class SeededModelWalker:
    def __init__(self, model, seed: int):
        self.model = model
        self.rng = random.Random(seed)
        self.path = []

    def execute_walk(self, max_steps: int = 50):
        current_state = self.model.initial_state()
        for step in range(max_steps):
            available_transitions = self.model.get_valid_transitions(current_state)
            if not available_transitions:
                break
            # Deterministic selection based on seed RNG
            chosen_transition = self.rng.choice(available_transitions)
            self.path.append(chosen_transition.name)
            current_state = chosen_transition.execute_and_verify()
```

## Why it exists

Seeded model walks solve the fundamental tension between exploring new paths and maintaining test determinism:

1. **Defeating the Pesticide Paradox**: Hand-written tests execute the exact same happy-path sequence on every run, missing subtle bugs triggered by unorthodox navigation flows (e.g., adding an item, searching, deleting an item, pressing back, then checking out). Seeded walks explore diverse, complex permutations that human authors rarely write.
2. **Guaranteed 100% Reproducibility**: Unlike unseeded chaos monkeys or naive fuzzers whose bugs are notoriously hard to reproduce, a seeded walk failure is 100% reproducible simply by passing the failing seed number.
3. **High Return on Investment**: Writing a single state machine model enables the generation of hundreds of unique test journeys and automated edge-case exploration with zero additional test authoring overhead.
