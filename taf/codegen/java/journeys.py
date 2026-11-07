"""The test classes — one per test type: JourneysTest (ui),
ApiTest (browserless), VisualTest (golden grammar),
WalksTest (seeded graph walks)."""

import json

from .common import *
from .actions import _saves
from .steps import _emit_step

_SUITE_FILES = {"ui": "JourneysTest", "api": "ApiTest",
                "visual": "VisualTest", "walk": "WalksTest"}

_SUITE_TITLES = {
    "ui": "One test per declared journey — arrange, act, assert.",
    "api": "Browserless endpoint journeys — no Page ever opens.",
    "visual": "Golden-screenshot regression — `taf promote` approves baselines.",
    "walk": "Seeded graph walks — exploratory, deterministic by seed.",
}

_BASES = {"ui": "taf.runtime.BaseTest",
          "api": "taf.runtime.ApiBaseTest",
          "visual": "taf.runtime.BaseTest",
          "walk": "taf.runtime.BaseTest"}


def suite_filename(jtype):
    return _SUITE_FILES[jtype]


def _method_body_ui(m, name, j):
    """arrange/act/assert for a page-bound journey (ui, visual, walk)."""
    start = j["start"]
    ctx = {"visual": ops.journey_type(m, name) == "visual"}
    if ops.journey_examples(m, name):
        ctx["row"] = "example"
    body = ["        // arrange\n"
            "        var sut = new %s(page);\n" % _state_class(start),
            "        sut.gotoRoute(baseUrl);\n",
            "        sut.expectArrived();\n",
            "        // act\n"]
    inline = [s for s in j.get("steps", []) if isinstance(s, dict)]
    if _saves(inline):
        body.append("        var saved = new java.util.HashMap<String, Object>();\n")
    for op, arg in ops.journey_ops(m, name)[1:]:
        if op == "run":
            body.append("        Actions.%s(page, baseUrl, soft);\n" % _j(arg))
        elif op == "step":
            body.append("\n".join(
                _emit_step(arg, m.get("endpoints") or {}, "        ", ctx)) + "\n")
        elif op == "assert-marker":
            body.append("        new %s(page).expectArrived();\n" % _state_class(arg))
        elif op == "assert-final":
            body.append("        // assert\n")
            body.append("        new %s(page).expectArrived();\n" % _state_class(arg))
    if not any(op == "assert-final" for op, _ in ops.journey_ops(m, name)):
        body.append("        // assert\n")
    return body


def _method_body_api(m, name, j):
    """Browserless — `request` is the APIRequestContext."""
    ctx = {"api": True}
    if ops.journey_examples(m, name):
        ctx["row"] = "example"
    body = []
    inline = [s for s in j.get("steps", []) if isinstance(s, dict)]
    if _saves(inline):
        body.append("        var saved = new java.util.HashMap<String, Object>();\n")
    for s in inline:
        body.append("\n".join(
            _emit_step(s, m.get("endpoints") or {}, "        ", ctx)) + "\n")
    return body or ["        // no steps\n"]


def _method(m, name, jtype):
    j = m["journeys"][name]
    rows = ops.journey_examples(m, name)
    lines = []
    for t in ops.journey_tags(m, name):
        lines.append('    @Tag("%s")\n' % _esc(t))
    body = (_method_body_api(m, name, j) if jtype == "api"
            else _method_body_ui(m, name, j))
    if rows:
        provider = "%sExamples" % _j(name)
        lines.append(
            "    @ParameterizedTest(name = \"%s[{index}]\")\n"
            "    @MethodSource(\"%s\")\n"
            "    void %s(java.util.Map<String, Object> example) {\n"
            % (ops.test_name_camel(name), provider, _j(name)))
        src = [
            "    static java.util.stream.Stream<java.util.Map<String, Object>> %s() {\n"
            "        return java.util.stream.Stream.of(\n"
            % provider]
        for r in rows:
            src.append("            java.util.Map.of(%s),\n" % ", ".join(
                "%s, %s" % (_q(k), json.dumps(v)) for k, v in r.items()))
        src[-1] = src[-1].rstrip(",\n") + "\n"
        src.append("        );\n    }\n\n")
        return "".join(lines) + "".join(body + ["    }\n\n"]) + "".join(src)
    lines.append("    @Test\n    void %s() {\n" % _j(name))
    return "".join(lines + body + ["    }\n\n"])


def _imports(m, names, jtype):
    """The import block for one suite file."""
    inline = [s for name in names
              for s in m["journeys"][name].get("steps", [])
              if isinstance(s, dict)]
    has_rows = any(ops.journey_examples(m, n) for n in names)
    imports = ["import com.microsoft.playwright.*;",
               "import org.jspecify.annotations.Nullable;",
               "import taf.runtime.*;",
               "import org.junit.jupiter.api.Test;",
               "import org.junit.jupiter.api.Tag;",
               "import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;",
               "import static org.junit.jupiter.api.Assertions.assertEquals;"]
    if has_rows:
        imports.append("import org.junit.jupiter.params.ParameterizedTest;")
        imports.append("import org.junit.jupiter.params.provider.MethodSource;")
    if jtype == "api":
        return "\n".join(imports) + "\n\n"
    if any(isinstance(s, str)
           for name in names for s in m["journeys"][name].get("steps", [])):
        pass  # Actions referenced same-package — no import needed
    return "\n".join(imports) + "\n\n"


def _suite_file(m, jtype):
    """The emitted test class for one type, or None when the model has
    no journeys of it."""
    names = [n for n in m["journeys"] if ops.journey_type(m, n) == jtype]
    if not names:
        return None
    cls = _SUITE_FILES[jtype]
    lines = [_HEADER, f"package {_PKG};\n\n",
             "// @concept CONCEPT-testing-v1-001-01-arrange-act-assert\n",
             "// @concept CONCEPT-qa-v1-001-01-arrange-act-assert\n\n",
             _imports(m, names, jtype),
             "/** %s */\n" % _SUITE_TITLES[jtype],
             "public final class %s extends %s {\n\n"
             % (cls, _BASES[jtype])]
    for name in names:
        lines.append(_method(m, name, jtype))
    lines.append("}\n")
    return "".join(lines)
