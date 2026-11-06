---
id: CONCEPT-java-v1-026-01-records-and-jackson-serialization
status: accepted
subproject: java
layer: L3-tooling
since: Java 16
standing: recommended
requires: CONCEPT-java-v1-002-01-records
---

# Records and Jackson JSON Serialization

## Definition

Jackson 2.12+ provides native, zero-boilerplate serialization and deserialization for Java records without requiring `@JsonCreator` or `@JsonProperty` annotations on individual components. Jakarta Validation annotations can be applied directly to record components for clean DTO validation.

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public record CreateUserRequest(
    @NotBlank String username,
    @Email String email,
    @Positive int quotaLimit
) {}

// Deserialization requires no extra configuration:
ObjectMapper mapper = new ObjectMapper();
CreateUserRequest req = mapper.readValue(jsonInput, CreateUserRequest.class);
```

## Why it exists

Traditional POJOs required mutable no-argument constructors, getters, setters, or repetitive `@JsonProperty` annotations on constructors for immutable models. Jackson detects record components through the reflection API for records (`Class.getRecordComponents()`), directly invoking the canonical constructor for deserialization and the accessor methods for serialization. Combining records with Jakarta Validation produces minimal, robust, and immutable API boundary transfer objects.
