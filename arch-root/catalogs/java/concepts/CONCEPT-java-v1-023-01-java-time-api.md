---
id: CONCEPT-java-v1-023-01-java-time-api
status: accepted
subproject: java
layer: L2-language
since: Java 8
standing: recommended
---

# Immutable java.time API

## Definition

The `java.time` package (JSR-310) provides an immutable, thread-safe domain model for dates, times, durations, and intervals based on the ISO-8601 calendar, separating machine time (`Instant`) from human-oriented wall-clock time (`LocalDate`, `LocalTime`, `ZonedDateTime`, `OffsetDateTime`).

```java
Instant nowUtc = Instant.now();
LocalDate date = LocalDate.of(2026, Month.NOVEMBER, 6);
ZonedDateTime eventTime = ZonedDateTime.now(ZoneId.of("America/New_York"));

Duration timeout = Duration.ofMinutes(15);
Instant deadline = nowUtc.plus(timeout);

Period gracePeriod = Period.ofDays(30);
LocalDate renewalDate = date.plus(gracePeriod);
```

## Why it exists

Replaces legacy `java.util.Date`, `java.util.Calendar`, and `java.text.SimpleDateFormat`. Legacy date classes were notoriously mutable (leading to race conditions and defensive copy requirements), zero-indexed months confusingly (January was 0), conflated timestamps with time zones, and formatting classes were not thread-safe. The `java.time` types are completely immutable, thread-safe, mathematically sound, and aligned with ISO standards.
