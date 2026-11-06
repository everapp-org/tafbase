---
id: CONCEPT-js-v1-001-01-object-freeze-and-destructuring
status: accepted
subproject: js
layer: L2-language
since: ES2015
standing: recommended
realizes: CONCEPT-prog-v1-001-01-immutable-data-carrier
---

# Frozen Plain Object and Destructuring

## Definition

In JavaScript, shallowly immutable data carriers are constructed using plain object literals sealed with `Object.freeze()`. A frozen object prevents the addition of new properties, removal of existing properties, and modification of property values. Paired with ES2015 destructuring assignment, properties can be unpacked cleanly into local variables.

```js
export function createPoint(x, y) {
  return Object.freeze({ x, y });
}

const point = createPoint(10, 20);
// point.x = 99; // Fails silently or throws TypeError in strict mode ('use strict')

const { x, y } = point;
console.log(`Point at (${x}, ${y})`);
```

## Why it exists

Plain JavaScript objects are open and mutable by default. Passing mutable objects across module boundaries or callback pipelines frequently causes bugs when a consumer modifies an object's properties in place or attaches undocumented fields.

`Object.freeze()` and destructuring realize `CONCEPT-prog-v1-001-01-immutable-data-carrier`:
1. **Mutation prevention:** Throws an immediate `TypeError` in strict mode if any code attempts to alter, add, or delete object fields.
2. **Ergonomic unpacking:** Destructuring syntax allows consumers to extract required properties directly in parameter lists or assignments.
3. **Engine optimizations:** JavaScript virtual machines (like V8) can optimize property lookups on frozen objects by freezing the hidden class transitions.
