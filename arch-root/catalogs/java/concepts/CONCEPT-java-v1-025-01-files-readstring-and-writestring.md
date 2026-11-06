---
id: CONCEPT-java-v1-025-01-files-readstring-and-writestring
status: accepted
subproject: java
layer: L2-language
since: Java 12
standing: recommended
---

# Modern Files Helpers and Path Operations

## Definition

The `java.nio.file.Files` utility class provides concise methods for file operations, including `Files.readString(Path)`, `Files.writeString(Path, CharSequence)`, `Files.mismatch(Path, Path)`, and modern factory methods like `Path.of(...)`.

```java
Path configPath = Path.of("etc", "app-config.yaml");

// Read entire file as UTF-8 String in one call
String content = Files.readString(configPath, StandardCharsets.UTF_8);

// Write String atomically with standard options
Path outputPath = Path.of("var", "output.json");
Files.writeString(outputPath, jsonPayload,
    StandardOpenOption.CREATE,
    StandardOpenOption.TRUNCATE_EXISTING);

// Find offset of first mismatched byte between two files (-1 if identical)
long mismatchOffset = Files.mismatch(configPath, Path.of("etc", "backup.yaml"));
```

## Why it exists

Reading or writing a small text file historically required ceremonies involving `BufferedReader`, `InputStreamReader`, `FileInputStream`, or third-party utility libraries. Developers frequently mishandled character encodings (defaulting to platform encoding instead of UTF-8) or neglected proper stream closure. `Files.readString` and `Files.writeString` guarantee proper UTF-8 decoding, buffered chunk transfers, and deterministic file descriptor release.
