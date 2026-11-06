---
id: CONCEPT-js-v1-005-01-try-finally-and-explicit-resource-management
status: accepted
subproject: js
layer: L2-language
since: ES2024
standing: recommended
realizes: CONCEPT-prog-v1-005-01-scoped-resource-cleanup
---

# Try-Finally and Explicit Resource Management

## Definition

In JavaScript, deterministic cleanup is historically implemented via `try ... finally` blocks. In modern ECMAScript (ES2024 / Stage 3 Explicit Resource Management proposal), deterministic cleanup is formalized through `using` and `await using` declarations alongside `Symbol.dispose` and `Symbol.asyncDispose`. When a resource variable declared with `using` exits its lexical block, its disposal method is called automatically.

```js
// ES2024 / Stage 3 Explicit Resource Management
class FileHandle {
  constructor(path) { this.path = path; }
  [Symbol.dispose]() {
    console.log(`Closing file handle: ${this.path}`);
  }
}

export function processFile(path) {
  using handle = new FileHandle(path);
  console.log(`Processing ${handle.path}`);
} // handle[Symbol.dispose]() is invoked deterministically upon leaving this block
```

## Why it exists

JavaScript engines rely on garbage collection for memory, but garbage collection cannot be triggered deterministically to close sockets, database connection pools, file descriptors, or browser automation contexts. In complex workflows with multiple early returns or async rejections, manual cleanup calls are easily bypassed, leading to resource leaks.

Explicit resource management realizes `CONCEPT-prog-v1-005-01-scoped-resource-cleanup`:
1. **Deterministic release:** Guarantees disposal runs the instant execution leaves the lexical block scope.
2. **Reverse acquisition order:** When multiple `using` variables are declared in a single scope, disposal methods run in reverse order (LIFO), preserving resource dependency hierarchies.
3. **Async compatibility:** Supports `await using` and `Symbol.asyncDispose` for asynchronous tear-downs (such as closing remote browser connections or committing network transactions).
