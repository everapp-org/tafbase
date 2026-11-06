# Master Task Plan: GAKS Ontology, DSL-First Target Profiles & Clean `tafbase` Regeneration

> **Strategy:** Zero touch on current `tafbase` implementation until Phase 3. First upgrade the upstream foundations in **GAKS** (`/data/Projects/ikcx/ikc3`) and **DSL-First** (`/data/Projects/ikcx/dsl-first`), then cleanly regenerate `tafbase` (`/data/Projects/ikcx/tafbase`) with Python, Java 21++, JavaScript, and TypeScript lanes.

---

## Repository & Credential Matrix

| Repository | Path | SSH Remote | Git Identity | `gh` CLI Account |
|---|---|---|---|---|
| **IKC3 (GAKS)** | `/data/Projects/ikcx/ikc3` | `git@github-personal-mrge-org:mrge-org/ikc3.git` | `mrge-org <3890263+mrge-org@users.noreply.github.com>` | `mrge-org` |
| **DSL-First** | `/data/Projects/ikcx/dsl-first` | `git@github-personal-everapp:everapp-org/dsl-first.git` | `George Petrov <gp1960@gmail.com>` | `everapp-org` |
| **tafbase** | `/data/Projects/ikcx/tafbase` | `git@github-personal-everapp:everapp-org/tafbase.git` | `George Petrov <gp1960@gmail.com>` | `everapp-org` |

---

## The Dual Concept Ontology Architecture (in GAKS)

### 1. Programming Concepts Hierarchy
* **Tier 1 — Abstract Programming Archetypes (`CONCEPT-prog-v1-*`, Layer: `L0-Archetype`)**
  * Language-independent constructs emitted by DSL-First models: *Immutable Data Carrier*, *Closed Type Union (Sum Type)*, *Exhaustive Branching / Pattern Matching*, *Null-Safe Optionality*, *Scoped Resource Cleanup*, *Scoped Test Fixture*, *Parallel Fan-Out*, *Immutable Collection Literal*, *Lambda / Higher-Order Function*, *External / Environment Binding*.
* **Tier 2 — Host-Language Realizations (Layer: `L1-Language` & `L2-Library`)**
  * **Java 8 → 27 ("Java++") (`CONCEPT-java-v1-*`)**: Extracted from Nayden Gochev's *"Java++"* presentation — Lambdas & Method References, Default/Private Interface Methods, `try`-with-resources (effectively final), Collection Factories (`List.of`, `Map.of`), Stream Slicing (`takeWhile`/`dropWhile`), `var` Type Inference, Switch Expressions & `yield`, Helpful NPEs, Text Blocks, Records & Compact Constructors, `instanceof` Pattern Matching, Sealed Classes/Interfaces, Virtual Threads (Loom), Switch Pattern Matching, Record Deconstruction Patterns, Unnamed Variables (`_`), Flexible Constructor Bodies (statements before `super`), Simplified `void main()`, JSpecify Nullness (`@NullMarked`, `@Nullable`, `TYPE_USE` placement, pragmatic nullness vs `Optional`), Google Error Prone, Uber NullAway, Custom Bug Checkers, Lombok AST Generation, Java 23+ `-proc:full`, Manifold Extensions, ZGC/Shenandoah, Compact Object Headers, AppCDS.
  * **Python 3.12+ (`CONCEPT-python-v1-*`)**: `@dataclass(frozen=True)`, `TypeAlias` & Union Types (`A | B`), Structural Pattern Matching (`match`/`case`), Type Hints & `T | None` (`mypy`/`pyright`), Context Managers (`with` / `__enter__`/`__exit__`), Generators & `yield`, Comprehension & Tuple Literals, `asyncio` / `ThreadPoolExecutor`, Virtual Environments (`venv`).
  * **JavaScript ESM (`CONCEPT-js-v1-*`)**: ES Modules (`import`/`export`), Object/Array Destructuring, Arrow Functions & Closures, `async`/`await` & `Promise.all`, Template Literals, `Object.freeze`, Optional Chaining (`?.`) & Nullish Coalescing (`??`), JSDoc `@ts-check` Type Annotations.
  * **TypeScript (`CONCEPT-ts-v1-*`)**: `readonly` Interfaces & Type Aliases, Discriminated (Tagged) Unions, Exhaustiveness Checking (`never`), `strictNullChecks`, Utility Types (`Readonly<T>`, `Partial<T>`, `Record<K,V>`), `using` Explicit Resource Management.

### 2. QA, ISTQB & Test Automation Concepts Hierarchy
* **Tier 0 — ISTQB Foundation Level (CTFL v4.0) (`CONCEPT-istqb-v1-*`, Layer: `L0-Foundation`)**
  * **Fundamentals:** Error (Mistake) vs. Defect (Fault/Bug) vs. Failure; Verification vs. Validation; Testing vs. Debugging; The 7 Testing Principles (Exhaustive testing is impossible, Early testing / Shift-left, Defect clustering, Pesticide paradox, Testing is context-dependent, Absence-of-errors fallacy, Testing shows presence of defects).
  * **Test Levels & Types:** Component (Unit), Component Integration, System, System Integration, Acceptance (UAT); Functional vs. Non-Functional; Black-Box vs. White-Box; Confirmation Testing (Re-testing) vs. Regression Testing.
  * **Static vs. Dynamic Testing:** Static Analysis & Model Verification (refusals, compiler checks) vs. Dynamic Execution.
  * **Test Design Techniques:** Equivalence Partitioning (EP), Boundary Value Analysis (BVA), Decision Table Testing (realized by `catalog.dsl`), **State Transition Testing** (realized by `kernel.dsl` + `tafbase` state graphs), Statement & Branch/Edge Coverage (realized by `taf walk --cover`), Exploratory & Checklist-based Testing.
  * **Test Management & Oracles:** Test Oracle (realized by `marker`, `expect`, mail/visual oracles), Test Pyramid, Entry/Exit Criteria & Definition of Ready/Done (realized by `preflight`), Defect Lifecycle (realized by `result-sink`).
* **Tier 1 — Test Automation Archetypes (`CONCEPT-qa-v1-*`, Layer: `L1-Automation`)**
  * Arrange-Act-Assert (AAA), The Locator Ladder (Role/Name → Label/Text → TestID → CSS/XPath), Synchronization & Actionability, Session & Context Isolation, Page Object Model (POM), API Fixture Seeding, Hard vs. Soft (Collected) Assertions, The Failure Funnel & Artifacts, Flakiness & Deterministic Replay, Model-Based Seeded Walks.
* **Tier 2 — Tool & Runner Realizations (Layer: `L2-Library`)**
  * **Playwright (`CONCEPT-playwright-v1-*`)**: `Browser` / `BrowserContext` / `Page`, `getByRole` & Locator API, Actionability Auto-Waiting, Web-First Retrying Assertions (`expect(locator)`), `storageState` Auth Reuse, Trace Viewer & Video/DOM Snapshots, Network Interception (`page.route`), APIRequestContext.
  * **Selenium WebDriver (`CONCEPT-selenium-v1-*`)**: `WebDriver` Session Lifecycle, `By` Locators (`By.id`, `By.cssSelector`, `By.xpath`), Explicit Waits (`WebDriverWait` + `ExpectedConditions` — contrasted with Playwright auto-wait), Implicit Waits & Pitfalls, `PageFactory` / `@FindBy`, `ThreadLocal<WebDriver>` for Parallel Runs, StaleElementReferenceException Handling.
  * **JUnit 5 (`CONCEPT-junit-v1-*`)**: `@BeforeAll`/`@BeforeEach`/`@AfterEach`/`@AfterAll`, `Assertions.assertAll` (soft assertions), `@ParameterizedTest`, `@Tag` Filtering, `TestWatcher` Extensions.
  * **pytest (`CONCEPT-pytest-v1-*`)**: `@pytest.fixture(scope=...)` with `yield`, `conftest.py` Discovery, `@pytest.mark.parametrize`, Marks & Filtering (`-m`), Hooks (`pytest_runtest_makereport`).
  * **Playwright Test Runner TS/JS (`CONCEPT-pwtest-v1-*`)**: `test.extend()` Custom Fixtures, Worker-Scoped vs. Test-Scoped Fixtures, Built-in Parallel Workers & Sharding (`--shard`), `playwright.config.ts` Projects & Matrix, Retries & `test.step()`.

---

## Execution Phases & Task Checklist

### Phase 1: GAKS Upstream (`/data/Projects/ikcx/ikc3` — `mrge-org`)
- [x] **Task G1 — Ontology Frontmatter & Shared Catalog Import (`pro` / `inherit`)**
  - [x] Pull latest `origin/master` in `ikc3` and create feature branch.
  - [x] Inspect current GAKS bundle generator (`src/gaks/`, `gaks/tools/`, `gaks/bundle/`).
  - [x] Extend GAKS `CONCEPT` schema and checkers (`gaks_check.py`, `check.mjs`) to support ontology frontmatter: `layer`, `since`, `realizes`, `contrasts-with`, `requires`, `standing` (`recommended` | `situational` | `preview` | `discouraged`).
  - [x] Add shared catalog resolution (`catalogs` in `gaks.project.json`) so projects can cite standard concepts (`@concept CONCEPT-java-v1-...`, `CONCEPT-istqb-v1-...`, etc.) from the GAKS bundle without local file duplication.
- [x] **Task G2 — Programming Concepts Catalogs (`flash` / `flash_lite` subagents)**
  - [x] **G2a (`flash`):** Author Tier 1 Programming Archetypes (`CONCEPT-prog-v1-*`, 10 concepts).
  - [x] **G2b (`flash`):** Author Tier 2 Java++ Catalog (`CONCEPT-java-v1-*`, 31 concepts from presentation + JUnit lifecycle).
  - [x] **G2c (`flash`):** Author Tier 2 Python, JavaScript, and TypeScript Catalogs (`CONCEPT-python-v1-*`, `CONCEPT-js-v1-*`, `CONCEPT-ts-v1-*`, 30 concepts).
- [x] **Task G3 — ISTQB, QA & Test Automation Concepts Catalogs (`flash` / `flash_lite` subagents)**
  - [x] **G3a (`flash`):** Author Tier 0 ISTQB Foundation Catalog (`CONCEPT-istqb-v1-*`, 15 concepts) and Tier 1 QA Automation Archetypes (`CONCEPT-qa-v1-*`, 10 concepts).
  - [x] **G3b (`flash`):** Author Tier 2 Playwright (`CONCEPT-playwright-v1-*`, 10 concepts) and Selenium (`CONCEPT-selenium-v1-*`, 10 concepts) Catalogs with `realizes:` and `contrasts-with:` links.
  - [x] **G3c (`flash`):** Author Tier 2 Runner Catalogs (`CONCEPT-junit-v1-*`, `CONCEPT-pytest-v1-*`, `CONCEPT-pwtest-v1-*`, 15 concepts).
- [x] **Task G4 — GAKS Static Site "Rosetta Stone" & Prerequisite Graph (`pro` / `flash`)**
  - [x] Update `site.mjs` so concept pages automatically render cross-language / cross-tool equivalents (via `realizes:` and `contrasts-with:`) and prerequisite links (via `requires:`).
  - [x] Run GAKS test suite (90 Node tests, 43 Python/Clojure parity tests, 84 bundle checks, 19 Clojure declaration tests) and verify bundle export.

### Phase 2: DSL-First Upstream (`/data/Projects/ikcx/dsl-first` — `everapp-org`)
- [x] **Task D1 — Target Profile / Platform Binding Specification (`pro` / `inherit`)**
  - [x] Pull latest branch in `dsl-first` (`origin/main` merged with `proposal/catalog-and-behavior-extensions` on `feat/target-profiles-and-concept-ontology`).
  - [x] Author the **Target Profile** specification (`target` block / `TARGET_DSL.md` + `§5.5` in `DSL_FIRST_METHODOLOGY_GUIDE.md`) covering language version, runner, driver, dependencies, `realize`, `prefer`, `avoid`, and `budget` across Java 21++, Python 3.12, JS, and TS.
- [x] **Task D2 — Ontology & GAKS Concept Emission Guide (`pro` / `inherit`)**
  - [x] Document the two-tier ontology mapping (DSL construct → Tier 1 Archetype → Tier 2 Target Construct + `@concept` annotation), the 3-Channel Concept Arrival & `[!decision]` Funnel (`§9.4` in `DSL_FIRST_METHODOLOGY_GUIDE.md`), and the 3-tier QA/ISTQB/Tool ontology (`§14` in `DSL_FIRST_QA_GUIDE.md`).

### Phase 3: Clean Regeneration of `tafbase` (`/data/Projects/ikcx/tafbase` — `everapp-org`) — **COMPLETED**
- [x] **Task T1 — Clean-Slate Setup & GAKS Bundle Update (`pro` / `inherit`)**
  - [x] Create clean regeneration branch (`feat/clean-regeneration-4-lanes`) in `tafbase` with the new GAKS bundle and imported standard catalogs (`istqb`, `qa`, `prog`, `java`, `python`, `js`, `ts`, `playwright`, `selenium`, `junit`, `pytest`, `pwtest`).
- [x] **Task T2 — Four-Lane Deterministic Emitters (`flash` / `pro`)**
  - [x] Implement/regenerate clean emitters driven by Target Profiles and `taf/dsl/framework-spec.dsl`:
    - [x] Lane 1: **Python 3.12** (`pytest` + Playwright) (`generated/python/ikc3-tracker`)
    - [x] Lane 2: **Java 21++** (JUnit 5 + Playwright + Jackson + JSpecify `@NullMarked` + Error Prone/NullAway `pom.xml`) (`generated/java/ikc3-tracker`)
    - [x] Lane 3: **TypeScript 5.6** (`@playwright/test` native `test.extend<TafFixtures>` + strict `tsconfig.json`) (`generated/ts/ikc3-tracker`)
    - [x] Lane 4: **JavaScript ESM** (`@playwright/test` ESM + JSDoc `@ts-check`) (`generated/js/ikc3-tracker`)
  - [x] Verify byte-identical `taf.manifest.json` parity, 97/97 `pytest` tests passing, `mvn clean test-compile` with 0 warnings/errors, and 0 findings in `gaks_check.py --code` across all four lanes.

