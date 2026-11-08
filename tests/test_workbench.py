"""T-wb-* — tests for the Browser Workbench (SPEC-taf-v1-003-01, PLAN-taf-v1-003-01).

@spec SPEC-taf-v1-003-01-the-browser-workbench
@plan PLAN-taf-v1-003-01-the-browser-workbench
"""

import json
import os
import tempfile

from taf import journal_runtime, model, spec, workbench


def _base_model():
    return {
        "sut": {"name": "wb-sut", "base-url": "http://127.0.0.1:4856"},
        "states": {
            "login": {
                "route": "/login",
                "marker": {"text": "Secret Portal Sign In"},
            }
        },
        "elements": {
            "secret": {"css": "#secret-in"},
            "go": {"role": "button", "name": "Go"},
        },
        "journeys": {
            "smoke": {
                "start": "login",
                "steps": [],
                "expect-final": {"state": "login"},
            }
        },
    }


# ----------------------------------------------------------------------
# T-wb-001: DSL contract & model validation for `security`
# ----------------------------------------------------------------------

def test_dsl_contract_declares_workbench_env_and_refusal():
    contract = spec.spec()["contract"]
    for v in ("TAF_SECURITY_MODE", "TAF_WB_HUD", "TAF_LIBRARY_DIR"):
        assert v in contract["env"], f"missing {v} in framework-spec.dsl"
    assert "bad-security" in contract["refusals"]


def test_model_accepts_valid_security_clause():
    m = _base_model()
    m["security"] = {
        "mode": "raw",
        "hud": "detached",
        "allowed-origins": ["http://127.0.0.1:4856", "https://api.trusted.internal"],
        "third-party-patterns": ["/node_modules/", "/vendor/"],
        "forbid-sinks": ["password-read", "global-keylogger", "unexpected-egress"],
    }
    assert model.validate(m) == []


def test_model_refuses_bad_security_clauses():
    m = _base_model()
    m["security"] = {
        "mode": "invalid-mode",
        "hud": "invalid-hud",
        "forbid-sinks": ["not-a-sink"],
        "unknown-key": True,
    }
    refs = model.validate(m)
    reasons = {r["reason"] for r in refs}
    clauses = {r["clause"] for r in refs}
    assert "bad-security" in reasons
    assert "security.mode" in clauses
    assert "security.hud" in clauses
    assert "security.forbid-sinks" in clauses
    assert "security.unknown-key" in clauses


# ----------------------------------------------------------------------
# T-wb-002: Stack-frame origin, /node_modules/ attribution & source.page
# ----------------------------------------------------------------------

def test_classify_caller_stack_distinguishes_first_and_third_party():
    page_origin = "http://127.0.0.1:4856"
    s1 = "Error\n    at onClick (http://127.0.0.1:4856/static/app.js:42:11)"
    r1 = workbench.classify_caller_stack(s1, page_origin=page_origin)
    assert r1["third_party"] is False

    s2 = "Error\n    at steal (http://127.0.0.1:4856/node_modules/rogue-pkg/index.js:12:5)"
    r2 = workbench.classify_caller_stack(s2, page_origin=page_origin)
    assert r2["third_party"] is True
    assert "bundle-pattern:/node_modules/" in r2["reason"]

    s3 = "Error\n    at track (https://evil-cdn.example.org/tracker.js:1:99)"
    r3 = workbench.classify_caller_stack(s3, page_origin=page_origin)
    assert r3["third_party"] is True
    assert "cross-origin:https://evil-cdn.example.org" in r3["reason"]


def test_handle_event_reads_url_from_source_page_not_payload():
    """PLAN-ikc-v3-086-01 §3.1: never trust an address passed by a page script."""
    class _FakePage:
        url = "https://real-origin.example/page"

    with tempfile.TemporaryDirectory() as tmp:
        session = workbench.WorkbenchSession(m=_base_model(), library_dir=tmp)
        session.handle_event(
            {"page": _FakePage()},
            {"type": "mark-selection", "exact": "hello", "url": "https://spoofed.example/fake"},
        )
        assert session.marks[0]["url"] == "https://real-origin.example/page"
        assert session.highlights["https://real-origin.example/page"][0]["exact"] == "hello"


# ----------------------------------------------------------------------
# T-wb-003 & T-wb-004: Live BrowserContext verification
# ----------------------------------------------------------------------

def test_live_zero_trust_bridge_raw_mode_mark_only_and_stall_queue():
    from playwright.sync_api import sync_playwright

    m = _base_model()
    with tempfile.TemporaryDirectory() as tmp:
        lib_dir = os.path.join(tmp, "library")
        res_dir = os.path.join(tmp, "results")
        journal_runtime.begin(res_dir, "wb-session")
        try:
            session = workbench.WorkbenchSession(
                m=m,
                library_dir=lib_dir,
                results_dir=res_dir,
                mode_override="raw",
                hud_override="detached",
            )
            with sync_playwright() as p:
                browser = workbench.launch_browser(p, headless=True)
                ctx = browser.new_context()
                session.attach_to_context(ctx)
                page = ctx.new_page()
                html_doc = (
                    "<!DOCTYPE html><html><head><title>Authored Page</title></head>"
                    "<body>"
                    "<p id='article-p'>The quick brown fox jumps over the lazy dog.</p>"
                    "<input id='secret-in' type='password' value='top-secret-42' />"
                    "</body></html>"
                )
                page.goto("data:text/html," + html_doc)

                # 1. Closure isolation: window.__tafWorkbenchBridge is deleted
                assert page.evaluate("typeof window.__tafWorkbenchBridge") == "undefined"

                # 2. In `raw` + `detached` HUD mode, ZERO extra DOM elements exist
                assert page.evaluate("document.querySelectorAll('[data-taf-wb-shadow]').length") == 0

                # 3. First-party read of #secret-in causes no alert
                val_1p = page.evaluate("""
                (() => {
                  return document.getElementById('secret-in').value;
                })()
                //# sourceURL=http://127.0.0.1:4856/app/main.js
                """)
                assert val_1p == "top-secret-42"
                assert len(session.security_alerts) == 0

                # 4. Bundled 3rd-party (/node_modules/) read in RAW mode is unblocked
                #    and raises `password-read` and `global-keylogger` alerts
                val_3p_raw = page.evaluate("""
                (() => {
                  window.addEventListener('keydown', () => {});
                  return document.getElementById('secret-in').value;
                })()
                //# sourceURL=http://127.0.0.1:4856/node_modules/untrusted-widget/index.js
                """)
                assert val_3p_raw == "top-secret-42"
                sinks = [a["sink"] for a in session.security_alerts]
                assert "password-read" in sinks
                assert "global-keylogger" in sinks
                assert all(a["blocked"] is False for a in session.security_alerts)
                assert page.evaluate("document.querySelectorAll('[data-taf-wb-shadow]').length") == 0

                # 5. Toggle HUD to `docked` (D1) and mode to `shield`
                page.evaluate("""
                window.__tafWorkbenchControl.setHud('docked');
                window.__tafWorkbenchControl.setMode('shield');
                """)
                assert page.evaluate("document.querySelectorAll('[data-taf-wb-shadow]').length") == 1
                assert session.sec_cfg["mode"] == "shield"
                assert session.sec_cfg["hud"] == "docked"

                # 6. In `shield` mode, 3rd-party read of #secret-in is blocked (returns "")
                val_3p_shield = page.evaluate("""
                (() => {
                  return document.getElementById('secret-in').value;
                })()
                //# sourceURL=http://127.0.0.1:4856/node_modules/untrusted-widget/index.js
                """)
                assert val_3p_shield == ""
                assert session.security_alerts[-1]["sink"] == "password-read"
                assert session.security_alerts[-1]["blocked"] is True

                # 7. Q13: Mark selection with a private note -> `<mark>` is painted,
                #    but `mark.title` is empty so the page DOM never sees the note text!
                mk = page.evaluate("""
                (() => {
                  const p = document.getElementById('article-p');
                  const range = document.createRange();
                  range.selectNodeContents(p);
                  const sel = window.getSelection();
                  sel.removeAllRanges();
                  sel.addRange(range);
                  return window.__tafWorkbenchControl.markSelection('Private note for journal only');
                })()
                """)
                assert mk["exact"] == "The quick brown fox jumps over the lazy dog."
                assert page.evaluate("document.querySelectorAll('mark[data-taf-wb-highlight]').length") == 1
                assert page.evaluate("document.querySelector('mark[data-taf-wb-highlight]').title") == ""
                assert "Private note for journal only" not in page.evaluate("document.documentElement.outerHTML")
                assert session.marks[0]["note"] == "Private note for journal only"
                assert session.highlights[page.url][0]["note"] == "Private note for journal only"
                assert os.path.isfile(os.path.join(lib_dir, "highlights.json"))

                # 8. Standalone article archiving and highlight re-hydration (works without IKC3)
                md_path = session.archive_article(
                    url=page.url,
                    title="Authored Page",
                    text="The quick brown fox jumps over the lazy dog.",
                    html=html_doc,
                )
                assert os.path.isfile(md_path)
                assert os.path.isfile(os.path.join(os.path.dirname(md_path), "snapshot.html"))

                # Revisit page and re-hydrate saved highlights without exposing note text in DOM
                page.goto("data:text/html," + html_doc)
                page.evaluate("window.__tafWorkbenchControl.setHud('docked')")
                rehydrated_count = page.evaluate(
                    "(items) => window.__tafWorkbenchControl.rehydrateHighlights(items)",
                    session.highlights[page.url],
                )
                assert rehydrated_count == 1
                assert page.evaluate("document.querySelector('mark[data-taf-wb-highlight]').title") == ""

                # 9. Record a click and file a fault report locally (§4.4 stall queue)
                page.click("#article-p")
                repro = session.file_exploratory_fault(
                    what="Fox jumped too high", url=page.url
                )
                assert repro["stalled"] is True
                assert len(repro["steps_so_far"]) >= 1
                stall_file = os.path.join(res_dir, "unstalled-reports.json")
                assert os.path.isfile(stall_file)
                stalled_items = json.load(open(stall_file, encoding="utf-8"))
                assert len(stalled_items) == 1
                assert stalled_items[0]["what"] == "Fox jumped too high"

                browser.close()
        finally:
            journal_runtime.end("passed")
