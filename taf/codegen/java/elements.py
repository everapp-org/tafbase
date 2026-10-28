"""Elements + state classes — the locator rungs spelled."""

from .common import *


def _page_class(name, st):
    return (_HEADER +
            f'package {_PKG};\n\n'
            "// @concept CONCEPT-pom-v1-001-01-the-page-object\n"
            "// @concept CONCEPT-playwright-v1-003-01-auto-waiting\n\n"
            "import com.microsoft.playwright.Locator;\n"
            "import com.microsoft.playwright.Page;\n"
            "import com.microsoft.playwright.assertions.LocatorAssertions;\n"
            "import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;\n\n"
            f"/** The '{name}' state. Its marker proves arrival. */\n"
            f"public class {_state_class(name)} {{\n"
            f'    public static final String ROUTE = "{st.get("route", "")}";\n'
            "    private final Page page;\n"
            "    private final Locator marker;\n\n"
            f"    public {_state_class(name)}(Page page) {{\n"
            "        this.page = page;\n"
            f"        this.marker = {_loc(st['marker'])};\n"
            "    }\n\n"
            "    public void gotoRoute(String baseUrl) { page.navigate(baseUrl + ROUTE); }\n"
            "    public void expectArrived() {\n"
            "        double ms = Double.parseDouble(System.getenv().getOrDefault(\"TAF_ARRIVE_MS\", \"15000\"));\n"
            "        assertThat(marker).isVisible(new LocatorAssertions.IsVisibleOptions().setTimeout(ms));\n"
            "    }\n"
            "}\n")


def _elements_class(m):
    if not m.get("elements"):
        return None
    lines = [_HEADER, f"package {_PKG};\n\n",
             "// @concept CONCEPT-playwright-v1-001-01-the-locator-ladder\n\n",
             "import com.microsoft.playwright.Locator;\n",
             "import com.microsoft.playwright.Page;\n",
             "import com.microsoft.playwright.options.AriaRole;\n\n",
             "/** Named locators, one method each — the locator ladder. */\n",
             "public class Elements {\n"]
    for name, loc in m["elements"].items():
        lines.append(f"    public static Locator {_j(name)}(Page page) {{\n"
                     f"        return {_loc(loc)};\n    }}\n")
    lines.append("}\n")
    return "".join(lines)
