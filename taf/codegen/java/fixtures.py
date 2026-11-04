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
        authState = runDir + "/@@auth-state@@";
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
public abstract class BaseTest {
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
        boolean headless = "1".equals(System.getenv("TAF_HEADLESS"));
        browser = playwright.chromium().launch(new BrowserType.LaunchOptions()
            .setHeadless(headless)
            .setSlowMo(Double.parseDouble(
                System.getenv().getOrDefault("TAF_SLOWMO", "0"))));
        // The run contract, printed once: what env shaped this run.
        System.out.println("taf env: base_url=" + baseUrl
            + " headless=" + headless
            + " slowmo=" + System.getenv().getOrDefault("TAF_SLOWMO", "0")
            + " video=" + (System.getenv("TAF_VIDEO") != null ? "on" : "off")
            + " arrive_ms=" + System.getenv().getOrDefault("TAF_ARRIVE_MS", "15000")
            + " results=" + runDir);
        // AUTH:CALL — the auth bootstrap splices signInOnce() here
    }

    // @concept CONCEPT-taf-v1-004-01-the-artifacts
    protected static String runDir =
        System.getenv().getOrDefault("TAF_RESULTS", "results")
        + "/" + new java.text.SimpleDateFormat("yyyyMMdd-HHmmss").format(new java.util.Date());

    @BeforeEach
    void fresh(org.junit.jupiter.api.TestInfo info) throws java.io.IOException {
        soft = new SoftChecks();
        TafJournal.begin(runDir, info.getDisplayName());
        System.out.println("── " + info.getDisplayName() + " ──");
        var opts = new Browser.NewContextOptions();
        if (System.getenv("TAF_VIDEO") != null)
            opts.setRecordVideoDir(TafJournal.testDir());
        context = browser.newContext(opts);
        page = context.newPage();
    }

    // @concept CONCEPT-testing-v1-002-01-the-failure-funnel
    // A TestWatcher fires AFTER @AfterEach — too late for evidence.
    // These two extensions land the verdict early enough: after the
    // test body, and on a @BeforeEach failure.
    @org.junit.jupiter.api.extension.RegisterExtension
    final org.junit.jupiter.api.extension.AfterTestExecutionCallback outcome =
            ctx -> {
        failed = ctx.getExecutionException()
            .map(t -> !(t instanceof org.opentest4j.TestAbortedException))
            .orElse(false);
        if (soft != null) {
            try {
                soft.flush();  // collect-and-flush: every failed check shows
            } catch (AssertionError | RuntimeException e) {
                failed = true;   // a soft-only failure is still a failure
                throw e;
            }
        }
    };
    @org.junit.jupiter.api.extension.RegisterExtension
    final org.junit.jupiter.api.extension.LifecycleMethodExecutionExceptionHandler setupFailure =
            new org.junit.jupiter.api.extension.LifecycleMethodExecutionExceptionHandler() {
        @Override
        public void handleBeforeEachMethodExecutionException(
                org.junit.jupiter.api.extension.ExtensionContext ctx,
                Throwable t) throws Throwable {
            failed = true;
            throw t;
        }
    };

    @AfterEach
    void closeContext(org.junit.jupiter.api.TestInfo info)
            throws java.io.IOException {
        try {
            if (failed) {
                FAILED.add(info.getDisplayName());
                if (page != null) {
                    try {  // evidence for a human: the screen, the DOM
                        page.screenshot(new Page.ScreenshotOptions()
                            .setPath(TafJournal.testDir().resolve("@@screenshot@@")));
                        java.nio.file.Files.writeString(
                            TafJournal.testDir().resolve("@@dom@@"), page.content());
                    } catch (Exception ignored) { }
                }
                TafJournal.event("fail", "\\\"test\\\": \\\""
                    + info.getDisplayName().replace("\\\"", "'") + "\\\"");
                if (System.getenv("TAF_DEBUG") != null && page != null)
                    page.pause();  // TAF_DEBUG: stop at the failure, browser stays open
            }
        } finally {
            try {
                if (context != null) context.close();
            } finally {
                TafJournal.end(failed ? "failed" : "passed");
            }
        }
    }

    @AfterAll
    static void shutdown() throws java.io.IOException {
        browser.close();
        playwright.close();
        java.nio.file.Files.createDirectories(java.nio.file.Paths.get(runDir));
        java.nio.file.Files.writeString(
            java.nio.file.Paths.get(runDir, "@@failed@@"),
            String.join("\\n", FAILED));  // the rerun manifest
        // The artifact manifest: where this run's evidence lives.
        System.out.println("results → " + runDir);
        if (!FAILED.isEmpty())
            System.out.println("failed → " + String.join(", ", FAILED)
                + "  (rerun: TAF_RERUN=1 mvn test)");
    }
}
''' % (_PKG, m["sut"]["base-url"])
    auth = m["sut"].get("auth")
    if auth:
        conf = conf.replace(
            '        // AUTH:CALL — the auth bootstrap splices signInOnce() here\n',
            '        signInOnce();  // AUTH:CALL\n')
    else:
        conf = conf.replace(
            '        // AUTH:CALL — the auth bootstrap splices signInOnce() here\n', '')
    if auth:
        conf = conf.replace(
            "var opts = new Browser.NewContextOptions();",
            "var opts = new Browser.NewContextOptions()\n"
            "            .setStorageStatePath("
            "java.nio.file.Paths.get(authState));")
        conf = conf.replace(
            "    @AfterAll\n    static void shutdown()",
            _auth_bootstrap(m) + "    @AfterAll\n    static void shutdown()")
    return conf
