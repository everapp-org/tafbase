---
id: CONCEPT-ts-v1-005-01-using-disposable
status: accepted
subproject: ts
layer: L2-language
since: TypeScript 5.2
standing: recommended
realizes: CONCEPT-prog-v1-005-01-scoped-resource-cleanup
contrasts-with: CONCEPT-java-v1-012-01-try-with-resources-and-cleaner
---

# Explicit Resource Management with Using and Disposable

## Definition

Introduced in TypeScript 5.2 (implementing the TC39 Stage 3 Explicit Resource Management proposal), `using` and `await using` declarations provide deterministic scope-based disposal. Objects implementing the global `Disposable` interface (with `[Symbol.dispose]()`) or `AsyncDisposable` interface (with `[Symbol.asyncDispose]()`) are automatically cleaned up when the lexical block exits, regardless of normal return or thrown exceptions.

```ts
export class DatabaseConnection implements Disposable {
  constructor(public readonly url: string) {}

  query(sql: string): string {
    return `Results for ${sql}`;
  }

  [Symbol.dispose](): void {
    console.log(`Connection to ${this.url} closed.`);
  }
}

export function executeWork(): void {
  using conn = new DatabaseConnection("postgres://localhost:5432/app");
  conn.query("SELECT 1");
} // conn[Symbol.dispose]() is guaranteed to be invoked here
```

## Why it exists

Prior to TypeScript 5.2, deterministic cleanup required wrapping every resource acquisition in nested `try ... finally` blocks. Asynchronous workflows with multiple transient resources suffered from severe boilerplate (often called "finally pyramid of doom") and high risk of leaking resources if an exception was thrown before entering a `finally` block.

`using` and `Disposable` realize `CONCEPT-prog-v1-005-01-scoped-resource-cleanup`:
1. **Lexical RAII semantics:** Brings RAII (Resource Acquisition Is Initialization) semantics to TypeScript with zero boilerplate.
2. **Reverse disposal order:** Multiple `using` declarations in the same block are disposed of in reverse order of initialization (LIFO).
3. **Contrast with Java:** Java's `try`-with-resources (`CONCEPT-java-v1-012-01-try-with-resources-and-cleaner`) requires an explicit `try (...)` wrapper block, whereas TypeScript's `using` declaration attaches directly to any standard block scope (function, loop, or `if` statement).
