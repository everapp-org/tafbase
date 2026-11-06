---
id: CONCEPT-python-v1-007-01-taskgroup-and-executor
status: accepted
subproject: python
layer: L2-language
since: Python 3.11
standing: recommended
realizes: CONCEPT-prog-v1-007-01-parallel-fan-out
contrasts-with: CONCEPT-java-v1-009-01-virtual-threads
---

# TaskGroup and Executor Concurrency

## Definition

In Python, structured concurrency is realized asynchronously via `asyncio.TaskGroup` (introduced in Python 3.11) and synchronously via `concurrent.futures.ThreadPoolExecutor` (or `ProcessPoolExecutor`). An `asyncio.TaskGroup` used as an asynchronous context manager spawns multiple coroutines, awaits their collective completion upon exiting the context, and cancels all remaining sibling tasks immediately if any child task raises an exception, grouping unhandled exceptions into an `ExceptionGroup`.

```python
import asyncio

async def fetch_data(source_id: int) -> str:
    await asyncio.sleep(0.01)
    return f"data-{source_id}"

async def main() -> list[str]:
    results: list[str] = []
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fetch_data(1))
        t2 = tg.create_task(fetch_data(2))
    # Context exits only after all tasks complete or an exception occurs
    return [t1.result(), t2.result()]
```

## Why it exists

Before Python 3.11, asynchronous fan-out relied primarily on `asyncio.gather()` or `asyncio.wait()`. These functions did not cancel other tasks when one failed, frequently leaving orphaned coroutines running in the background. Furthermore, handling multiple exceptions required cumbersome custom filtering, often masking critical bugs.

`asyncio.TaskGroup` realizes `CONCEPT-prog-v1-007-01-parallel-fan-out`:
1. **Guaranteed task termination:** The enclosing scope cannot terminate while background coroutines remain active.
2. **Proactive cancellation:** If one task fails, remaining tasks are promptly cancelled, conserving I/O and CPU resources.
3. **Contrast with Java:** While Java leverages lightweight virtual threads (`CONCEPT-java-v1-009-01-virtual-threads`) with `StructuredTaskScope` across blocking APIs, Python utilizes `TaskGroup` on top of an explicit cooperative event loop for I/O-bound concurrency, delegating CPU-bound work to `ProcessPoolExecutor`.
