---
id: CONCEPT-python-v1-010-01-os-environ-get
status: accepted
subproject: python
layer: L2-language
since: Python 3.0
standing: recommended
realizes: CONCEPT-prog-v1-010-01-external-environment-binding
---

# Environment Lookup with Fallback

## Definition

In Python, accessing process environment variables is accomplished via the standard `os.environ` mapping. The `os.environ.get(key, default)` method inspects the process environment for a specified key, returning the value as a string if present or falling back to a provided default without raising a `KeyError`. For strict configuration, `os.environ[key]` can be used to fail immediately when a required variable is missing.

```python
import os
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    port: int
    environment: str

    @classmethod
    def load(cls) -> "RuntimeConfig":
        return cls(
            port=int(os.environ.get("PORT", "8080")),
            environment=os.environ.get("APP_ENV", "development"),
        )
```

## Why it exists

Directly reading raw environment variables across disparate modules causes subtle failures when keys are misspelled, missing, or have unexpected formats. Furthermore, unhandled `KeyError` exceptions occurring during normal request processing lead to unexpected crashes in production.

`os.environ.get` realizes `CONCEPT-prog-v1-010-01-external-environment-binding`:
1. **Deterministic fallbacks:** Provides sensible local development defaults while allowing CI and production deployments to override values via external injection.
2. **Centralized configuration mapping:** Encourages loading and validating environment variables at application startup into typed data carriers.
3. **Twelve-Factor alignment:** Facilitates separation of code from configuration in accordance with containerized and cloud-native application architectures.
