---
id: SPEC-taf-v1-003-01-the-browser-workbench
status: draft
date: 2026-11-08
subproject: taf
authors:
  - George Petrov
  - Antigravity
---

# The browser workbench

## One line

`taf studio` attaches to a browser through Playwright to draft SUT model clauses, collect standalone reading highlights and archives, file fault reports, and watch the page for unexpected JavaScript actions.

## Lineage and standalone rule

- Extends [[ADR-taf-v1-001-01-tafbase-stands-alone]], [[SPEC-taf-v1-001-04-tafbase]], [[SPEC-taf-v1-002-01-the-framework-model]], and [[SPEC-taf-v1-002-02-the-framework-spec-dsl]].
- Uses `taf record` ([[CONCEPT-dsl-v1-001-01-the-sut-model]], [[CONCEPT-qa-v1-002-01-the-locator-ladder]], [[CONCEPT-playwright-v1-002-01-semantic-locators]]), `taf_journal` ([[CONCEPT-taf-v1-004-01-the-artifacts]], [[CONCEPT-taf-v1-006-01-the-subtitle-track]]), and `sink_ikc3` ([[CONCEPT-taf-v1-002-01-the-result-sink]]).
- **`tafbase` stands alone ([[ADR-taf-v1-001-01-tafbase-stands-alone]]):**
  - `tafbase` must work with no IKC3 present.
  - When IKC3 is not present, `taf studio` uses its own local dashboard tab and writes local files (`*.sut.model.json`, `results/`, and `TAF_LIBRARY_DIR` for highlights, trails, and archives).
  - When `TAF_IKC3_WS` is set, `taf studio` also sends `:support/file-report` to `/bus-ws` through `sink_ikc3`.

## Where DSL-First applies

1. **In `taf/dsl/framework-spec.dsl` and `*.sut.model.json`:**
   - The `security` clause, its modes (`shield`, `audit`, `raw`, `off`), its HUD options (`docked`, `toast-on-alert`, `detached`), the nine watched sinks, `TAF_SECURITY_MODE`, `TAF_WB_HUD`, `TAF_LIBRARY_DIR`, and the refusal `bad-security` are declared as data.
2. **In the runtime bridge (`taf/workbench.py`):**
   - The init script, overlay, and local dashboard are shared static assets beside the host.

## Three security rules from `PLAN-ikc-v3-086-01` and `PLAN-ikc-v3-086-02`

### 1. The page cannot call the binding (`§3.1`)

`expose_binding` puts a function on `window`. To stop calls from page scripts:
- The init script runs before any script of the page. It copies `window.__tafWorkbenchBridge` into a private closure variable and deletes `window.__tafWorkbenchBridge`.
- The host reads the page address from `source["page"].url` on the binding callback. It never trusts a URL passed inside the call arguments.

### 2. Never paint note text into the page DOM (`§3.2`, `Q13`)

A script of the page can read anything placed into the page DOM.
- When the user highlights text, the script wraps the text in `<mark>` only.
- It never writes the user's note into `mark.title` or into any DOM attribute.
- The note text goes only through the binding to the host journal (`journal.jsonl` and `journal.srt`) and to `highlights.json`.

### 3. Local fault record and stall queue (`§4.4`)

When the user files a fault report and `/bus-ws` is unset or does not answer, the host does not lose the report. It writes the report and all recorded steps to `results/unstalled-reports.json`.

## The three concurrent modes in `taf studio`

| mode | what the user does | what `tafbase` writes locally (and sends to `/bus-ws` if set) |
|---|---|---|
| **Mode 1: TAF model authoring** | Clicks, fills inputs, marks states, and files faults | Drafts `steps` and `elements` (`env:` secrets redacted), writes `results/unstalled-reports.json`, and sends `:support/file-report` if `TAF_IKC3_WS` is set |
| **Mode 2: Standalone web reader** | Browses pages, selects text to highlight, adds notes, and archives pages | Writes `highlights.json` (with mark-only repaint on revisit), `history-trails.jsonl`, and `archive/<date>-<slug>/article.md` under `TAF_LIBRARY_DIR` |
| **Mode 3: Page watchdog (`shield`, `audit`, `raw`)** | Browses with `shield` on by default, or switches to `audit` or `raw` | Blocks or logs third-party JavaScript access to sensitive sinks |

## The page watchdog (`shield`, `audit`, `raw`)

### Modes

1. **`shield` (default):** Blocks third-party reads of password inputs and cookies, blocks unapproved network egress, blocks unsolicited clipboard writes, and disables transparent clickjacking overlays.
2. **`audit`:** Blocks nothing. Records every watched sink call and stack frame into `journal.jsonl` for security tests.
3. **`raw`:** For pages authored by the user. Blocks nothing, and alerts when third-party JavaScript performs an unexpected action.

### Decisions

> [!decision] D1 decided 2026-11-08 George Petrov
> How should alerts work when `raw` mode is active on a page authored by the user?
> Recommendation: Provide a toggle between `detached` (zero DOM nodes added to the page) and `toast-on-alert` or `docked`.
> Answer: Option that toggles both.

> [!decision] D2 decided 2026-11-08 George Petrov
> Must third-party script attribution check bundle paths in the call stack as well as external origins?
> Recommendation: Yes. Check both external URL origins and path patterns such as `/node_modules/` and `/vendor/` in `Error.stack`.
> Answer: Yes.

### Watched sinks (`security.forbid-sinks`)

- `password-read`: third-party read of `HTMLInputElement.prototype.value` on a password or secret input.
- `global-keylogger`: third-party `addEventListener` for `keydown`, `keypress`, `keyup`, `input`, or `paste` on `window`, `document`, or `body`.
- `cookie-read`: third-party read or write of `document.cookie`.
- `storage-read`: third-party read of `localStorage` or `sessionStorage` keys that match `token`, `secret`, `auth`, `session`, `code`, or `key`.
- `unexpected-egress`: `fetch` or beacon to an origin outside `sut.base-url` and `security.allowed-origins`, or started by a third-party stack frame.
- `dynamic-eval`: third-party call to `eval` or `Function`.
- `clipboard-write`: call to `navigator.clipboard.writeText` without a first-party user click.
- `overlay-trap`: transparent (`opacity < 0.05`) high-`z-index` element over clickable controls.
- `phishing-marker`: page matches a declared `states.*.marker` on an untrusted origin.
