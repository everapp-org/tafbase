---
id: CONCEPT-java-v1-008-01-text-blocks
status: accepted
subproject: java
layer: L2-language
since: Java 15
standing: recommended
---

# Multi-Line Text Blocks

## Definition

Text blocks are multi-line string literals enclosed in triple quotes (`"""`) that preserve code indentation while automatically stripping incidental leading whitespace. They support line continuation escapes (`\`) and explicit trailing space escapes (`\s`).

```java
String query = """
    SELECT id, name, email
    FROM users
    WHERE status = 'ACTIVE'
      AND score > %d
    ORDER BY created_at DESC
    """.formatted(threshold);

String jsonPayload = """
    {
      "name": "Widget",
      "tags": ["alpha", "beta"],
      "enabled": true
    }
    """;
```

## Why it exists

Prior to text blocks, multi-line strings (SQL queries, JSON, HTML, XML, Markdown) required concatenation with `+`, escaped quotes `\"`, and manual `\n` line delimiters, making embedded DSLs difficult to read and format. The compiler strips incidental indentation determined by the leftmost non-whitespace character or closing delimiter, preserving essential nested indentation without requiring awkward flush-left string formatting.
