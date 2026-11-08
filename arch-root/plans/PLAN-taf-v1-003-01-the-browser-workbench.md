---
id: PLAN-taf-v1-003-01-the-browser-workbench
status: in-progress
date: 2026-11-08
subproject: taf
authors:
  - George Petrov
  - Antigravity
---

# PLAN-taf-v1-003-01 — the browser workbench: standalone TAF studio, reader, and page watchdog

Status: in progress

The contract: [[SPEC-taf-v1-003-01-the-browser-workbench]], extending [[ADR-taf-v1-001-01-tafbase-stands-alone]], [[SPEC-taf-v1-002-01-the-framework-model]], and [[SPEC-taf-v1-002-02-the-framework-spec-dsl]].

`tafbase` gains `taf studio` (and `taf record --workbench`). Per [[ADR-taf-v1-001-01-tafbase-stands-alone]], `tafbase` runs standalone with no IKC3 dependency:
- When IKC3 is not present, `taf studio` uses its own local dashboard tab and writes local files for all three modes:
  1. **TAF authoring mode:** `steps`, `elements`, state markers, `.srt` notes, and local fault reports (`results/unstalled-reports.json`).
  2. **Standalone web reader mode:** visit trails (`history-trails.jsonl`), W3C text-quote highlights (`highlights.json`) with mark-only repaint on revisit, and offline Markdown archives (`archive/<date>-<slug>/article.md`) under `TAF_LIBRARY_DIR`.
  3. **Page watchdog mode (`shield`, `audit`, `raw`):** default-on protection and third-party JavaScript alerts (`Error.stack` origin and `/node_modules/` attribution).
- When `TAF_IKC3_WS` is set, `taf studio` also sends `:support/file-report` to `/bus-ws` through `taf/sink_ikc3.py`.

> [!decision] D3 decided 2026-11-08 George Petrov
> Should `taf/dsl/framework-spec.dsl` declare the `security` contract while the JavaScript watchdog and overlay stay a shared asset?
> Recommendation: Yes. Declare `TAF_SECURITY_MODE`, `TAF_WB_HUD`, `TAF_LIBRARY_DIR`, and `refusal bad-security` in `framework-spec.dsl` and `taf/model.py`.
> Answer: Proceed with the DSL-First contract and the Python implementation.

## Release note (draft)

- New: `taf/dsl/framework-spec.dsl` and `taf/model.py` validate the `security` clause (`mode`, `hud`, `allowed-origins`, `third-party-patterns`, `forbid-sinks`) and refuse invalid declarations with `bad-security`.
  Accepted by: T-wb-001
- New: the init script (`taf/workbench.py`) deletes `window.__tafWorkbenchBridge` inside a private closure, reads the page address from `source.page`, classifies callers by origin and by `/node_modules/` or `/vendor/` paths, and watches nine security sinks.
  Accepted by: T-wb-002
- New: `raw` mode adds zero DOM nodes to the page when `hud` is `detached`, or shows a closed Shadow DOM toast on alert when `hud` is `toast-on-alert`.
  Accepted by: T-wb-003
- New: `taf studio` works standalone without IKC3: it records steps, saves highlights and offline article archives under `TAF_LIBRARY_DIR`, paints `<mark>` without exposing note text to the page DOM, and writes fault reports locally (or sends them to `/bus-ws` when configured).
  Accepted by: T-wb-004

## The pillars, tested

| Pillar | How this plan tests it |
|---|---|
| **`tafbase` stands alone** ([[ADR-taf-v1-001-01-tafbase-stands-alone]]) | All three modes (TAF authoring, Web Reader highlights and archiving, and Page Watchdog) work with local files and no IKC3 bus. |
| **Grammar and contract as data** ([[SPEC-taf-v1-002-01-the-framework-model]]) | `TAF_SECURITY_MODE`, `TAF_WB_HUD`, `TAF_LIBRARY_DIR`, and `refusal bad-security` live in `taf/dsl/framework-spec.dsl`. |
| **Bridge isolation and `source.page` address** ([[SPEC-taf-v1-003-01-the-browser-workbench]]) | Tests verify that `window.__tafWorkbenchBridge` is `undefined` to page scripts and that the host reads the page address from `source["page"].url`. |
| **Mark-only repaint (`Q13`)** | Tests verify that highlighting text with a note wraps the `<mark>` without putting the note text into `mark.title` or the page DOM. |

## The lanes

### ▶ Lane TAF/PLAN-taf-v1-003-01/A-1 — DSL contract and model validation for `security`

The contract: [[SPEC-taf-v1-003-01-the-browser-workbench]] and [[SPEC-taf-v1-002-02-the-framework-spec-dsl]].

Extend `taf/dsl/framework-spec.dsl` with `TAF_SECURITY_MODE`, `TAF_WB_HUD`, `TAF_LIBRARY_DIR`, and `refusal bad-security`. Extend `taf/model.py` to validate the optional `security` block in `*.sut.model.json`.

**Release note (draft)**

- New: `*.sut.model.json` accepts a `security` block; invalid values refuse with `bad-security`.
  Accepted by: T-wb-001

### ▶ Lane TAF/PLAN-taf-v1-003-01/B-2 — closure-isolated bridge and page watchdog (`shield`, `audit`, `raw`)

Implement in `taf/workbench.py`:
1. Private closure capture and deletion of `window.__tafWorkbenchBridge`.
2. Host address extraction from `source_info["page"].url` rather than the call payload.
3. Stack-frame classifier (`classify_caller_stack`) for cross-origin scripts and `/node_modules/` or `/vendor/` bundle paths.
4. Traps for the nine security sinks and the live toggle between `detached`, `toast-on-alert`, and `docked`.

**Release note (draft)**

- New: default-on `shield` watchdog and zero-DOM `raw` mode alert on unexpected third-party JavaScript actions.
  Accepted by: T-wb-002, T-wb-003

### ▶ Lane TAF/PLAN-taf-v1-003-01/C-3 — standalone `taf studio`, reader archiver, mark-only repaint, and fault queue

Implement in `taf/workbench.py` and `taf/__main__.py`:
1. Standalone Tab 1 Dashboard (`render_dashboard_html`) and `--library-dir` (`TAF_LIBRARY_DIR`) for highlights, visit trails, and offline Markdown archives (`article.md`).
2. Mark-only highlight and repaint (`<mark>` without `mark.title`, so the site never reads note text).
3. Mid-journey fault report recording into `results/unstalled-reports.json` (and optional `:support/file-report` dispatch via `taf/sink_ikc3.py` when `TAF_IKC3_WS` is set).
4. `connect_over_cdp` (`--cdp`) support for attaching to a normal Chrome profile.

**Release note (draft)**

- New: `taf studio` runs standalone without IKC3 for model authoring, web reading/archiving, and fault capture.
  Accepted by: T-wb-004

### ▶ Lane TAF/PLAN-taf-v1-003-01/D-4 — four-lane runtime bridge emission (`python`, `java`, `ts`, `js`)

Emit the host bridge and shared watchdog script into `taf-runtime` across Python, Java 21++, TypeScript, and JavaScript.
