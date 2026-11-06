---
id: CONCEPT-java-v1-029-01-foreign-function-and-memory-api
status: accepted
subproject: java
layer: L2-language
since: Java 22
standing: situational
---

# Foreign Function and Memory API

## Definition

The Foreign Function and Memory (FFM) API (`java.lang.foreign`) enables Java programs to interoperate with code and data outside the Java runtime (off-heap memory and native C libraries) safely and efficiently without brittle JNI glue code.

```java
import java.lang.foreign.Arena;
import java.lang.foreign.FunctionDescriptor;
import java.lang.foreign.Linker;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.ValueLayout;
import java.lang.invoke.MethodHandle;

// Call C standard library strlen
Linker linker = Linker.nativeLinker();
MethodHandle strlen = linker.downcallHandle(
    linker.defaultLookup().find("strlen").orElseThrow(),
    FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS)
);

try (Arena arena = Arena.ofConfined()) {
    MemorySegment cString = arena.allocateFrom("Modern Java FFM");
    long len = (long) strlen.invokeExact(cString);
    System.out.println("C strlen: " + len);
} // Off-heap memory is freed deterministically upon arena exit
```

## Why it exists

The Java Native Interface (JNI) was notoriously difficult, unsafe, and slow: it required writing custom C/C++ stubs, compiling platform-specific shared libraries, and suffered high transition overhead with no memory safety guarantees. The FFM API introduces `Arena` for deterministic off-heap memory lifecycle management and `Linker` for direct pure-Java native function downcalls, providing type safety, memory safety, and high performance without writing a single line of C code.
