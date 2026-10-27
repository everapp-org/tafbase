"""JourneysTest — one @Test per model journey."""

from .common import *
from .actions import _saves, _EXTRA_IMPORTS
from .steps import _emit_step


def _journeys_class(m):
    lines = [_HEADER, f"package {_PKG};\n\n",
             "// @concept CONCEPT-testing-v1-001-01-arrange-act-assert\n\n",
             "import org.junit.jupiter.api.Test;\n", _EXTRA_IMPORTS,
             "/** One @Test per declared journey — arrange, act, assert. */\n",
             "public class JourneysTest extends BaseTest {\n\n"]
    for name, j in m["journeys"].items():
        start = j["start"]
        body = [f"        // arrange\n"
                f"        var sut = new {_state_class(start)}(page);\n"
                f"        sut.gotoRoute(baseUrl);\n"
                f"        sut.expectArrived();\n"
                f"        // act\n"]
        if _saves([s for s in j.get("steps", []) if isinstance(s, dict)]):
            body.append("        var saved = new java.util.HashMap<String, Object>();\n")
        for op, arg in ops.journey_ops(m, name)[1:]:
            if op == "run":
                body.append(f"        Actions.{_j(arg)}(page, baseUrl, soft);\n")
            elif op == "step":
                body.append("\n".join(_emit_step(arg, m.get("endpoints") or {}, "        ")) + "\n")
            elif op == "assert-marker":
                body.append(f"        new {_state_class(arg)}(page).expectArrived();\n")
            elif op == "assert-final":
                body.append("        // assert\n")
                body.append(f"        new {_state_class(arg)}(page).expectArrived();\n")
        if not any(op == "assert-final" for op, _ in ops.journey_ops(m, name)):
            body.append("        // assert\n")
        lines.append(f"    @Test\n    void {ops.test_name_camel(name)}() {{\n{''.join(body)}    }}\n\n")
    lines.append("}\n")
    return "".join(lines)
