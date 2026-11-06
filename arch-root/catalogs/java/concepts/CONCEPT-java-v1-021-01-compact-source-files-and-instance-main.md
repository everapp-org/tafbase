---
id: CONCEPT-java-v1-021-01-compact-source-files-and-instance-main
status: accepted
subproject: java
layer: L2-language
since: Java 25
standing: recommended
---

# Compact Source Files, Instance main, and Module Import Declarations

## Definition

Compact source files allow executable Java programs to omit ceremonial `public class` declarations, `public static void main(String[] args)` signatures, and repetitive standard library imports using instance `main()` methods and module import declarations (`import module java.base;`).

```java
import module java.base;

void main() {
    IO.println("Starting task runner...");
    List<String> items = List.of("alpha", "beta", "gamma");
    items.forEach(IO::println);
}
```

## Why it exists

Writing small utilities, scripts, education examples, or CLI tools in Java historically carried onerous syntactic ceremony: mandatory class enclosures, accessibility modifiers (`public static`), String array parameter declarations, and numerous explicit imports. Compact source files eliminate this friction, allowing single-file Java applications and CLI tools to be executed directly (`java Script.java`) with syntax as lean as scripting languages while retaining Java's static typing and performance.
