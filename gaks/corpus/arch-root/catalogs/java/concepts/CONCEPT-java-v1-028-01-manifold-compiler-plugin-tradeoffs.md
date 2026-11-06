---
id: CONCEPT-java-v1-028-01-manifold-compiler-plugin-tradeoffs
status: accepted
subproject: java
layer: L3-tooling
since: Manifold 2024
standing: discouraged
---

# Manifold Compiler Plugin Trade-Offs

## Definition

Manifold is an experimental Java compiler plugin system providing language extensions such as string interpolation, extension methods, operator overloading, and structural typing via compiler bytecode transformation. While expressive, non-standard compiler plugins introduce severe architectural trade-offs.

```java
package com.example.extensions;

import manifold.ext.rt.api.Extension;

@Extension
public class StringExtensions {
    public static String echo(@Extension String text) {
        return text + " ... " + text;
    }
}

// Call site appears to add methods to java.lang.String:
// "hello".echo();
```

## Why it exists

Manifold addresses the desire for expressive features found in alternative JVM languages within standard Java source files. However, it operates by hooking deep internal compiler implementation classes rather than following the Java Community Process or OpenJDK standard APIs. This produces brittle build toolchains that break across JDK minor updates, degrades IDE analysis performance, creates confusing deviations from standard Java language semantics, and prevents libraries from being consumed cleanly by standard Java projects. Its standing is discouraged for production enterprise codebases and portable libraries.
