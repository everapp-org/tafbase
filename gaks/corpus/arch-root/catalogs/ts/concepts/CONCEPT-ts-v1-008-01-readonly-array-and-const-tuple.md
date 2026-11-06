---
id: CONCEPT-ts-v1-008-01-readonly-array-and-const-tuple
status: accepted
subproject: ts
layer: L2-language
since: TypeScript 3.4
standing: recommended
realizes: CONCEPT-prog-v1-008-01-immutable-collection-literal
---

# Readonly Collection Types and Const Tuples

## Definition

In TypeScript 3.4+, immutable collections are declared using `readonly T[]`, `ReadonlyArray<T>`, `ReadonlyMap<K, V>`, `ReadonlySet<T>`, and `as const` assertions on array literals. Marked collections disallow mutating methods (`push`, `pop`, `splice`, `set`, `delete`) at compile time. Applying `as const` to an array literal creates a fixed-length `readonly` tuple with exact literal member types.

```ts
export const ROLES = ['admin', 'operator', 'viewer'] as const;
// Type: readonly ['admin', 'operator', 'viewer']

export type Role = (typeof ROLES)[number]; // 'admin' | 'operator' | 'viewer'

export function sanitizeTags(tags: readonly string[]): readonly string[] {
  // tags.push('new'); // Error: Property 'push' does not exist on type 'readonly string[]'.
  return tags.filter((t) => t.trim().length > 0);
}
```

## Why it exists

JavaScript arrays are inherently mutable. Standard library routines such as `.sort()` mutate arrays in place, causing bugs when cached arrays or function parameters are sorted by one component while another component expects their original order.

Readonly collections and const tuples realize `CONCEPT-prog-v1-008-01-immutable-collection-literal`:
1. **Single source of truth:** A const tuple defines both the runtime array of values and derives the union type of valid strings (`(typeof ROLES)[number]`), eliminating duplicate declarations.
2. **Defensive copying elimination:** Functions accepting `readonly T[]` guarantee callers that their input arrays will not be modified, removing the need to copy arrays defensively.
3. **Zero runtime overhead:** Pure compile-time enforcement that emits standard, lightweight JavaScript arrays without wrapper objects.
