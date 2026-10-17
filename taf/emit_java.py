"""Emit a Playwright-Java + JUnit 5 suite from a valid SUT model — lane
TAF/PLAN-taf-v1-001-01/D-4.

@concept CONCEPT-dsl-v1-001-01-the-sut-model
@concept CONCEPT-playwright-v1-001-01-the-locator-ladder

Same model, same ops (taf/ops.py), Java syntax: a pom.xml, a BaseTest
with the JUnit lifecycle (the fixture's Java face), one public class per
state, an Actions class, a JourneysTest, and the byte-identical
taf.manifest.json. The parity contract is structural, not verbal.
"""

import json
import os

from taf import ops

_PKG = "taf.generated"
_PKG_DIR = "src/test/java/" + _PKG.replace(".", "/")


def _j(name):
    return ops.camel(name)


def _state_class(name):
    return ops.state_class(name)


def _loc(loc):
    """The Playwright-Java locator call for one rung of the ladder."""
    rung, l = ops.locator_rung(loc)
    if rung == "role":
        extra = f', new Page.GetByRoleOptions().setName("{l["name"]}")' if "name" in l else ""
        return f'page.getByRole("{l["role"]}"{extra})'
    if rung == "label":
        return f'page.getByLabel("{l["label"]}")'
    if rung == "text":
        return f'page.getByText("{l["text"]}")'
    if rung == "placeholder":
        return f'page.getByPlaceholder("{l["placeholder"]}")'
    if rung == "testid":
        return f'page.getByTestId("{l["testid"]}")'
    if rung == "xpath":
        return f'page.locator("xpath={l["xpath"]}")'
    return f'page.locator("{l["css"]}")'


def _emit_step(step, endpoints, pad):
    form, arg = next(iter(step.items()))
    if form == "navigate":
        return [f'{pad}page.navigate(baseUrl + {_state_class(arg)}.ROUTE);']
    if form == "click":
        name = arg.get("element") if isinstance(arg, dict) else arg
        return [f"{pad}Elements.{_j(name)}(page).click();"]
    if form == "check":
        name = arg.get("element") if isinstance(arg, dict) else arg
        return [f"{pad}Elements.{_j(name)}(page).check();"]
    if form == "select":
        name = arg.get("element") if isinstance(arg, dict) else arg
        val = f'"{arg["value"]}"' if isinstance(arg, dict) and "value" in arg else ""
        return [f"{pad}Elements.{_j(name)}(page).selectOption({val});"]
    if form == "fill":
        return [f'{pad}Elements.{_j(arg["element"])}(page).fill("{arg.get("value", "")}");']
    if form == "wait-for":
        if "state" in arg:
            return [f"{pad}new {_state_class(arg['state'])}(page).expectArrived();"]
        return [f"{pad}assertThat(Elements.{_j(arg['element'])}(page)).isVisible();"]
    if form == "api":
        name = arg if isinstance(arg, str) else arg.get("endpoint")
        args = {} if isinstance(arg, str) else arg.get("args") or {}
        ep = endpoints[name]
        path, status = ep["path"], (ep.get("expect") or {}).get("status", 200)
        pexpr = f'"{path}"'
        for k, v in args.items():
            pexpr += f'.replace("{{{k}}}", "{v}")'
        lines = [f'{pad}APIResponse resp = page.request().{ep["method"].lower()}(baseUrl + {pexpr});',
                 f"{pad}assertEquals({status}, resp.status());"]
        if isinstance(arg, dict) and arg.get("save"):
            for k, jpath in arg["save"].items():
                lines.append(f'{pad}saved.put("{k}", resp.json(){_jsonpath(jpath)});')
        return lines
    if form == "dwell":
        # A pause for a watching human — observation, not synchronization.
        return [f"{pad}page.waitForTimeout({arg});"]
    if form == "wait-any":
        locs = f"Elements.{_j(arg[0])}(page)" + "".join(
            f".or(Elements.{_j(n)}(page))" for n in arg[1:])
        return [f"{pad}assertThat({locs}).isVisible();"]
    if form == "maybe":
        # An ifPresent step: try it, never fail.
        inner = _emit_step(arg, endpoints, pad + "    ")
        return [f"{pad}try {{"] + inner + [
            f"{pad}}} catch (Exception ignored) {{ /* maybe: not applicable */ }}"]
    if form == "expect":
        if isinstance(arg, dict) and "element" in arg:
            el = f"Elements.{_j(arg['element'])}(page)"
            if arg.get("soft"):
                # Collect into the SoftChecks stack; @AfterEach flushes
                # once — the run shows every failed check.
                inner = _emit_step({"expect": {k: v for k, v in arg.items()
                                               if k != "soft"}},
                                   endpoints, pad + "        ")
                stmt = inner[0].strip()
                return [
                    f"{pad}if (soft != null) {{",
                    f'{pad}    soft.check("{arg["element"]}", () -> {stmt[:-1]});',
                    f"{pad}}} else {{",
                    f"{pad}    try {{ {stmt}",
                    f'{pad}    }} catch (AssertionError e) {{ System.out.println("soft expect failed: " + e.getMessage()); }}',
                    f"{pad}}}"]
            if arg.get("hidden"):
                return [f"{pad}assertThat({el}).isHidden();"]
            if "text" in arg:
                return [f'{pad}assertThat({el}).hasText("{arg["text"]}");']
            if "count" in arg:
                return [f"{pad}assertThat({el}).hasCount({arg['count']});"]
            return [f"{pad}assertThat({el}).isVisible();"]
        if isinstance(arg, dict) and "value" in arg:
            return [f"{pad}assertEquals({json.dumps(arg.get('equals'))}, saved.get(\"{arg['value']}\"));"]
    return [f"{pad}// unsupported step: {form}"]


def _jsonpath(p):
    """'$.a.b' -> .get("a").get("b") — v1 supports dotted keys only."""
    return "".join(f'.get("{k}")' for k in str(p).lstrip("$").split(".") if k)


_HEADER = "// Generated by tafbase (taf emit --lang java). Do not edit —\n" \
          "// edit the model and regenerate.\n"


def _pom(m):
    return '''<!-- Generated by tafbase: taf emit lang=java. Do not edit;
     edit the model and regenerate. -->
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>%s</groupId>
  <artifactId>%s-tests</artifactId>
  <version>1.0.0</version>
  <properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>
  <dependencies>
    <dependency>
      <groupId>com.microsoft.playwright</groupId>
      <artifactId>playwright</artifactId>
      <version>1.49.0</version>
    </dependency>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>5.11.4</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
  <build><plugins>
    <plugin><groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-surefire-plugin</artifactId><version>3.5.2</version></plugin>
  </plugins></build>
</project>
''' % (_PKG, m["sut"]["name"])


def _basetest(m):
    return _HEADER + '''package %s;

// @concept CONCEPT-java-v1-001-01-the-junit-lifecycle
// @concept CONCEPT-playwright-v1-002-01-the-browser-context

import com.microsoft.playwright.*;
import org.junit.jupiter.api.*;

/** The fixture's Java face: one browser for the run, one fresh context
    per test — isolation by construction. */
public abstract class BaseTest {
    // @concept CONCEPT-taf-v1-003-01-the-environment
    protected static String baseUrl =
        System.getenv().getOrDefault("TAF_BASE_URL", "%s");
    private static Playwright playwright;
    private static Browser browser;
    protected BrowserContext context;
    protected Page page;
    protected SoftChecks soft;
    // @concept CONCEPT-testing-v1-004-01-the-rerun
    private static final java.util.List<String> FAILED =
        new java.util.ArrayList<>();

    @BeforeAll
    static void launch() {
        playwright = Playwright.create();
        // Headed by default — a learner should see the journey happen.
        // TAF_HEADLESS=1 for CI; TAF_SLOWMO=<ms> slows each action.
        browser = playwright.chromium().launch(new BrowserType.LaunchOptions()
            .setHeadless("1".equals(System.getenv("TAF_HEADLESS")))
            .setSlowMo(Double.parseDouble(
                System.getenv().getOrDefault("TAF_SLOWMO", "0"))));
    }

    // @concept CONCEPT-taf-v1-004-01-the-artifacts
    protected static String runDir =
        System.getenv().getOrDefault("TAF_RESULTS", "results")
        + "/" + new java.text.SimpleDateFormat("yyyyMMdd-HHmmss").format(new java.util.Date());

    @BeforeEach
    void fresh(org.junit.jupiter.api.TestInfo info) throws java.io.IOException {
        soft = new SoftChecks();
        TafJournal.begin(runDir, info.getDisplayName());
        var opts = new Browser.NewContextOptions();
        if (System.getenv("TAF_VIDEO") != null)
            opts.setRecordVideoDir(TafJournal.testDir());
        context = browser.newContext(opts);
        page = context.newPage();
    }

    @AfterEach
    void closeContext(org.junit.jupiter.api.extension.ExtensionContext ctx)
            throws java.io.IOException {
        boolean failed = ctx.getExecutionException().isPresent();
        if (failed) {
            FAILED.add(ctx.getDisplayName());
            try {  // evidence for a human: the screen, the DOM
                page.screenshot(new Page.ScreenshotOptions()
                    .setPath(TafJournal.testDir().resolve("screenshot.png")));
                java.nio.file.Files.writeString(
                    TafJournal.testDir().resolve("dom.html"), page.content());
            } catch (Exception ignored) { }
            TafJournal.event("fail", "\\\"test\\\": \\\""
                + ctx.getDisplayName().replace("\\\"", "'") + "\\\"");
            if (System.getenv("TAF_DEBUG") != null)
                page.pause();  // TAF_DEBUG: stop at the failure, browser stays open
        }
        context.close();
        // @concept CONCEPT-testing-v1-002-01-the-failure-funnel
        soft.flush();  // collect-and-flush: one fail shows every failed check
        TafJournal.end(failed ? "failed" : "passed");
    }

    @AfterAll
    static void shutdown() throws java.io.IOException {
        browser.close();
        playwright.close();
        java.nio.file.Files.createDirectories(java.nio.file.Paths.get(runDir));
        java.nio.file.Files.writeString(
            java.nio.file.Paths.get(runDir, "failed.txt"),
            String.join("\\n", FAILED));  // the rerun manifest
    }
}
''' % (_PKG, m["sut"]["base-url"])


def _page_class(name, st):
    return (_HEADER +
            f'package {_PKG};\n\n'
            "// @concept CONCEPT-pom-v1-001-01-the-page-object\n"
            "// @concept CONCEPT-playwright-v1-003-01-auto-waiting\n\n"
            "import com.microsoft.playwright.Locator;\n"
            "import com.microsoft.playwright.Page;\n"
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
            "    public void expectArrived() { assertThat(marker).isVisible(); }\n"
            "}\n")


def _elements_class(m):
    if not m.get("elements"):
        return None
    lines = [_HEADER, f"package {_PKG};\n\n",
             "// @concept CONCEPT-playwright-v1-001-01-the-locator-ladder\n\n",
             "import com.microsoft.playwright.Locator;\n",
             "import com.microsoft.playwright.Page;\n\n",
             "/** Named locators, one method each — the locator ladder. */\n",
             "public class Elements {\n"]
    for name, loc in m["elements"].items():
        lines.append(f"    public static Locator {_j(name)}(Page page) {{\n"
                     f"        return {_loc(loc)};\n    }}\n")
    lines.append("}\n")
    return "".join(lines)


def _saves(steps):
    return any(isinstance(s.get("api"), dict) and s["api"].get("save")
               for s in steps if isinstance(s, dict) and "api" in s)


_EXTRA_IMPORTS = ("import com.microsoft.playwright.*;\n"
                  "import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;\n"
                  "import static org.junit.jupiter.api.Assertions.assertEquals;\n\n")


def _actions_class(m):
    if not m.get("actions"):
        return None
    lines = [_HEADER, f"package {_PKG};\n\n", _EXTRA_IMPORTS,
             "/** One method per declared action — the edges of the graph. */\n",
             "public class Actions {\n"]
    for name, act in m["actions"].items():
        steps = act.get("do", [])
        decl = "        var saved = new java.util.HashMap<String, Object>();\n" if _saves(steps) else ""
        body = "\n".join(l for step in steps
                         for l in _emit_step(step, m.get("endpoints") or {}, "        "))
        # Every action narrates itself — the label; the run reads as a story.
        title = act.get("title", name)
        narrate = (f'        try {{ TafJournal.note("→ {title}"); }}\n'
                   f'        catch (java.io.IOException e) {{ System.out.println("→ {title}"); }}\n')
        lines.append(f"    public static void {_j(name)}(Page page, String baseUrl, SoftChecks soft) {{\n"
                     f"{narrate}{decl}{body or '        // no steps'}\n    }}\n")
    lines.append("}\n")
    return "".join(lines)


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


_CUSTOM_README = """# custom/ — hand-authored tests live here

Everything in this suite EXCEPT this directory is generated: edit the
model and regenerate, never the emitted files. Tests written by hand
belong in this directory — the emitter never writes here.

Hand-written tests inherit the suite: `BaseTest` fixtures, the page
classes, `Elements`, `Actions`. What they do not inherit is the model's
guarantees — they are not walked, not in the manifest, not covered by
parity.

This directory is also the DSL's incubator (the absorption loop,
CONCEPT-dsl-v1-013-01): a pattern that recurs here is a clause the
model should learn. It should trend toward empty.
"""


def _journal_class():
    return (_HEADER + f"package {_PKG};\n\n"
            "// @concept CONCEPT-taf-v1-004-01-the-artifacts\n\n"
            "import java.io.IOException;\n"
            "import java.nio.file.*;\n\n"
            "/** The timestamped event stream, one per test —\n"
            "    results/<runId>/<testId>/journal.jsonl. The .srt writer,\n"
            "    rerun manifest and fault reports read it downstream. */\n"
            "public class TafJournal {\n"
            "    private static java.io.BufferedWriter current;\n"
            "    private static long start;\n"
            "    private static Path dir;\n"
            "    private static final java.util.List<long[]> noteT = new java.util.ArrayList<>();\n"
            "    private static final java.util.List<String> noteL = new java.util.ArrayList<>();\n\n"
            "    public static void begin(String runDir, String testId) throws IOException {\n"
            "        dir = Paths.get(runDir, testId);\n"
            "        Files.createDirectories(dir);\n"
            "        start = System.nanoTime();\n"
            "        noteT.clear(); noteL.clear();\n"
            "        current = Files.newBufferedWriter(dir.resolve(\"journal.jsonl\"));\n"
            "    }\n\n"
            "    public static Path testDir() { return dir; }\n\n"
            "    public static void note(String label) throws IOException {\n"
            "        event(\"note\", \"\\\"label\\\": \\\"\" + label.replace(\"\\\"\", \"'\") + \"\\\"\");\n"
            "        noteT.add(new long[]{(System.nanoTime() - start) / 1_000_000L});\n"
            "        noteL.add(label);\n"
            "        System.out.println(label);\n"
            "    }\n\n"
            "    public static void event(String kind, String fieldsJson) throws IOException {\n"
            "        if (current == null) return;\n"
            "        long t = (System.nanoTime() - start) / 1_000_000L;\n"
            "        current.write(\"{\\\"t\\\": \" + t + \", \\\"event\\\": \\\"\" + kind + \"\\\", \" + fieldsJson + \"}\\n\");\n"
            "        current.flush();\n"
            "    }\n\n"
            "    private static String srtTs(long ms) {\n"
            "        return String.format(\"%02d:%02d:%02d,%03d\", ms/3600000, ms%3600000/60000, ms%60000/1000, ms%1000);\n"
            "    }\n\n"
            "    public static void end(String outcome) throws IOException {\n"
            "        if (current != null) {\n"
            "            event(\"end\", \"\\\"outcome\\\": \\\"\" + outcome + \"\\\"\");\n"
            "            current.close();\n"
            "            current = null;\n"
            "        }\n"
            "        if (dir != null && !noteL.isEmpty()) {\n"
            "            StringBuilder s = new StringBuilder();\n"
            "            for (int i = 0; i < noteL.size(); i++) {\n"
            "                long e = i + 1 < noteL.size() ? noteT.get(i + 1)[0] : noteT.get(i)[0] + 2000;\n"
            "                s.append(i + 1).append('\\n')\n"
            "                 .append(srtTs(noteT.get(i)[0])).append(\" --> \").append(srtTs(e))\n"
            "                 .append('\\n').append(noteL.get(i)).append(\"\\n\\n\");\n"
            "            }\n"
            "            Files.writeString(dir.resolve(\"journal.srt\"), s.toString());\n"
            "        }\n"
            "    }\n"
            "}\n")


def _softchecks_class():
    return (_HEADER + f"package {_PKG};\n\n"
            "// @concept CONCEPT-testing-v1-002-01-the-failure-funnel\n\n"
            "import java.util.ArrayList;\n"
            "import java.util.List;\n\n"
            "/** `soft` expects collect here instead of failing on the spot;\n"
            "    the fixture flushes once at test end — the test still fails,\n"
            "    but a run shows the whole damage, not the first hit only. */\n"
            "public class SoftChecks {\n"
            "    public final List<String> failures = new ArrayList<>();\n\n"
            "    public void check(String label, Runnable assertion) {\n"
            "        try { assertion.run(); }\n"
            "        catch (AssertionError e) { failures.add(label + \" — \" + e.getMessage()); }\n"
            "    }\n\n"
            "    public void flush() {\n"
            "        org.junit.jupiter.api.Assertions.assertTrue(failures.isEmpty(),\n"
            "            failures.size() + \" soft check(s) failed: \" + String.join(\"; \", failures));\n"
            "    }\n"
            "}\n")


def emit(model, outdir):
    """Write the suite into `outdir`; returns the list of files written."""
    pkgdir = os.path.join(outdir, _PKG_DIR)
    os.makedirs(pkgdir, exist_ok=True)
    files = {os.path.join(outdir, "pom.xml"): _pom(model),
             os.path.join(outdir, "custom", "README.md"): _CUSTOM_README,
             os.path.join(pkgdir, "SoftChecks.java"): _softchecks_class(),
             os.path.join(pkgdir, "TafJournal.java"): _journal_class(),
             os.path.join(pkgdir, "BaseTest.java"): _basetest(model),
             os.path.join(pkgdir, "Elements.java"): _elements_class(model),
             os.path.join(pkgdir, "Actions.java"): _actions_class(model),
             os.path.join(pkgdir, "JourneysTest.java"): _journeys_class(model),
             os.path.join(outdir, "taf.manifest.json"): _manifest(model)}
    for name, st in model["states"].items():
        files[os.path.join(pkgdir, f"{_state_class(name)}.java")] = _page_class(name, st)
    written = []
    for path, content in files.items():
        if content is None:
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(path)
    return written


def _manifest(m):
    return json.dumps(ops.manifest(m), indent=2, sort_keys=True) + "\n"
