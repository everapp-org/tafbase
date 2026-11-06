---
id: CONCEPT-js-v1-007-01-promise-all-and-allsettled
status: accepted
subproject: js
layer: L2-language
since: ES2020
standing: recommended
realizes: CONCEPT-prog-v1-007-01-parallel-fan-out
---

# Concurrent Promise Fan-Out

## Definition

In JavaScript, concurrent fan-out across multiple asynchronous tasks is managed through `Promise.all` and `Promise.allSettled` (ES2020). `Promise.all` executes an iterable of promises concurrently, returning an array of resolved values if all succeed, or immediately rejecting with the first encountered rejection (fail-fast). `Promise.allSettled` waits for all promises to either resolve or reject, returning an array of outcome descriptors (`{ status: 'fulfilled', value }` or `{ status: 'rejected', reason }`).

```js
export async function fetchUserData(userId) {
  const [profile, preferences, notifications] = await Promise.all([
    fetchProfile(userId),
    fetchPreferences(userId),
    fetchNotifications(userId),
  ]);
  return { profile, preferences, notifications };
}
```

## Why it exists

In asynchronous code, running independent I/O tasks sequentially with sequential `await` statements introduces unnecessary latency bottlenecks. However, initiating unmanaged promises without awaiting their aggregation risks unhandled rejections and lost error traces.

`Promise.all` and `Promise.allSettled` realize `CONCEPT-prog-v1-007-01-parallel-fan-out`:
1. **Parallel throughput:** Dispatches independent network, disk, or API operations simultaneously on the event loop.
2. **Fail-fast synchronization:** `Promise.all` ensures that if any prerequisite fails, the caller is notified immediately rather than waiting for slow sibling operations.
3. **Resilient aggregation:** `Promise.allSettled` provides complete visibility over batch jobs where partial failures are acceptable and must be individually inspected without short-circuiting.
