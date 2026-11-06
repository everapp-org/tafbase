---
id: PLAN-taf-v1-002-01-vendor-user-separation-and-test-types
subproject: taf
status: in-progress
type: implementation-plan
authored: 2026-11-06
authors:
  - George Petrov
  - Antigravity
---

# PLAN-taf-v1-002-01 — Vendor/User Separation & Multi-Type Test Architecture

> **Core Architectural Rule ([[SPEC-taf-v1-002-01-the-framework-model]]):**
> *"The SUT model and the framework model are different objects — the second generates the programs that read the first."*
>
> - **Vendor Action (`tafbase` + `framework-spec.dsl` + Target Profile):** Generates the **Test Automation Framework** (`taf-runtime` / `tests_base` equivalent) in Python, Java 21++, TypeScript, or JavaScript. Done by the framework vendor.
> - **User Action (QA Engineer in the target framework):** Authors/derives SUT models (`*.sut.model.json`), Page Objects, and tests (UI, API, Visual, Data-Driven, Walk/Exploratory) and executes them using the generated framework. Done by the framework user.

---

## Part 1: Short Postmortem — Why Did This Confusion Happen?

### 1. Timeline of Two Conflicting Mental Models in `tafbase`
1. **October 15, 2026 ([[SPEC-taf-v1-001-04-tafbase]]):**
   - `tafbase` started as a **single-stage SUT-to-Suite compiler**: given `suts/ikc3-tracker.sut.model.json`, `taf emit` emitted a single flat directory (`generated/python/ikc3-tracker`) containing both the framework runtime (`conftest.py` / `TafSupport.java`) and the SUT tests (`test_journeys.py` / `TrackerJourneysTest.java`).
2. **October 27, 2026 ([[SPEC-taf-v1-002-01-the-framework-model]]):**
   - The architecture pivoted to **two distinct models**:
     1. **The Framework Model (`taf/dsl/framework-spec.dsl`)** — owned by the **Vendor**, defining what the framework is (step vocabulary, locator ladder, environment contract, artifacts, reporting sinks).
     2. **The SUT Model (`suts/ikc3-tracker.sut.model.json`)** — owned by the **User**, defining the application under test.
3. **Where Implementation Stopped Halfway (Root Cause):**
   - Although `framework-spec.dsl` was introduced, the code generators (`taf/codegen/{python,java,ts,js}/emitter.py`) were never split into a **Framework Emitter (Vendor)** and a **SUT/Test Emitter (User)**.
   - Instead, `emitter.emit(sut_model, out_dir)` continued to take `sut_model` as its primary input and **baked SUT-specific constants (`BASE_URL`, `sut.auth` login steps, `viewport`) directly inside the generated framework harness (`conftest.py`, `TafSupport.java`, `fixtures.ts`, `fixtures.mjs`)**.
   - Worse, `taf/runner.py` (`taf run`) defaulted to creating a temporary directory (`/tmp/taf-run-*`), generating both the framework and the tests on the fly, running them, and deleting the directory—treating code generation as a runtime step of test execution.
4. **Why Phase 3 Repeated It:**
   - During Phase 3 regeneration, we focused on fixing the 6 deficiencies listed in [[RESEARCH-taf-v1-004-01-evaluation-and-implementation-deficiencies]] and achieving 4-language parity (`python`, `java`, `ts`, `js`) on the existing `emitter.emit(model, out_dir)` signature, rather than splitting the Vendor framework artifact (`tests_base`) from the User SUT module (`suts/ikc3-tracker`).

---

## Part 2: Where Are the Different Test Types from the Researched Prototype (`qa_tafbase`)?

In the researched prototype (`qa_tafbase` — [[RESEARCH-taf-v1-002-01-the-harvest-from-qa-tafbase]], [[RESEARCH-taf-v1-003-01-the-harvest-in-detail]]), the 91.5k-line repository had a reusable engine (**`tests_base`**) and **multiple distinct test types / suite modules**.

In `tafbase` today, **everything was flattened into a single test type: a browser UI `journey`**. Here is the exact accounting of the prototype's test types and where they stand:

| # | Test Type in Researched Prototype (`qa_tafbase`) | Prototype Evidence | Current State in `tafbase` | What Is Missing / Needed |
|---|---|---|---|---|
| **1** | **Web UI Functional / E2E Journey Tests** (`portal` module, `@qa_env`, `@uat_env`, `@smoke`, `@regression`) | `CucumberTestBase.java`, `PortalStepdefs.java`, `LoginPom.java` | **Present** (`journeys` in `*.sut.model.json`) | Needs native runner tag filtering (`@Tag("smoke")`, `@pytest.mark.smoke`, `@smoke`) wired to `journey.tags`. |
| **2** | **Pure API / Backend Contract Tests** & **Hybrid API-Arrange + UI-Act Tests** | `FxoCommands.java`, SOAP/XML & REST templates, `endpoints` | **Half-baked** (`endpoints` + `api`/`save` steps exist *only inside browser journeys*) | A pure API test currently launches a full browser `Page`! Needs a **browserless `api-tests` / `request`-only test type** + `fixtures` (API arrange before UI act). |
| **3** | **Visual / Golden-Screenshot Regression Suite** (`screenshots` module, `HappyPathBase`, `ScreenshotToolMain`) | `TestBaseScreenshots.java`, `TCID_RunId_Res_Step_{Expected,Actual,Diff}.PNG`, `ThymeleafReportRenderer`, `ApplySelectionUseCase` | **Reduced to 1 step** (`{"compare-screen": "name"}` inside UI journeys) | Missing dedicated **Visual Regression test type**, `Expected/Actual/Diff` side-by-side HTML diff report, device exclusion masks, and the `promote` approval CLI. |
| **4** | **Data-Driven / Parameterized & Multilingual Tests** | `Quiz.java` (18 languages matrix), Cucumber `Scenario Outline:` + `Examples:` (`exampleCounter`) | **Missing in emitters** (even though GAKS catalog has `CONCEPT-junit-v1-002-01` & `CONCEPT-pytest-v1-002-01`) | Journeys need a `parameters` / `examples` table that emits `@ParameterizedTest` + `@MethodSource` (Java), `@pytest.mark.parametrize` (Python), and `for (const row of ...)` (TS/JS). |
| **5** | **Model-Based Seeded Walk & Coverage Suite** | New in `tafbase` (`taf/walker.py`, [[CONCEPT-qa-v1-010-01-model-based-seeded-walk]]) | **Conflated into `journeys`** (`walk-seed-42` emitted inside the same file as hand-authored journeys) | Needs its own generated test file/suite (`test_walks.py` / `TrackerWalksTest.java` / `walks.spec.ts`) and tag (`@Tag("walk")` / `@Tag("exploratory")`). |
| **6** | **Environment / Config & Preflight Self-Check Tests** | `AConfigFixerTests.java` (3-layer config verification), `suiteStopReason` preflight | **Hidden inside session fixture** | Should also be runnable as an explicit **Smoke / Preflight Check test type** (`@Tag("preflight")`) that validates URLs, endpoints, and auth before regression runs. |
| **7** | **Mobile Native / Hybrid App Tests** (`portal_apk`, `portal_ios`) | `AppStepDefsBase.java`, `ApkPom.java`, Appium capabilities, BrowserStack mobile tokens | **Only mobile web viewport emulation** (`target.viewport`) | Requires a Mobile/Appium or device-emulation Target Profile (`device:` matrix in `catalog.dsl`). |
| **8** | **Out-of-Band / Email Oracle Tests** & **Living Spec Tests** | `MailUtils.java` / `EmailActions.java` (POP3 polling + MFA scrape); Concordion `BaseFixture.java` | **Concept-only** ([[CONCEPT-testing-v1-006-01-the-living-spec]], [[CONCEPT-testing-v1-007-01-the-mail-oracle]]) | Pluggable oracle adapters in the framework runtime (`MailOracle`, storyboard HTML report). |

---

## Part 3: Task Handoff & Implementation Plan

### Phase V1 — Separate Vendor Framework Generation (`taf emit-framework`) from User Test Generation (`taf emit-tests`)
- [ ] **Task V1.1 — Split `taf/codegen/<lang>/` into `framework_emitter` (Vendor) and `sut_emitter` (User):**
  - **Vendor output (`framework/` or `taf_runtime`):** Emits the reusable, SUT-agnostic engine driven strictly by `taf/dsl/framework-spec.dsl`:
    - Python: `taf_runtime/` (`Preflight`, `SoftChecks`, `SrtWriter`, `FailureFunnel`, `ApiClient`, `VisualComparator`, `pytest` plugin hooks).
    - Java 21++: `taf.runtime.*` (`TafExtension.java`, `TafContext.java`, `SoftChecks.java`, `SrtWriter.java`, `ApiClient.java`, `RerunCondition.java`).
    - TypeScript: `taf-runtime/` (`fixtures.ts`, `soft-checks.ts`, `srt-writer.ts`, `api-client.ts`).
    - JavaScript ESM: `taf-runtime/` (`fixtures.mjs`, `soft-checks.mjs`, `srt-writer.mjs`, `api-client.mjs`).
  - **User output (`suts/<sut-name>/` or `tests/`):** Emits only SUT-specific artifacts from `*.sut.model.json` that import `taf_runtime`:
    - SUT configuration & auth bootstrap (`sut_config.py` / `TrackerSutConfig.java` / `sut.config.ts`)
    - Page Objects & Locators (`pages.py` / `TrackerPages.java` / `pages.ts`)
    - Test files organized by test type.
- [ ] **Task V1.2 — Fix the CLI Contract (`taf/__main__.py`, `taf/runner.py`):**
  - `taf emit-framework --lang {python,java,ts,js} -o <dir>`: Vendor command (takes **no** SUT model; reads only `framework-spec.dsl`).
  - `taf emit-tests <sut.model.json> --lang {python,java,ts,js} -o <dir>`: User command (generates only Page Objects + tests against the framework).
  - Remove the implicit `/tmp/taf-run-*` framework regeneration from `taf run`: `taf run` executes an existing suite directory and sets `TAF_*` runtime variables.

### Phase V2 — Restore the Missing Test Types Across All 4 Lanes
- [ ] **Task V2.1 — Test Type 1: Tagged UI Functional Journeys (`ui` / `smoke` / `regression`):**
  - Emit native runner tags from `journey.tags` (`@pytest.mark.<tag>`, JUnit `@Tag("<tag>")`, Playwright `{ tag: ['@smoke'] }`) so users can run smoke vs. regression subsets natively (`pytest -m smoke`, `mvn test -Dgroups=smoke`, `npx playwright test --grep @smoke`).
- [ ] **Task V2.2 — Test Type 2: Standalone Browserless API Tests (`api_tests`):**
  - Allow `api_journeys` (or journeys that only invoke `endpoints` / `api` / `save` / `expect`) to run **without launching a browser `Page`**, using Playwright's `APIRequestContext` / Java `HttpClient` / Python `urllib` directly (`test_api.py`, `TrackerApiTest.java`, `api.spec.ts`).
- [ ] **Task V2.3 — Test Type 3: Data-Driven / Parameterized Tests (`examples` / `parameters`):**
  - Support `examples: [{"user": "...", "expected": "..."}]` (and `locale` matrices) on journeys in `*.sut.model.json` and `framework-spec.dsl`.
  - Emit `@pytest.mark.parametrize` (Python), `@ParameterizedTest` + `@MethodSource` (Java 21++), and `for (const example of ...)` parameterized blocks (TS/JS).
- [ ] **Task V2.4 — Test Type 4: Dedicated Visual Regression Suite & Approval Workflow (`visual` + `taf promote`):**
  - Emit visual regression journeys with the `TCID_RunId_Resolution_StepId_{Expected,Actual,Diff}.png` artifact grammar, mask locators, and a `taf promote` CLI / HTML diff report for human baseline approval (completing Lane J-10).
- [ ] **Task V2.5 — Test Type 5: Separate Model-Based Walk / Exploratory Suite (`walks`):**
  - Emit seeded graph walks and edge-coverage walks into their own dedicated test module (`test_walks.py`, `TrackerWalksTest.java`, `walks.spec.ts`) tagged `@walk` so deterministic regression tests and exploratory graph walks are cleanly separated.

