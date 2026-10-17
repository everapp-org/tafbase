---
id: RESEARCH-taf-v1-003-01-the-harvest-in-detail
status: draft
subproject: taf
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The harvest in detail — evidence appendix

The full evidence behind RESEARCH-taf-v1-002-01: every idea recovered
from the previous-generation framework (a Maven multi-module
Java/Selenium/Cucumber/Appium suite — `tests_base` engine plus
per-product modules), with the file that proves it, the translation to
generated code, and where it landed in this corpus.

Architecture context: JUnit4 + Cucumber 7.13 + Selenium 4.35 + Appium.
A prior generation exists underneath (Concordion + a TSV interpreter —
item 14). `→` marks the tafbase landing: a CONCEPT page, a lane of
`PLAN-taf-v1-001-01`, or done.

## Per-step pacing / dwell

### 1. `visibilitySleep` / `visiSleep` — the global dwell

- **Evidence:** `tests_base/.../utils/TimeUtils.java:478-498`; config
  `visibility.sleep.time=222` (`config.properties:32`); mutable static
  `Configuration.VISIBILITY_SLEEP` (`utils/Configuration.java:60,192`).
  Called before and after nearly every action
  (`com/fxcm/qa/TestBase.java:809-826`).
- **What it is:** a `Thread.sleep` wrapper with two units and a
  zero-arg overload using the global. Two purposes: let JS/animations
  settle, and make live-watching pleasant (paired with the `Overlay`).
  Overridden per call-site (`visiSleep(345)` at `TestBase.java:1082`),
  per run (config), at runtime (non-final static; even inside JS —
  `setTimeout(()=>arguments[0].click(), VISIBILITY_SLEEP)` at
  `TestBase.java:756,789`).
- **Translation:** a DSL-level annotation, not a sleep — resolved at
  codegen into per-step literals.
- **Cost:** small. **→ done** — `{"dwell": <ms>}`;
  [[CONCEPT-dsl-v1-003-01-the-dwell]].

## Browser/driver factory

### 2. "Resolution" — one token drives local emulation AND BrowserStack

- **Evidence:** `CucumberTestBase.initTest` dispatches on
  `"desktop, mobile, tablet".contains(resolution)` (`:139-143`); local
  mobile/tablet via CDP `Emulation.setDeviceMetricsOverride`
  (`:550-572`); remote via token parsing — `w10_chrome`,
  `iPhone16Pro_safari`, `GalaxyS25Ultra_samsung` → os/osVersion/
  deviceName/browserName switch (`:319-430`). Env creds override
  `browserstack.yml` (`:289-290`); `buildIdentifier=TEST_RUN_ID`,
  `sessionName=testName_example` (`:306-307`).
- **Translation:** already a mini-DSL — `device: Pixel9ProXL_chrome`
  emits the exact capabilities object; zero runtime parsing,
  compile-time vocabulary.
- **Cost:** medium. **→** lane K-11;
  [[CONCEPT-dsl-v1-012-01-the-target]].

### 3. Tag → environment → URL AND locator-version selection

- **Evidence:** `isUatTest` maps `@qa_env`/`@uat_env`/`@browserstack_*`
  to suiteName + testUrl + `DEFAULT_VERSION`
  (`CucumberTestBase.java:128-134,218-239`;
  `DEFAULT_VERSION_QA/UAT` in `Configuration.java:28-29,139-148`).
- **Translation:** `env:` bakes baseUrl + locator version into the
  emitted suite.
- **Cost:** small. **→** lane K-11; same concept as item 2.

## Waits

### 4. Named wait vocabulary, soft and hard

- **Evidence:** `waitUntilVisibilityOfElement`,
  `waitLongVisibilityOfElement`, `waitInvisibilityOfElement`,
  `waitUntilClickable`, `waitUntilVisibilityOfEitherElements`,
  `waitUntilVisibilityOfText` (`TestBase.java:962-1146`). Soft variant
  logs + saves DOM + screenshot, continues
  (`waitUntilVisibilityOfElementParametrized`, `:985-1011`); hard
  variant fails through `teststepFail` (`...AndConfirm`, `:1013-1040`).
  Implicit wait fixed at 2 s (`:419`).
- **Translation:** DSL verbs `wait`, `check` (soft), `wait any`.
- **Cost:** small. **→ done in part** — `wait-any`, `soft: true`;
  [[CONCEPT-dsl-v1-004-01-the-wait]].

## Page objects / element wrappers

### 5. `VersionedLocator` — the version × language matrix

- **Evidence:** `pom/VersionedLocator.java` (whole file);
  `ElementBase.locators` Guava `Table<Integer,Language,VersionedLocator>`
  + `addLocator` + `getBestGuessLocator` — largest version ≤ requested,
  English fallback (`pom/ElementBase.java:30,43-46,61-134`); usage
  `loginLink.addLocator(new VersionedLocator(515, Language.SPANISH,
  "xpath", "..."))` (`pom/portal/LoginPom.java:195`). A
  `screenLocation` type carries pixel coords for Sikuli
  (`VersionedLocator.java:28-34`; `ApkPom.java:85-128`).
- **Translation:** `element loginLink: xpath(...) | v515+ es:
  xpath(...)` — generated lookup, or per-version generated suites.
- **Cost:** medium/lane-sized. **→** lane I-9;
  [[CONCEPT-dsl-v1-005-01-the-versioned-locator]].

### 6. `canonicalName` + `parentName` — self-narrating actions

- **Evidence:** `new ElementBase("Sign In button in the 'Login'",
  stepName, ...)` (`LoginPom.java:110-114`); every helper logs
  `"Clicking " + canonicalName + " on " + parentName`
  (`TestBase.java:731-732`).
- **Translation:** `title` on actions/elements → emitted narration.
- **Cost:** small. **→ done** — `title` prints `→ open the TOT island`;
  [[CONCEPT-dsl-v1-006-01-the-label]].

### 7. Semantic locator kinds beyond `By`

- **Evidence:** `buttonTextLabel`, `inputTextLabel` (label →
  following-sibling input), `selectTextLabel`, `nameAttr`, `contains`
  (`ElementBase.java:76-101`).
- **Translation:** DSL kinds `button "…"`, `input labeled "…"` —
  generator emits the XPath.
- **Cost:** small. **→** folded into
  [[CONCEPT-playwright-v1-001-01-the-locator-ladder]] ("the rung above
  the rungs").

## Reporting & debugging

### 8. `teststepFail` — the single funnel for failure

- **Evidence:** `TestBase.java:1666-1691` — appends exception line
  number, shows message, calls `breakPoint()`, saves DOM, screenshots
  (Robot local / `TakesScreenshot` remote), then fails. Called by step
  defs (`PortalStepdefs.java:1398`).
- **Translation:** generated failure hook — DOM + screenshot +
  structured record.
- **Cost:** small. **→ done in part** — the pytest hook files DOM+URL;
  [[CONCEPT-testing-v1-002-01-the-failure-funnel]].

### 9. Screenshots as golden standard — grammar + approval loop

- **Evidence:** grammar
  `TestCaseId_RunId_Resolution_StepId_{Expected,Actual,Diff}.PNG`
  (`utils/screenshots/domain/ScreenshotName.java:7-18`); capture +
  compare in `ActionsBase.compareImages` (`:1052-1163`) —
  `_Expected_ALT.PNG` alternates, `REPLACE_DELETED_SCREENSHOTS` reseeds,
  `IGNORE_MISSING_SCREENSHOTS` soft-skips; per-device excluded regions
  (notch, status bar) + `pixelToleranceLevel(0.4)` + `DYN`-in-name →
  looser `minimalRectangleSize=1300`
  (`screenshots/TestBaseScreenshots.java:316-357`); scan → group →
  Thymeleaf HTML (`infra/ResultsScanner.java`,
  `infra/ThymeleafReportRenderer.java`); promotion via selection file +
  auto-generated commit message
  (`app/ApplySelectionUseCase.java:36-76,140-162`); CLI
  `cli/ScreenshotToolMain.java`.
- **Translation:** `compare screen` step + `taf promote`.
- **Cost:** lane-sized. **→** lane J-10;
  [[CONCEPT-testing-v1-003-01-the-golden-file]].

### 10. PPTX slide-per-step report

- **Evidence:** `TestBaseScreenshots.takeScreenshotCurrent` builds
  `XMLSlideShow` slides: NOMATCH → diff+actual+expected, MATCH → actual
  (`:231-313,386+`).
- **Translation:** obsolete as PPTX; the *one report card per visual
  step* idea is item 9's renderer.
- **Cost:** n/a — subsumed. **→** left behind.

### 11. Driver-aware artifact capture + dead-session recovery

- **Evidence:** `teststepFail` picks capture by driver class
  (`TestBase.java:1679-1684`); `isNullSessionId` +
  `testContext.getSavedDriver()` re-acquires a dead driver
  (`:990-993,1042-1047`; `ActionsBase.checkClassFieldsAreLoaded`
  `:107-119`); `saveDom` (`:850-874`); per-test log via Logback MDC sift
  `logreset<N>` (`LogbackUtils.java:19-30`, copied at teardown
  `CucumberTestBase.java:643`).
- **Translation:** viewport capture + DOM + console slice + step index.
- **Cost:** small. **→** folded into the failure funnel + artifacts.

### 12. `breakPoint()` + `testIsUnderTest` + `keepBrowserOpen`

- **Evidence:** empty method to hang an IDE breakpoint on
  (`utils/Utils.java:30-32`); invoked in `@AfterStep` on failure
  (`CucumberHooks.java:370-378`); `keepBrowserOpen` skips teardown
  (`CucumberTestBase.java:106,600-613`).
- **Translation:** `--debug` keeps the browser, breaks on failure.
- **Cost:** small. **→** lane L-12;
  [[CONCEPT-testing-v1-005-01-the-debug-run]].

## Configuration architecture

### 13. Layered properties, every resolved value logged

- **Evidence:** `Configuration.loadConfig` loads root
  `../config.properties` then overlays module `config.properties`
  (`utils/Configuration.java:248-272`); 3-layer resolution
  user > config > test (`AConfigFixerTests.java:138-209`); env var
  overrides (`TAFBASE_TARGET`, `RUN_TYPE`, BrowserStack creds);
  `-DconfigFile`; every resolved value logged at boot (`:99-232`).
- **Translation:** config as codegen inputs; emit a `config.dump()`.
- **Cost:** small. **→** folded into the target header (item 2/3) and
  [[CONCEPT-taf-v1-003-01-the-environment]].

## The prior-generation DSL — tafbase's ancestor

### 14. `HappyPathBase` — the TSV interpreter

- **Evidence:** `screenshots/HappyPathBase.java:104-349` (the whole
  `interpret()` commented out). Columns (`:58-67`): `scrId | step |
  action | fieldCanonicalName | label | value | scrControl |
  transLabel | transValue | jiraTicket`. Actions: `Action`,
  `WaitHeader`, `WaitH1`, `WaitH2`, `CheckFlavicon`, `CheckLink`,
  `HandleLocale`, `SetParameter`, `SetParamLabel`, `DoStep`.
  `scrControl` toggled screenshot per line; `transLabel`/`transValue`
  ran one row against localized UIs; `jiraTicket` linked the step.
  Per-test `test.properties` under `src/test/resources/screenshots/`.
- **Translation:** read as a requirements doc — the column model is a
  field-proven DSL grammar; codegen is its compile-time heir.
- **Cost:** n/a — it is our spec's ancestor. **→**
  [[CONCEPT-dsl-v1-007-01-the-step-language]].

### 15. Concordion fixtures — spec methods return display strings

- **Evidence:** `testcases/BaseFixture.java` (ConcordionRunner +
  ScreenshotExtension + RunTotals);
  `TestcasesBaseFixture.java:72-76` (StoryboardExtension = per-step
  screenshot storyboard in the HTML spec); action methods return
  `String` so specs embed results (`TestBase.java:1335-1361` —
  `moveSliderByLabel` returns the label).
- **Translation:** steps return the observed value; the report shows
  expected-vs-actual inline.
- **Cost:** medium. **→** deferred;
  [[CONCEPT-testing-v1-006-01-the-living-spec]].

## Clever extras

### 16. Failed-only rerun

- **Evidence:** `RunnerFailedCucumberApkBrowserStackQaTests.java:16` —
  `features = {"@target/rerun.txt"}`; Cucumber `rerun` plugin writes
  failed coords, a dedicated runner replays them.
- **Translation:** `taf run --last-failed` over a rerun manifest.
- **Cost:** small. **→** lane L-12;
  [[CONCEPT-testing-v1-004-01-the-rerun]].

### 17. Suite circuit breaker — `suiteStopReason`

- **Evidence:** static flag; `checkForStop()` fails fast every
  subsequent test and notifies (`TestBase.java:1647-1661`); set when
  e.g. the mail server dies (`MailUtils.java:70-71`).
- **Translation:** `requires:` preflight + runtime breaker.
- **Cost:** small. **→** lane L-12;
  [[CONCEPT-taf-v1-005-01-the-preflight]].

### 18. Mail testing — baseline + poll-new + masked compare

- **Evidence:** `MailUtils.initMailProperties` snapshots POP3 inboxes,
  stamps `setStartWaitMail` (`MailUtils.java:47-93`); polling scans
  only indices ≥ old count and requires `sentDate > startWait`
  (`:262-292`) on a sparse schedule {2,15,25,43,…,179}s over 182 s
  (`:260-261`); expected body = file with `X_PLACEHOLDER_X` wildcards +
  regex-masked `Date:`/`Deposit ID:` (`EmailActions.java:145-212`); MFA
  code scraped from mail HTML and typed into the page (`:297-326`);
  progress written to `document.title` — visible in BrowserStack
  session videos (`MailUtils.java:306-310`).
- **Translation:** `expect mail to X subject ~"..." within 180s`.
- **Cost:** medium. **→** deferred;
  [[CONCEPT-testing-v1-007-01-the-mail-oracle]].

### 19. CloudFlare human-check bypass — image match + Robot click

- **Evidence:** `CucumberTestBase.securitySiteHandler`
  (`:802-860`): screenshot → OpenCV `matchTemplate` → human-ish mouse
  move → click checkbox coords (`opencv/ImageChecker.java:24-50`).
  Companion: `sikuli/SikuliActions.java` (wait/highlight/click by
  image, offset clicks, `getTextAtRightToLabel` OCR). Also
  `headerParams: {"tradu-test":" automation"}` to get whitelisted
  (`CucumberTestBase.java:311`).
- **Translation:** `click image "verify.png"` as a `fragile` escape;
  backend cooperation header preferred.
- **Cost:** medium. **→** deferred;
  [[CONCEPT-dsl-v1-008-01-the-image-step]].

### 20. Video via external recorder + hotkeys

- **Evidence:** `VideoUtils` drives a desktop recorder with Robot
  Ctrl+Alt+6/7, moves the mp4 into the per-test results folder
  (`utils/VideoUtils.java:86-135`); `video.recording.enabled`.
- **Translation:** built-in browser video; keep the artifact lifecycle.
- **Cost:** small. **→** lane J-10/L-12;
  [[CONCEPT-taf-v1-004-01-the-artifacts]].

### 21. Live-watch trio — `Overlay`, window-minimizing, `KeepVmAwakeThread`

- **Evidence:** always-on-top Swing strip showing test name/step
  (`utils/Overlay.java:30-64`, fed by `showTopMess`/`showLowMess`);
  Win+M brings AUT frontmost (`Utils.java:50-67`); ±1 px mouse jiggle
  keeps the CI VM unlocked (`com/fxcm/qa/KeepVmAwakeThread.java:42-66`;
  `CiTestsRunner.java:84`).
- **Translation:** mostly obsolete for generated suites; keep
  `document.title` progress (free, shows in remote videos).
- **Cost:** small for the title trick. **→** folded into
  [[CONCEPT-dsl-v1-006-01-the-label]].

### 22. `CiTestsRunner` — the meta-runner

- **Evidence:** `com/fxcm/qa/CiTestsRunner.java` — arg → `TAF_RUN`
  switch picks Maven profile/project/story list (`:175-269`), invokes
  Maven in-process per story, archives into dated folders
  `TEST_REGRESSION_LOCATION/yyMMdd/HHmm/`, copies to share, announces
  start/results on Slack+Mattermost, `System.exit(0)` around a Jenkins
  exit-code bug (`:154-158`). Machine whitelist
  `test.copytox.list` + `isCopyToX` (`Utils.java:83-96`;
  `FileUtils.java:429-456`); `suiteName.txt`/`publicURL.txt` sidecars
  for the HTML matrix (`CucumberHooks.java:303-354`;
  `utils/jenkins/v2/JenkinsReportManager.java:133-139`).
- **Translation:** `tafbase run` emits
  `results/<date>/<runId>/{suiteName.txt, report.html, artifacts/}`.
- **Cost:** medium. **→** lane L-12;
  [[CONCEPT-taf-v1-004-01-the-artifacts]].

### 23. Test-ID convention inside scenario names

- **Evidence:** `getCompactTestName` extracts the first 6-char token
  (`ASM011`) as canonical ID (`CucumberHooks.java:267-289`); IDs drive
  golden filenames and result folders; feature folders map to report
  groups (`getTestFolder`, `:237-248`); `exampleCounter` disambiguates
  outline rows (`:206-217`).
- **Translation:** `test ASM011 "..."` — a first-class DSL token.
- **Cost:** small. **→** lane J-10/L-12;
  [[CONCEPT-dsl-v1-009-01-the-test-id]].

### 24. Backend fixtures — FXO SOAP/XML command templates

- **Evidence:** `utils/FxoCommands.java` (XML templates → `.bat` →
  `ResultLogin`/`TraderAccountProperties`); per-env property files
  `fxo_cmd/fxoffice_*.properties`; used for test-data lookup in steps
  (`CucumberTestBase.java:763-797`). easytest-core jar vendored in
  `lib/`; `src/test/resources/recentFailures.tsv`.
- **Translation:** `fixture:` blocks — arrange via API, act via UI.
- **Cost:** medium. **→** deferred;
  [[CONCEPT-dsl-v1-010-01-the-fixture]].

### 25. Multilingual data assets

- **Evidence:** `Quiz.java:51-80` — one xlsx column per language,
  `currentLanguage` picks it; `Language` enum, 18 languages;
  `sliderMoves`/`sliderArabicMoves` localize ordinal positions
  (commented, `TestBase.java:241-329`); Arabic flips slider direction
  (`:1347-1351`).
- **Translation:** data tables with a `lang` dimension.
- **Cost:** medium. **→** deferred;
  [[CONCEPT-dsl-v1-011-01-the-locale]].

### 26. Mobile "requirements" preamble + the `ifPresent` idiom

- **Evidence:** `AppStepDefsBase.initTest` (`:101-131`): checks Appium
  → local vs BrowserStack by tag → app reset via
  `terminateApp/removeApp/pm clear/installApp/activateApp` (`:230-270`)
  → dismiss known system dialogs (`ifPresentUseChromeWithoutAnAccount`
  `:134-164`, license/cookies unless test is MEUL `:130`) →
  `applicationNotLoaded()` sanity + fail fast (`:315-323,432-449`).
  The `ifPresent*` idiom — click only if present, never fail —
  `TestBase.java:566-636`.
- **Translation:** `requires:`/`setup:` preamble + `maybe` step.
- **Cost:** medium/small. **→ done in part** — `maybe`;
  preamble is [[CONCEPT-taf-v1-005-01-the-preflight]] (lane L-12).

### 27. The never-built `.srt` subtitles

- **Evidence:** all five teardown paths capture `Date endVideo`, derive
  the `.srt` filename beside the moved `.mp4`, and call
  `createSubTitlesFile(subTitlesFilename, endVideo)` — commented out:
  `TestBase.java:501,541-542`, `CucumberTestBase.java:629,672-673`,
  `:150,193-194` (portal_apk), `:149,192-193` (portal_ios),
  `:306,349-350` (dealer_tools). `git log -S createSubTitlesFile`:
  only ever committed commented out. `setStartVideo()`
  (`utils/ScenarioContext.java:160-166`) already captured timestamps.
- **Translation:** emitted steps know text + clock → a teardown writes
  `results/<runId>/<test>.srt` beside the video.
- **Cost:** small once labels + video exist. **→** lane H-8/J-10;
  [[CONCEPT-taf-v1-006-01-the-subtitle-track]].

### 28. Accumulate failures, flush once — the soft-assert stack

- **Evidence:** `addFailureReason` appends to `verificationErrors` and
  sets `isTestFail` *without throwing* (`TestBase.java:1093-1100`).
  Callers that continue after a defect: element lookup (`:836`),
  screenshot NOMATCH — collects *and* still emits the PPTX slides
  (`TestBaseScreenshots.java:286-303`), `handleSubmissionException`
  (`:1230-1242`), slider misses (`:1291-1333`). The flush: one
  `fail("FAIL: " + finalMess)` at test end (`HappyPathBase.java:1270`,
  commented — the contract). The tally `matchNum`/`noMatchNum` logs
  `[M x / N y]` per compare (`TestBaseScreenshots.java:306-311`), so the
  report says *how many* checks failed. One level up: static
  `List<String> testResults` per test, flushed to Slack/Mattermost and
  `screenshotsResults.txt` by `TafSrcListener.testRunFinished`
  (`TafSrcListener.java:49-58`). Dormant sibling: `Checkpoints.mark(id)`
  (`utils/results/Checkpoints.java:23-40`) is serialized to XML by every
  teardown (`TestBase.java:517-533`) — **zero callers**; half-wired like
  the `.srt` writer.
- **Translation:** `check` collects, `expect` fails fast (item 4); the
  emitted teardown writes a *failure list* — each failed check with
  step id and artifact link — so one run shows the full damage.
  `Checkpoints` argues for an emitted `milestone <id>` marker: the last
  milestone reached is what triage wants, and its zero callers teach that
  opt-in features die — emit milestones implicitly per step.
- **Cost:** small. **→ done** — `SoftChecks` collects, the
  fixture/`@AfterEach` flushes once with the whole list;
  [[CONCEPT-testing-v1-002-01-the-failure-funnel]].

## Flagged as questionable / obsolete

- `com.fxcm.ws.*`, `esq.data.*`, duplicated `FXOConnector`, Axis stubs —
  legacy backend layer; the knowledge lives in item 24.
- `utils/jenkins/` v1 vs `v2/` — two parallel report generators; v2 is
  the live one.
- `GenerateBoth`/`GenerateBothOld`/`GenerateScr`/`GenerateDB` —
  overlapping test × run matrix generators.
- `pom/bb/*` — commented-out onboarding POM set; documents an old
  onboarding flow.
- `ChatMessage` — Slack/Mattermost via shelled Python with hardcoded
  tokens (`ChatMessage.java:36,52`). Port the notification idea, never
  the implementation — credentials in a repo are a security bug.
- `TitanxMode` stub (`TestBase.java:199-201`), `driversMap` (unused
  multi-driver ambition), `SubmissionsMode`, `getJbehaveReport`
  (reads a JBehave report — archaeology).
- Robot/AWT dependence (`takeFullHdScreenshot` crops a hardcoded
  1920×1080 rect, `TestBase.java:1188-1196`) — ties correctness to
  physical display state; viewport/CDP capture replaces it.

## Landing map

| landed | lanes | deferred |
|---|---|---|
| 1 dwell · 4 soft/wait-any · 6 title · 8 funnel (half) · 26 maybe · 28 check-collect | 2,3,5,7,9,12,13,16,17,20,22,23,27,28 → H-8..L-12 | 10,14 ancestor · 15 living-spec · 18 mail · 19 image · 24 fixtures · 25 locale |
