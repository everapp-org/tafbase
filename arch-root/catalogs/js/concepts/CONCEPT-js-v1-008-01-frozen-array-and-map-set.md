---
id: CONCEPT-js-v1-008-01-frozen-array-and-map-set
status: accepted
subproject: js
layer: L2-language
since: ES2015
standing: recommended
realizes: CONCEPT-prog-v1-008-01-immutable-collection-literal
---

# Frozen Array Literals and Read-Only Views

## Definition

In JavaScript, immutable array collections are constructed by passing array literals to `Object.freeze([...])`. Freezing an array prevents adding elements (`push`, `unshift`), removing elements (`pop`, `shift`), splicing, or reassigning existing indices. For keyed collections (`Map` and `Set`), immutability is realized by wrapping instances in read-only proxy objects that throw errors when mutating methods (`set`, `delete`, `add`, `clear`) are invoked.

```js
export const HTTP_METHODS = Object.freeze(['GET', 'POST', 'PUT', 'DELETE']);
// HTTP_METHODS.push('PATCH'); // Throws TypeError in strict mode

export function createReadOnlySet(iterable) {
  const innerSet = new Set(iterable);
  return {
    has: (item) => innerSet.has(item),
    get size() { return innerSet.size; },
    [Symbol.iterator]: () => innerSet.values(),
  };
}
```

## Why it exists

Arrays and collections in JavaScript are mutable by default. Mutating methods like `sort()` and `reverse()` modify the calling array in place rather than returning a copy. When collections are shared as configuration sets or cached lookup lists, inadvertent in-place mutation causes unpredictable regressions.

Frozen arrays and read-only views realize `CONCEPT-prog-v1-008-01-immutable-collection-literal`:
1. **Mutation immunity:** Prevents accidental modification of constant lookup tables and global configuration collections.
2. **Safe sharing:** Enables modules to return arrays directly without defensive copying (`[...items]`).
3. **API clarity:** Clearly communicates that a returned collection is unmodifiable and represents a fixed snapshot.
