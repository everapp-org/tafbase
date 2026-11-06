---
id: CONCEPT-ts-v1-007-01-typed-promise-concurrency
status: accepted
subproject: ts
layer: L2-language
since: TypeScript 4.0
standing: recommended
realizes: CONCEPT-prog-v1-007-01-parallel-fan-out
---

# Typed Promise Concurrency

## Definition

In TypeScript, concurrent fan-out via `Promise.all` and `Promise.allSettled` leverages variadic tuple types (introduced in TypeScript 4.0) to preserve exact heterogeneous types across concurrent operations. Passing a tuple of promises `[Promise<User>, Promise<Order[]>]` into `Promise.all` returns a strongly typed tuple `[User, Order[]]`, maintaining positional type safety across all parallel branches.

```ts
export interface User { id: string; name: string; }
export interface Order { id: string; total: number; }

export async function loadDashboard(userId: string): Promise<[User, Order[]]> {
  const userPromise: Promise<User> = fetchUser(userId);
  const ordersPromise: Promise<Order[]> = fetchOrders(userId);

  // TypeScript statically infers the exact tuple type [User, Order[]]
  const [user, orders] = await Promise.all([userPromise, ordersPromise]);
  return [user, orders];
}

declare function fetchUser(id: string): Promise<User>;
declare function fetchOrders(id: string): Promise<Order[]>;
```

## Why it exists

In JavaScript or untyped promise utilities, resolving heterogeneous operations in parallel degrades to returning an array of generic or `any` values. Developers are forced to insert manual type casts (`const user = res[0] as User`), which hide breaking changes if the promise ordering changes or an operation is modified.

Typed promise concurrency realizes `CONCEPT-prog-v1-007-01-parallel-fan-out`:
1. **Positional type integrity:** Swapping or adding an asynchronous call immediately updates the inferred tuple types, alerting downstream consumers of any mismatch.
2. **Exhaustive result checking:** With `Promise.allSettled`, TypeScript provides discriminated unions for each element (`PromiseFulfilledResult<T> | PromiseRejectedResult`), forcing callers to handle rejected states properly.
3. **High parallel performance:** Maximizes I/O concurrency without sacrificing static type guarantees.
