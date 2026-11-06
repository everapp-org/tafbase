---
id: CONCEPT-java-v1-017-01-stream-gatherers
status: accepted
subproject: java
layer: L2-language
since: Java 24
standing: recommended
---

# Stream Gatherers

## Definition

Stream gatherers (`Stream.gather(Gatherer)`) extend the Stream API with intermediate operations capable of transforming streams of elements in ways that built-in intermediate operations (`map`, `filter`, `flatMap`) cannot, such as stateful, windowing, sliding, and short-circuiting intermediate transformations.

```java
import java.util.stream.Gatherers;

List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6, 7, 8);

// Fixed window chunking: chunks of size 3 -> (1, 2, 3), (4, 5, 6), (7, 8)
List<List<Integer>> fixedWindows = numbers.stream()
    .gather(Gatherers.windowFixed(3))
    .toList();

// Sliding window of size 2 -> (1, 2), (2, 3), (3, 4), ...
List<List<Integer>> slidingWindows = numbers.stream()
    .gather(Gatherers.windowSliding(2))
    .toList();

// Running prefix scan: (1, 3, 6, 10, ...)
List<Integer> runningTotals = numbers.stream()
    .gather(Gatherers.scan(() -> 0, Integer::sum))
    .toList();
```

## Why it exists

Since Java 8, `Collector` allowed customizing terminal stream operations, but the intermediate operations set was fixed in `java.util.stream.Stream`. Custom intermediate transformations—like batching items into fixed-size chunks, sliding windows, deduplicating consecutive items, or stateful accumulation—required breaking out of streams into imperative loops or external libraries. Stream gatherers provide a standardized, composable, parallel-capable SPI (`Gatherer.of(...)`) with built-in presets (`Gatherers.windowFixed`, `windowSliding`, `fold`, `scan`, `mapConcurrent`).
