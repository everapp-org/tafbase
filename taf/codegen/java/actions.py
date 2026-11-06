"""The Actions class — journeys' building blocks."""

from .common import *
from .steps import _emit_step


_EXTRA_IMPORTS = ("import com.microsoft.playwright.*;\n"
                  "import org.jspecify.annotations.Nullable;\n"
                  "import taf.runtime.*;\n"
                  "import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;\n"
                  "import static org.junit.jupiter.api.Assertions.assertEquals;\n\n")


def _saves(steps):
    return any(isinstance(s.get("api"), dict) and s["api"].get("save")
               for s in steps if isinstance(s, dict) and "api" in s)


def _actions_class(m):
    if not m.get("actions"):
        return None
    lines = [_HEADER, f"package {_PKG};\n\n",
             "// @concept CONCEPT-java-v1-003-01-local-variable-type-inference\n",
             "// @concept CONCEPT-java-v1-031-01-system-getenv-binding\n\n",
             _EXTRA_IMPORTS,
             "/** One method per declared action — the edges of the graph. */\n",
             "public final class Actions {\n",
             "    private Actions() {}\n"]
    for name, act in m["actions"].items():
        steps = act.get("do", [])
        decl = "        var saved = new java.util.HashMap<String, Object>();\n" if _saves(steps) else ""
        body = "\n".join(l for step in steps
                         for l in _emit_step(step, m.get("endpoints") or {}, "        "))
        # Every action narrates itself — the label; the run reads as a story.
        title = _q("→ " + act.get("title", name))
        narrate = (f'        try {{ TafJournal.note({title}); }}\n'
                   f'        catch (java.io.IOException e) {{ System.out.println({title}); }}\n')
        lines.append(f"    public static void {_j(name)}(Page page, String baseUrl, @Nullable SoftChecks soft) {{\n"
                     f"{narrate}{decl}{body or '        // no steps'}\n    }}\n")
    lines.append("}\n")
    return "".join(lines)
