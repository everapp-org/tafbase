"""BaseTest + auth bootstrap — the fixture's Java face."""

from .common import *
from .steps import _emit_step


def _auth_bootstrap(m):
    """sut.auth — one sign-in per run; the session kept as storage
    state each fresh context inherits (@concept dsl-v1-016-01)."""
    act = m["sut"]["auth"]["action"]
    cls = _state_class(m["actions"][act]["from"])
    return '''
    // @concept CONCEPT-dsl-v1-016-01-the-auth-clause
    // @concept CONCEPT-playwright-v1-004-01-the-storage-state
    private static String authState;
    static void signInOnce() {
        var c = browser.newContext();
        var pg = c.newPage();
        try {
            new %s(pg).gotoRoute(baseUrl);
            Actions.%s(pg, baseUrl, null);
        } catch (RuntimeException e) {
            if (System.getenv("TAF_DEBUG") != null) pg.pause();
            throw e;
        }
        authState = runDir + "/auth-state.json";
        c.storageState(new BrowserContext.StorageStateOptions()
            .setPath(java.nio.file.Paths.get(authState)));
        c.close();
    }
''' % (cls, _j(act))


def _basetest(m):
    conf = _HEADER + '''package %s;

// @concept CONCEPT-java-v1-001-01-the-junit-lifecycle
// @concept CONCEPT-playwright-v1-002-01-the-browser-context

import com.microsoft.playwright.*;
import org.junit.jupiter.api.*;

/** The fixture's Java face: one browser for the run, one fresh context
    per test — isolation by construction. */
public abstract class BaseTest
        implements org.junit.jupiter.api.extension.TestWatcher {
    // @concept CONCEPT-taf-v1-003-01-the-environment
    protected static String baseUrl =
        System.getenv().getOrDefault("TAF_BASE_URL", "%s");
    private static Playwright playwright;
    private static Browser browser;
    protected BrowserContext context;
    protected Page page;
    protected SoftChecks soft;
    private boolean failed;
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

    // @concept CONCEPT-testing-v1-002-01-the-failure-funnel
    @Override
    public void testFailed(org.junit.jupiter.api.extension.ExtensionContext ctx,
                           Throwable cause) { failed = true; }
    @Override
    public void testSucceeded(org.junit.jupiter.api.extension.ExtensionContext ctx) {
        failed = false;
    }
    @Override
    public void testAborted(org.junit.jupiter.api.extension.ExtensionContext ctx,
                            Throwable cause) { failed = false; }

    @AfterEach
    void closeContext(org.junit.jupiter.api.TestInfo info)
            throws java.io.IOException {
        if (failed) {
            FAILED.add(info.getDisplayName());
            try {  // evidence for a human: the screen, the DOM
                page.screenshot(new Page.ScreenshotOptions()
                    .setPath(TafJournal.testDir().resolve("screenshot.png")));
                java.nio.file.Files.writeString(
                    TafJournal.testDir().resolve("dom.html"), page.content());
            } catch (Exception ignored) { }
            TafJournal.event("fail", "\\\"test\\\": \\\""
                + info.getDisplayName().replace("\\\"", "'") + "\\\"");
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
    auth = m["sut"].get("auth")
    if auth:
        conf = conf.replace(
            'getOrDefault("TAF_SLOWMO", "0"))));\n    }',
            'getOrDefault("TAF_SLOWMO", "0"))));\n'
            '        signInOnce();\n    }')
        conf = conf.replace(
            "var opts = new Browser.NewContextOptions();",
            "var opts = new Browser.NewContextOptions()\n"
            "            .setStorageStatePath("
            "java.nio.file.Paths.get(authState));")
        conf = conf.replace(
            "    @AfterAll\n    static void shutdown()",
            _auth_bootstrap(m) + "    @AfterAll\n    static void shutdown()")
    return conf
