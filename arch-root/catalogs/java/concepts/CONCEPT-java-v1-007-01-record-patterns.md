---
id: CONCEPT-java-v1-007-01-record-patterns
status: accepted
subproject: java
layer: L2-language
since: Java 21
standing: recommended
realizes: CONCEPT-prog-v1-003-01-exhaustive-branching
requires: CONCEPT-java-v1-002-01-records, CONCEPT-java-v1-006-01-pattern-matching-instanceof-and-switch
---

# Record Patterns and Nested Destructuring

## Definition

Record patterns deconstruct record instances directly in pattern positions (`instanceof` and `switch`), binding individual record components to local variables in a single declarative step. Deconstruction can be arbitrarily nested.

```java
public record Point(int x, int y) {}
public record ColoredPoint(Point point, String color) {}
public record Window(ColoredPoint topLeft, ColoredPoint bottomRight) {}

public void render(Object shape) {
    if (shape instanceof Window(
            ColoredPoint(Point(int x1, int y1), String c1),
            ColoredPoint(Point(int x2, int y2), String c2))) {
        System.out.printf("Window [%s,%s] from (%d,%d) to (%d,%d)%n", c1, c2, x1, y1, x2, y2);
    }
}
```

## Why it exists

Extracting nested data from immutable carriers historically required repetitive accessor calls (`window.topLeft().point().x()`) paired with defensive null checks or manual type assertions at each layer of the hierarchy. Record patterns invert construction: where a constructor takes arguments and builds an object, a record pattern matches an object and extracts its constituent parts into variables. When combined with sealed types and switch expressions, record patterns enable concise, type-safe data manipulation without boilerplate getters.
