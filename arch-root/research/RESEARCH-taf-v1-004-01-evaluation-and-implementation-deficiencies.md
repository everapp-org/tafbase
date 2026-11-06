---
id: RESEARCH-taf-v1-004-01-evaluation-and-implementation-deficiencies
status: draft
subproject: taf
authored: 2026-11-05
authors:
  - George Petrov
  - Antigravity
---

# Evaluation of project clarity, missing information, and implementation deficiencies

## Why this exists

A comprehensive architectural and technical evaluation of `tafbase` as of
November 2026 (branch `fix/pr1-review`). The project's contract demands
DSL-First test generation, byte-for-byte manifest parity between Python and
Java suites, honest refusals, and deep learning surfaces. This document records
an audit of whether the repository is self-explanatory to newcomers, what
information is missing, and what defects exist in the current implementation phase.

Related:
  - [[PLAN-taf-v1-001-01-tafbase]]
  - [[SPEC-taf-v1-001-04-tafbase]]
  - [[SPEC-taf-v1-002-02-the-framework-spec-dsl]]
  - [[F-taf-v1-002-02-framework-model-acceptance]]

## How it was measured

1. **Corpus & layout inspection**: Checked `arch-root/` documents against
   GAKS rules (`gaks/tools/py/gaks_check.py`), reviewed READMEs, and mapped
   the directory structure.
2. **Execution gates**: Executed unit tests (`pytest`), Java suite compilation
   (`mvn test-compile`), manifest diff checks, and CLI commands (`check`,
   `dry-run`, `env`, `walk`).
3. **Bytecode and API contract verification**: Inspected Microsoft Playwright
   Java 1.49.0 bytecode via `javap` to verify interface methods referenced by
   the Java code emitter.
4. **Boundary and negative fuzzing**: Evaluated `taf.model.validate` with
   edge-case model definitions (inline steps, unchained final states,
   reserved keyword identifiers).

## The summary

* **Self-explanatoriness**: High architectural rigor in `arch-root/`, but
  obscured by "Dual DSL" ambiguity (SUT JSON model vs. Framework Spec ANTLR
  DSL), layout discrepancies, and an undocumented Java execution story.
* **Missing information**: Lack of a formal JSON Schema for IDE validation,
  sparse documentation on complex step arguments (`api`, `save`, `expect`),
  missing workflow guidance for `taf record`, and no generic result-sink SPI.
* **Problems & deficiencies**:
  1. A broken import in `tests/test_live.py` (`from taf import emit_java`).
  2. A flawed contract test in `tests/test_spec_contract.py` that concealed
     three missing refusals in `framework-spec.dsl`.
  3. Uncompilable Java code generated for `compare-screen` (no `hasScreenshot()`
     in Playwright Java) and `api.save` (no `resp.json()` in Playwright Java
     and no JSON parser dependency).
  4. Parity gaps in Java: `TAF_RERUN` is printed but never implemented; fault
     reporting via `ikc3_sink` is absent in Java.
  5. Unfulfilled acceptance criteria (AC-7, AC-8) from `F-taf-v1-002-02`,
     leaving `dryrun.py` hardcoded and omitting `TAF_ARRIVE_MS`.
  6. Model validation gaps in `taf.model.validate`: unvalidated final states,
     false-positive reachability rejections for inline navigation, and
     unvalidated identifier names producing syntax errors in emitted code.

---

## In detail: self-explanatory evaluation

### Strengths

* **Exemplary Corpus Rigor**: The documentation in `arch-root/` sets a high
  bar. Plans define draft release notes as acceptance criteria, ADRs provide
  clear context for architectural boundaries, and over 35 concept documents
  explain every primitive following a strict 5-question depth bar.
* **Cohesive CLI Lifecycle**: The framework implements a clean lifecycle:
  `taf check` validates, `taf emit` generates, and `taf run` executes.
  Invoking `taf <model>` intelligently defaults to `dry-run`, printing a
  preflight report before any browser is opened.
* **Committed Generation**: Emitted suites under `generated/` are committed
  artifacts, making code generator modifications visible in diffs.

### Gaps in Self-Explanatoriness

1. **The "Dual DSL" Ambiguity**:
   The README introduces `tafbase` as "DSL First", where a system under test
   is declared once as data. A newcomer immediately encounters two distinct DSLs:
   * The **SUT Model DSL** (`*.sut.model.json`): Authored in JSON by QA and test
     engineers.
   * The **Framework-Spec DSL** (`taf/dsl/framework-spec.dsl`): An ANTLR4-based
     meta-DSL (`dsl/FrameworkSpec.g4`) that defines the framework vocabulary
     and code templates for Python and Java.
   Without an explicit distinction in `README.md`, readers may confuse whether
   they are meant to author `.dsl` files or `.json` files.

2. **File Layout Discrepancies**:
   * `dsl/FrameworkSpec.g4` remains at the root under `dsl/`, whereas
     `framework-spec.dsl` was moved into `taf/dsl/` so it could be distributed
     as Python package data (`pyproject.toml`).
   * An untracked `codegen-java/target/` directory remains on disk from an
     earlier branch (`feature/codegen-java`), confusing developers inspecting
     the filesystem.
   * An empty `tools/` directory exists at root with no README or purpose.

3. **Missing Java Toolchain Guidance**:
   `CONTRIBUTING.md` and `README.md` focus entirely on Python setup
   (`.venv`, `pip install -e .`, `playwright install`). Even though Java
   generation is a primary parity pillar, Java prerequisites (JDK 17+, Maven,
   Playwright driver cache) and commands to compile or run the Java suite
   (`mvn test`) are absent from the developer guide.

---

## In detail: missing information

1. **Formal JSON Schema (`schema.json`)**:
   Model files (`suts/*.sut.model.json`) lack a JSON Schema (Draft-07 or
   2020-12). Providing `$schema` in model files would allow IDEs (VS Code,
   IntelliJ) to provide instant autocomplete, field descriptions, and
   diagnostics for model authors.

2. **Comprehensive Step Language Reference**:
   While `SPEC-taf-v1-001-04-tafbase` lists step names, exact parameter
   specifications are scattered across `taf/model.py` and
   `taf/dsl/framework-spec.dsl`. Missing explicit details include:
   * `api`: Supported endpoint parameter interpolation (`{id}`), HTTP method
     handling, and status code assertions.
   * `save`: Dotted key JSONPath grammar (`$.field.subfield`) and its
     limitations.
   * `expect`: The full matrix of assertion properties (`hidden`, `text`,
     `count`, `equals`, `value`) and how `soft: true` affects execution flow.

3. **The `taf record` Guide**:
   `taf record` starts an interactive browser session and intercepts DOM
   interactions, drafting locator ladder mappings into JSON. This capability
   is completely omitted from `README.md` and `suts/README.md`. No guide
   explains how to review and merge recorded steps into a `.sut.model.json`.

4. **Pluggable Sink Interface Contract**:
   `PLAN-taf-v1-001-01` describes fault-reporting sinks as a pluggable kind.
   Currently, only `sink_ikc3.py` exists, hardcoded to IKC3's WebSocket protocol.
   There is no documented abstract sink interface or guidance for writing
   adapters for Jira, GitHub Issues, or standard JUnit XML / Allure reporting.

---

## In detail: problems and deficiencies in current implementation

### 1. Broken Import in Opt-In Live Tests

In `tests/test_live.py:74`:
```python
from taf import emit_java
```
`taf/__init__.py` does not export `emit_java`. During codegen modularization,
the implementation moved to `taf.codegen.java.emitter`. Running
`TAF_LIVE=1 pytest tests/test_live.py` fails immediately with:
```
ImportError: cannot import name 'emit_java' from 'taf'
```
The test passed during standard runs only because `test_live.py` is guarded by
`@pytest.mark.skipif(not os.environ.get("TAF_LIVE"))`.

### 2. Flawed Contract Test in `test_spec_contract.py`

In `tests/test_spec_contract.py`:
```python
used = set(re.findall(r'_refusal\(\s*\w+,\s*"([a-z-]+)"', open("taf/model.py").read()))
```
The regex expects the first argument to be a bare identifier (`\w+`). When the
first argument is a literal string (e.g. `_refusal("document", "not-json", ...)`)
or an expression (e.g. `_refusal("states.%s" % name, "unreachable", ...)`), the
regex silently ignores the call.

Consequently, three refusal reasons used in `taf/model.py` are completely
missing from the `contract { refusal ... }` block in `taf/dsl/framework-spec.dsl`:
* `not-json`
* `empty-model`
* `unreachable`

Fixing the regex immediately exposes this defect.

### 3. Java Codegen Generates Uncompilable Code

1. **`compare-screen` fails compilation in Java**:
   In `taf/dsl/framework-spec.dsl`:
   ```java
   assertThat(page).hasScreenshot();  // baseline: ${arg}.png
   ```
   Bytecode analysis of `com.microsoft.playwright.assertions.PageAssertions`
   proves that `hasScreenshot()` **does not exist** in Playwright Java.
   In Playwright, `hasScreenshot()` is an exclusive feature of the
   TypeScript and Python test runners. Generating Java code for any model
   containing a `compare-screen` step causes `javac` to fail with:
   `cannot find symbol: method hasScreenshot()`.

2. **`api` with `save` fails compilation in Java**:
   In `taf/dsl/framework-spec.dsl`:
   ```java
   saved.put("${save_key}", resp.json()${jsonpath});
   ```
   In Playwright Java, `APIResponse` provides `text()` and `body()`, but
   **no `json()` method**. Furthermore, the emitted `pom.xml` includes no JSON
   library (such as Jackson or Gson). Any model with an API step that saves a
   response property fails Java compilation.

### 4. Python vs. Java Parity Gaps

1. **`TAF_RERUN` is a no-op in Java**:
   In Python, `conftest.py` implements `pytest_collection_modifyitems` to
   filter tests according to `failed.txt`. In Java, `BaseTest.java` prints a
   message stating `(rerun: TAF_RERUN=1 mvn test)`, but does not implement a
   JUnit 5 `ExecutionCondition` or test filter. All tests are executed
   regardless of `TAF_RERUN`.

2. **No Fault-Reporting Sink in Java**:
   Python emits `ikc3_sink.py` and hooks into test failures to file fault
   reports over WebSocket. The Java generator emits no sink client or
   reporting hook in `BaseTest.java`.

### 5. Spec Contract Drift in `dryrun.py`

In `F-taf-v1-002-02-framework-model-acceptance.md`:
* **AC-7** requires `dryrun.py` to derive its environment table from
  `contract.env` in `framework-spec.dsl`. Instead, `_env_table()` hardcodes its
  row definitions.
* When `TAF_ARRIVE_MS` was added to `framework-spec.dsl` under `contract`, it
  was not added to `dryrun.py`. As a result, `taf dry-run` and `taf env` omit
  `TAF_ARRIVE_MS` entirely, and `taf run` lacks an `--arrive-ms` CLI option.
* **AC-8** requires `model.py` refusal names to import from the spec contract
  rather than using string literals.

### 6. Validation Deficiencies in `taf.model.validate`

1. **Unchecked Journey Final State**:
   If a journey executes actions ending at state $S_1$, but declares
   `expect-final: {"state": "S_2"}`, `validate()` accepts the model without
   refusal. The emitted test fails at runtime when asserting the unexpected marker.
2. **Contradictory Zero-Step Journeys**:
   A journey with `start: "A"`, `steps: []`, and `expect-final: {"state": "B"}`
   is accepted as valid despite lacking any transition between $A$ and $B$.
3. **Reachability False Positives on Inline Navigation**:
   State reachability checks (`visited` set) only account for `start`,
   `expect-final`, and named action transitions (`from`/`to`). Inline steps
   such as `{"navigate": "target"}` are ignored, causing valid target states
   to be rejected as `:unreachable`.
4. **Lack of Identifier Sanitization**:
   Model elements named after programming keywords (e.g., `"class"`, `"def"`)
   or numeric strings (e.g., `"123"`) pass validation. When emitted, they
   generate syntax errors in both Python (`def class(page):`) and Java
   (`public static Locator class(Page page)`).

---

## The decisions that are George's

The following prioritized roadmap outlines the corrective actions:

1. **Immediate Bug Fixes**:
   * Fix the import in `tests/test_live.py` (`taf.codegen.java.emitter`).
   * Fix the regex in `tests/test_spec_contract.py` and declare `not-json`,
     `empty-model`, and `unreachable` under `contract` in `taf/dsl/framework-spec.dsl`.
2. **Java Codegen Corrections**:
   * Replace `resp.json()` in Java API emission with an explicit JSON parser
     (add Jackson to `pom.xml` template), or adjust the specification.
   * Replace `assertThat(page).hasScreenshot()` in Java with a supported
     visual comparison pattern or document the limitation in `SPEC-04`.
   * Implement JUnit 5 test filtering for `TAF_RERUN` in `BaseTest.java`.
3. **Spec Alignment (AC-7 & AC-8)**:
   * Refactor `dryrun.py` to derive environment variable rows from
     `spec()["contract"]["env"]`, bringing `TAF_ARRIVE_MS` into dry-run reports
     and `taf env`.
   * Bind `_refusal` calls in `taf/model.py` to declared contract symbols.
4. **Validation Hardening**:
   * Enforce that the end state of a journey's step sequence matches its
     `expect-final` declaration.
   * Include inline `navigate` and `wait-for` states in reachability traversal.
   * Add identifier validation/sanitization to prevent invalid symbol generation.
5. **Documentation & Developer Ergonomics**:
   * Clarify the dual-DSL architecture in `README.md`.
   * Document Java prerequisites and test execution in `CONTRIBUTING.md`.
   * Generate and publish a JSON Schema for `*.sut.model.json`.

