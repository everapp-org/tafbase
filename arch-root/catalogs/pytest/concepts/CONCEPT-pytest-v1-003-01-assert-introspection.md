---
id: CONCEPT-pytest-v1-003-01-assert-introspection
status: accepted
subproject: pytest
layer: L2-tool
since: pytest 8.0
standing: recommended
realizes: CONCEPT-qa-v1-007-01-hard-vs-soft-assertions
---

# Assert Statement AST Introspection

## Definition

Pytest intercepts and rewrites Python's native `assert` statements at module import time using Abstract Syntax Tree (AST) rewriting. 

Instead of requiring test authors to learn specialized assertion helper methods (such as `self.assertEqual`, `self.assertIn`, or `self.assertDictEqual` from standard `unittest`), tests write standard Python expressions with plain `assert`. When an assertion evaluates to false, pytest inspects the rewritten AST to compute intermediate values, perform granular structural diffs on complex dictionaries, lists, and dataclasses, and generate detailed human-readable error reports.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class UserProfile:
    id: int
    name: str
    roles: list[str]

def test_user_profile_payload():
    actual = UserProfile(id=101, name="Jordan Lee", roles=["viewer", "editor"])
    expected = UserProfile(id=101, name="Jordan Lee", roles=["viewer", "admin"])

    # Pytest AST rewriting intercepts failure and renders precise diff:
    # Differing items: roles: ['viewer', 'editor'] != ['viewer', 'admin']
    # Use -v to see full diff
    assert actual == expected
```

## Why it exists

Realizes `CONCEPT-qa-v1-007-01-hard-vs-soft-assertions`. Clear, actionable assertion diagnostics are necessary for diagnosing test failures quickly. Helper method assertions add mental friction, while plain Python `assert` without rewriting produces an uninformative `AssertionError` with no contextual comparison values.

AST introspection brings the best of both worlds: tests are authored using clean, unadorned native language syntax, while test runners deliver rich, contextual diff diagnostics upon failure.
