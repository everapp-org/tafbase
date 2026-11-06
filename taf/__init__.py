"""tafbase: DSL First test automation across Python, Java 21++, TypeScript, and JavaScript ESM."""

from taf.codegen.python import emitter as emit_python
from taf.codegen.java import emitter as emit_java


def __getattr__(name):
    if name == "emit_ts":
        from taf.codegen.ts import emitter as emit_ts
        return emit_ts
    if name == "emit_js":
        from taf.codegen.js import emitter as emit_js
        return emit_js
    raise AttributeError(f"module 'taf' has no attribute {name!r}")


__all__ = ["emit_python", "emit_java", "emit_ts", "emit_js"]
