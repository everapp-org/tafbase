---
id: CONCEPT-java-v1-009-01-virtual-threads
status: accepted
subproject: java
layer: L2-language
since: Java 21
standing: recommended
realizes: CONCEPT-prog-v1-007-01-parallel-fan-out
contrasts-with: CONCEPT-python-v1-007-01-taskgroup-and-executor
---

# Virtual Threads

## Definition

Virtual threads are lightweight, JVM-managed threads designed by Project Loom that decouple Java threads from operating system kernel threads. Millions of virtual threads can run concurrently using standard blocking I/O APIs without starving kernel resources.

```java
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i -> {
        executor.submit(() -> {
            HttpResponse<String> response = client.send(
                HttpRequest.newBuilder(uri).GET().build(),
                HttpResponse.BodyHandlers.ofString()
            );
            return response.body();
        });
    });
} // waits for all tasks to complete upon closing
```

## Why it exists

Platform threads map 1:1 to OS threads, which consume significant stack memory (~1 MB) and incur heavy kernel context-switching overhead. High-throughput servers previously abandoned simple thread-per-request blocking architectures in favor of reactive or asynchronous frameworks, which introduced complex callback chains, fragmented stack traces, and unreadable debugging profiles. Virtual threads unmount from carrier threads whenever blocking I/O occurs and mount again when data is ready, preserving the simple thread-per-task model and standard debugging tools with near-zero overhead. Never pool virtual threads; create them per task.
