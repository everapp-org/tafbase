---
id: CONCEPT-ts-v1-010-01-typed-env-config
status: accepted
subproject: ts
layer: L2-language
since: TypeScript 4.0
standing: recommended
realizes: CONCEPT-prog-v1-010-01-external-environment-binding
---

# Validated Environment Configuration Binding

## Definition

In TypeScript, external environment binding maps string-based environment variables from `process.env` into a strictly validated, immutable configuration interface. Helper functions validate the presence of required keys, coerce strings to numbers or booleans, check domain constraints, and return a `readonly` typed object, failing immediately at application startup if validation fails.

```ts
export interface AppEnvironment {
  readonly port: number;
  readonly databaseUrl: string;
  readonly isProduction: boolean;
}

export function loadAppEnvironment(env: Record<string, string | undefined> = process.env): AppEnvironment {
  const rawPort = env.PORT ?? '8080';
  const port = parseInt(rawPort, 10);
  if (Number.isNaN(port) || port <= 0 || port > 65535) {
    throw new Error(`Invalid PORT specified: "${rawPort}"`);
  }

  const databaseUrl = env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error("Missing required environment variable: DATABASE_URL");
  }

  return Object.freeze({
    port,
    databaseUrl,
    isProduction: env.NODE_ENV === 'production',
  });
}
```

## Why it exists

In Node.js, `process.env` typed as `NodeJS.ProcessEnv` treats all properties as `string | undefined`. Directly querying `process.env` across application components creates risks of `undefined` reference bugs, unvalidated string formats, and scattered fallback defaults.

Validated configuration binding realizes `CONCEPT-prog-v1-010-01-external-environment-binding`:
1. **Startup fail-fast:** Missing credentials or invalid ports cause an immediate startup crash rather than failing halfway through request servicing.
2. **Strict type contracts:** Downstream application services depend on a clean, typed `AppEnvironment` interface without worrying about string parsing or null checks.
3. **Environment testability:** Accepting the environment dictionary as an optional parameter makes unit testing configuration parsing trivial without mutating global `process.env`.
