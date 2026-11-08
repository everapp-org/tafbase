"""taf.workbench — standalone browser workbench: TAF Studio, Web Reader, and Page Watchdog.

@spec SPEC-taf-v1-003-01-the-browser-workbench
@plan PLAN-taf-v1-003-01-the-browser-workbench
@adr ADR-taf-v1-001-01-tafbase-stands-alone
@concept CONCEPT-dsl-v1-001-01-the-sut-model
@concept CONCEPT-qa-v1-002-01-the-locator-ladder
@concept CONCEPT-taf-v1-002-01-the-result-sink
@concept CONCEPT-taf-v1-004-01-the-artifacts

Runs standalone with no IKC3 dependency (ADR-taf-v1-001-01), while incorporating
the security and Playwright rules from PLAN-ikc-v3-086-01 and PLAN-ikc-v3-086-02:
1. Deletes `window.__tafWorkbenchBridge` inside a private closure and reads the page
   address from `source.page`, never from the payload (§3.1).
2. Paints `<mark>` only on the page and never writes note text into `mark.title` (§3.2, Q13).
3. Saves highlights, visit trails, and offline Markdown archives locally under `TAF_LIBRARY_DIR`.
4. Writes fault reports to `results/unstalled-reports.json` when standalone or when `/bus-ws`
   does not answer (§4.4), and sends `:support/file-report` when `TAF_IKC3_WS` is set.
"""

import json
import os
import re
import shutil
import time
import urllib.parse

from taf import journal_runtime, model, record, sink_ikc3

DEFAULT_THIRD_PARTY_PATTERNS = (
    "/node_modules/",
    "/vendor/",
    "/bower_components/",
    "webpack://",
    "vite://",
    "unpkg.com",
    "jsdelivr.net",
    "cdnjs.cloudflare.com",
)


def launch_browser(playwright_instance, headless=False, **kwargs):
    """Launch Chromium, or fall back to system Chrome when Playwright cache is absent."""
    try:
        return playwright_instance.chromium.launch(headless=headless, **kwargs)
    except Exception:
        for bin_name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
            exe = shutil.which(bin_name)
            if exe:
                return playwright_instance.chromium.launch(
                    executable_path=exe, headless=headless, **kwargs
                )
        raise


def resolve_security_config(m=None, env=None, mode_override=None, hud_override=None):
    """Resolve effective security posture and HUD mode: flag > env > model > default."""
    env = os.environ if env is None else env
    m = m or {}
    sec = m.get("security") or {}
    base_url = (m.get("sut") or {}).get("base-url") or ""
    parsed_base = urllib.parse.urlparse(base_url)
    base_origin = (f"{parsed_base.scheme}://{parsed_base.netloc}"
                   if parsed_base.scheme and parsed_base.netloc else "")

    mode = (mode_override
            or env.get("TAF_SECURITY_MODE")
            or sec.get("mode")
            or "shield")
    if mode not in model.SECURITY_MODES:
        mode = "shield"

    default_hud = "toast-on-alert" if mode == "raw" else "docked"
    hud = (hud_override
           or env.get("TAF_WB_HUD")
           or sec.get("hud")
           or default_hud)
    if hud not in model.SECURITY_HUDS:
        hud = default_hud

    allowed = list(sec.get("allowed-origins") or [])
    if base_origin and base_origin not in allowed:
        allowed.insert(0, base_origin)

    patterns = list(DEFAULT_THIRD_PARTY_PATTERNS)
    for p in sec.get("third-party-patterns") or []:
        if p not in patterns:
            patterns.append(p)

    sinks = list(sec.get("forbid-sinks") or model.SECURITY_SINKS)
    return {
        "mode": mode,
        "hud": hud,
        "base-origin": base_origin,
        "allowed-origins": allowed,
        "third-party-patterns": patterns,
        "forbid-sinks": sinks,
    }


def classify_caller_stack(stack_text, page_origin="", allowed_origins=(),
                          third_party_patterns=DEFAULT_THIRD_PARTY_PATTERNS):
    """Check `Error.stack` for external URL origins and `/node_modules/` or `/vendor/` paths."""
    if not stack_text:
        return {"third_party": False, "reason": "empty-stack", "frame": ""}
    allowed = set(allowed_origins or ())
    if page_origin:
        allowed.add(page_origin)

    for raw_line in str(stack_text).splitlines():
        line = raw_line.strip()
        if not line or "__tafWorkbench" in line:
            continue
        for pat in third_party_patterns:
            if pat and pat in line:
                return {
                    "third_party": True,
                    "reason": f"bundle-pattern:{pat}",
                    "frame": line,
                }
        for m in re.finditer(r"https?://[^\s)]+", line):
            url = re.sub(r"(:\d+)+$", "", m.group(0))
            u = urllib.parse.urlparse(url)
            origin = f"{u.scheme}://{u.netloc}" if u.scheme and u.netloc else ""
            if origin and page_origin and origin != page_origin and origin not in allowed:
                return {
                    "third_party": True,
                    "reason": f"cross-origin:{origin}",
                    "frame": line,
                }
    return {"third_party": False, "reason": "first-party", "frame": ""}


def build_init_script(sec_cfg, states=None, secret_locators=None, saved_highlights=None):
    """Build the init script injected via `context.add_init_script()`.

    1. Captures and deletes `window.__tafWorkbenchBridge` inside a private closure (§3.1).
    2. Traps the nine watched sinks with stack-frame origin and bundle-path attribution.
    3. Toggles between `detached` (zero DOM nodes), `toast-on-alert`, and `docked` (D1).
    4. Paints `<mark>` only when highlighting text, never placing note text into the DOM (Q13).
    """
    cfg_json = json.dumps({
        "security": sec_cfg,
        "states": states or {},
        "secrets": secret_locators or {},
        "highlights": saved_highlights or {},
    })
    return f"""
(() => {{
  const bridge = window.__tafWorkbenchBridge;
  try {{
    delete window.__tafWorkbenchBridge;
  }} catch (_e) {{
    window.__tafWorkbenchBridge = undefined;
  }}

  const CFG = {cfg_json};
  let secMode = CFG.security.mode || "shield";
  let hudMode = CFG.security.hud || (secMode === "raw" ? "toast-on-alert" : "docked");
  const patterns = CFG.security["third-party-patterns"] || [];
  const allowedOrigins = new Set(CFG.security["allowed-origins"] || []);
  const forbidSinks = new Set(CFG.security["forbid-sinks"] || []);

  const alerts = [];
  let shadowRoot = null;
  let hostEl = null;
  let toastContainer = null;
  let dockBar = null;
  let trustedUserGestureUntil = 0;

  const emit = (payload) => {{
    if (typeof bridge === "function") {{
      try {{ bridge(payload); }} catch (_e) {{}}
    }}
  }};

  const ladder = (el) => {{
    if (!el || !el.closest) return ["css", "body"];
    const idOf = (v) => v && /^[A-Za-z][\\w\\-]*$/.test(v) ? "#" + v : '[id="' + v + '"]';
    const testid = el.closest("[data-testid],[data-test-id],[data-qa]");
    if (testid) return ["testid", testid.getAttribute("data-testid")
                       || testid.getAttribute("data-test-id")
                       || testid.getAttribute("data-qa")];
    if (el.id) return ["css", idOf(el.id)];
    const di = el.closest("[data-import-id]");
    if (di) return ["css", '[data-import-id="' + di.getAttribute("data-import-id") + '"]'];
    const lab = el.labels && el.labels[0];
    if (lab) return ["label", lab.textContent.trim()];
    const roleMap = {{BUTTON: "button", A: "link", TEXTAREA: "textbox", SELECT: "combobox"}};
    const tag = el.tagName;
    let role = roleMap[tag];
    if (tag === "INPUT") {{
      role = {{text: "textbox", password: "textbox", checkbox: "checkbox",
              radio: "radio"}}[el.type] || "textbox";
    }}
    if (role) {{
      const name = el.getAttribute("aria-label")
          || (tag === "INPUT" && el.placeholder) || el.innerText || el.title
          || el.name || "";
      if (name.trim()) return ["role", role, name.trim().slice(0, 60)];
    }}
    return ["css", (tag || "body").toLowerCase()];
  }};

  const classifyStack = (stack) => {{
    if (!stack) return {{ thirdParty: false, reason: "empty-stack", frame: "" }};
    const pageOrigin = location.origin;
    const lines = String(stack).split("\\n");
    for (const raw of lines) {{
      const line = raw.trim();
      if (!line || line.includes("__tafWorkbench")) continue;
      for (const pat of patterns) {{
        if (pat && line.includes(pat)) {{
          return {{ thirdParty: true, reason: "bundle-pattern:" + pat, frame: line }};
        }}
      }}
      const m = line.match(/https?:\\/\\/[^\\s)]+/g);
      if (m) {{
        for (const rawUrl of m) {{
          try {{
            const u = rawUrl.replace(/(:\\d+)+$/, "");
            const o = new URL(u).origin;
            if (o && pageOrigin && pageOrigin !== "null" && o !== pageOrigin && !allowedOrigins.has(o)) {{
              return {{ thirdParty: true, reason: "cross-origin:" + o, frame: line }};
            }}
          }} catch (_e) {{}}
        }}
      }}
    }}
    return {{ thirdParty: false, reason: "first-party", frame: "" }};
  }};

  const ensureShadowHost = () => {{
    if (hudMode === "detached") return null;
    if (shadowRoot && hostEl && hostEl.isConnected) return shadowRoot;
    const rootTarget = document.documentElement || document.body;
    if (!rootTarget) return null;
    hostEl = document.createElement("div");
    hostEl.setAttribute("data-taf-wb-shadow", "1");
    hostEl.style.cssText = "all:initial;position:fixed;z-index:2147483647;bottom:12px;right:12px;pointer-events:none;";
    shadowRoot = hostEl.attachShadow({{ mode: "closed" }});
    const style = document.createElement("style");
    style.textContent = `
      .wb-box {{ font-family: system-ui, sans-serif; font-size: 12px; color: #f8fafc; pointer-events: auto; }}
      .wb-dock {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 6px 10px;
                  display: flex; gap: 6px; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.4); }}
      .wb-btn {{ background: #1e293b; color: #e2e8f0; border: 1px solid #475569; border-radius: 4px;
                 padding: 3px 7px; cursor: pointer; font-size: 11px; }}
      .wb-btn:hover {{ background: #334155; }}
      .wb-badge {{ padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 10px; text-transform: uppercase; }}
      .wb-shield {{ background: #065f46; color: #a7f3d0; }}
      .wb-audit {{ background: #1e40af; color: #bfdbfe; }}
      .wb-raw {{ background: #92400e; color: #fde68a; }}
      .wb-toast {{ background: #7f1d1d; border: 1px solid #ef4444; color: #fef2f2; border-radius: 6px;
                   padding: 8px 10px; margin-bottom: 6px; max-width: 360px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }}
    `;
    shadowRoot.appendChild(style);
    toastContainer = document.createElement("div");
    toastContainer.className = "wb-box";
    shadowRoot.appendChild(toastContainer);

    if (hudMode === "docked") {{
      renderDock();
    }}
    rootTarget.appendChild(hostEl);
    return shadowRoot;
  }};

  const renderDock = () => {{
    if (!shadowRoot) return;
    if (dockBar) dockBar.remove();
    if (hudMode !== "docked") return;
    dockBar = document.createElement("div");
    dockBar.className = "wb-box wb-dock";
    const badgeClass = secMode === "shield" ? "wb-shield" : (secMode === "audit" ? "wb-audit" : "wb-raw");
    dockBar.innerHTML = `
      <span class="wb-badge ${{badgeClass}}" id="wb-mode-btn" title="Cycle watchdog mode">${{secMode}}</span>
      <button class="wb-btn" id="wb-hud-btn" title="Toggle HUD display">HUD: ${{hudMode}}</button>
      <button class="wb-btn" id="wb-hl-btn" title="Highlight selected text">Highlight</button>
      <button class="wb-btn" id="wb-note-btn" title="Add session note">Note</button>
      <button class="wb-btn" id="wb-arch-btn" title="Archive page offline">Archive</button>
      <button class="wb-btn" id="wb-fault-btn" style="border-color:#ef4444;color:#fca5a5;" title="File fault report">Fault</button>
    `;
    dockBar.querySelector("#wb-mode-btn").onclick = (e) => {{
      e.stopPropagation();
      const order = ["shield", "audit", "raw"];
      secMode = order[(order.indexOf(secMode) + 1) % order.length];
      emit({{ type: "config-change", mode: secMode, hud: hudMode }});
      renderDock();
    }};
    dockBar.querySelector("#wb-hud-btn").onclick = (e) => {{
      e.stopPropagation();
      const order = ["docked", "toast-on-alert", "detached"];
      setHudMode(order[(order.indexOf(hudMode) + 1) % order.length]);
    }};
    dockBar.querySelector("#wb-hl-btn").onclick = (e) => {{
      e.stopPropagation();
      captureHighlight("");
    }};
    dockBar.querySelector("#wb-note-btn").onclick = (e) => {{
      e.stopPropagation();
      const sel = (window.getSelection && window.getSelection().toString().trim()) || "";
      emit({{ type: "note", text: sel || ("Note on " + location.pathname) }});
    }};
    dockBar.querySelector("#wb-arch-btn").onclick = (e) => {{
      e.stopPropagation();
      emit({{ type: "archive-request", title: document.title, text: document.body ? document.body.innerText : "" }});
    }};
    dockBar.querySelector("#wb-fault-btn").onclick = (e) => {{
      e.stopPropagation();
      const sel = (window.getSelection && window.getSelection().toString().trim()) || "";
      emit({{
        type: "fault-report",
        what: sel || ("Fault observed on " + location.pathname),
        dom: document.documentElement ? document.documentElement.outerHTML.slice(0, 20000) : ""
      }});
    }};
    shadowRoot.appendChild(dockBar);
  }};

  const setHudMode = (nextHud) => {{
    hudMode = nextHud;
    emit({{ type: "config-change", mode: secMode, hud: hudMode }});
    if (hudMode === "detached") {{
      if (hostEl && hostEl.isConnected) hostEl.remove();
      hostEl = null;
      shadowRoot = null;
      toastContainer = null;
      dockBar = null;
    }} else {{
      ensureShadowHost();
      if (hudMode === "toast-on-alert" && dockBar) {{
        dockBar.remove();
        dockBar = null;
      }} else if (hudMode === "docked") {{
        renderDock();
      }}
    }}
  }};

  const raiseSecurityAlert = (sink, detail, callerInfo, blocked) => {{
    if (secMode === "off" || !forbidSinks.has(sink)) return;
    const alertObj = {{
      type: "security-alert",
      sink: sink,
      mode: secMode,
      hud: hudMode,
      blocked: Boolean(blocked),
      detail: detail,
      reason: callerInfo.reason,
      frame: callerInfo.frame,
      ts: Date.now()
    }};
    alerts.push(alertObj);
    emit(alertObj);

    if (hudMode === "detached") {{
      const origTitle = document.title;
      if (!origTitle.startsWith("[!ALERT] ")) {{
        document.title = "[!ALERT] " + origTitle;
        setTimeout(() => {{
          if (document.title.startsWith("[!ALERT] ")) document.title = origTitle;
        }}, 1500);
      }}
      return;
    }}

    const root = ensureShadowHost();
    if (root && toastContainer) {{
      const t = document.createElement("div");
      t.className = "wb-toast";
      t.innerHTML = `<strong>[${{secMode.toUpperCase()}}${{blocked ? " BLOCKED" : " ALERT"}}] ${{sink}}</strong><br/>`
        + `${{detail}}<br/><small style="opacity:0.85">${{callerInfo.reason}}</small>`;
      toastContainer.appendChild(t);
      setTimeout(() => {{ if (t.isConnected) t.remove(); }}, 6000);
    }}
  }};

  // 1. password-read trap
  const inputProto = window.HTMLInputElement && window.HTMLInputElement.prototype;
  const valDesc = inputProto && Object.getOwnPropertyDescriptor(inputProto, "value");
  if (valDesc && valDesc.get) {{
    Object.defineProperty(inputProto, "value", {{
      configurable: true,
      enumerable: valDesc.enumerable,
      get: function() {{
        const isSecret = this.type === "password"
          || (this.name && /pass|secret|token|code/i.test(this.name))
          || (this.id && /pass|secret|token|code/i.test(this.id));
        if (isSecret) {{
          const caller = classifyStack(new Error().stack);
          if (caller.thirdParty) {{
            const shouldBlock = (secMode === "shield");
            raiseSecurityAlert("password-read", "3rd-party read of #" + (this.id || this.name || "password"), caller, shouldBlock);
            if (shouldBlock) return "";
          }}
        }}
        return valDesc.get.call(this);
      }},
      set: function(v) {{
        return valDesc.set.call(this, v);
      }}
    }});
  }}

  // 2. global-keylogger trap
  const origAddEv = EventTarget.prototype.addEventListener;
  EventTarget.prototype.addEventListener = function(type, listener, options) {{
    if (["keydown", "keypress", "keyup", "input", "paste"].includes(String(type))) {{
      const isGlobal = (this === window || this === document || this === document.body || this === document.documentElement);
      if (isGlobal) {{
        const caller = classifyStack(new Error().stack);
        if (caller.thirdParty) {{
          const shouldBlock = (secMode === "shield");
          raiseSecurityAlert("global-keylogger", "3rd-party global listener on " + type, caller, shouldBlock);
          if (shouldBlock) return;
        }}
      }}
    }}
    return origAddEv.call(this, type, listener, options);
  }};

  // 3. cookie-read trap
  const docProto = window.Document && window.Document.prototype;
  const cookieDesc = (docProto && Object.getOwnPropertyDescriptor(docProto, "cookie"))
    || Object.getOwnPropertyDescriptor(HTMLDocument.prototype, "cookie");
  if (cookieDesc && cookieDesc.get) {{
    Object.defineProperty(Document.prototype, "cookie", {{
      configurable: true,
      enumerable: cookieDesc.enumerable,
      get: function() {{
        const caller = classifyStack(new Error().stack);
        if (caller.thirdParty) {{
          const shouldBlock = (secMode === "shield");
          raiseSecurityAlert("cookie-read", "3rd-party access to document.cookie", caller, shouldBlock);
          if (shouldBlock) return "";
        }}
        return cookieDesc.get.call(this);
      }},
      set: function(v) {{
        const caller = classifyStack(new Error().stack);
        if (caller.thirdParty) {{
          const shouldBlock = (secMode === "shield");
          raiseSecurityAlert("cookie-read", "3rd-party write to document.cookie", caller, shouldBlock);
          if (shouldBlock) return;
        }}
        return cookieDesc.set.call(this, v);
      }}
    }});
  }}

  // 4. storage-read trap
  if (window.Storage && window.Storage.prototype) {{
    const origGetItem = Storage.prototype.getItem;
    Storage.prototype.getItem = function(key) {{
      if (/token|secret|auth|session|code|pass|key/i.test(String(key))) {{
        const caller = classifyStack(new Error().stack);
        if (caller.thirdParty) {{
          const shouldBlock = (secMode === "shield");
          raiseSecurityAlert("storage-read", "3rd-party storage read of '" + key + "'", caller, shouldBlock);
          if (shouldBlock) return null;
        }}
      }}
      return origGetItem.call(this, key);
    }};
  }}

  // 5. unexpected-egress trap
  if (typeof window.fetch === "function") {{
    const origFetch = window.fetch;
    window.fetch = function(input, init) {{
      const urlStr = typeof input === "string" ? input : (input && input.url) || "";
      const caller = classifyStack(new Error().stack);
      let untrustedDest = false;
      let destOrigin = "";
      try {{
        const u = new URL(urlStr, location.href);
        destOrigin = u.origin;
        if (location.origin !== "null" && destOrigin !== location.origin && !allowedOrigins.has(destOrigin)) {{
          untrustedDest = true;
        }}
      }} catch (_e) {{}}
      if (untrustedDest || caller.thirdParty) {{
        const reason = untrustedDest
          ? {{ thirdParty: true, reason: "egress-origin:" + destOrigin, frame: caller.frame || urlStr }}
          : caller;
        const shouldBlock = (secMode === "shield" && untrustedDest);
        raiseSecurityAlert("unexpected-egress", "fetch to " + urlStr, reason, shouldBlock);
        if (shouldBlock) return Promise.reject(new Error("Blocked by TAF Workbench Shield"));
      }}
      return origFetch.apply(this, arguments);
    }};
  }}

  // 6. clipboard-write trap
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {{
    const origClipWrite = navigator.clipboard.writeText.bind(navigator.clipboard);
    navigator.clipboard.writeText = function(text) {{
      const caller = classifyStack(new Error().stack);
      const noUserGesture = Date.now() > trustedUserGestureUntil;
      if (caller.thirdParty || noUserGesture) {{
        const info = caller.thirdParty ? caller : {{ thirdParty: true, reason: "no-user-gesture", frame: String(text).slice(0, 60) }};
        const shouldBlock = (secMode === "shield");
        raiseSecurityAlert("clipboard-write", "Unsolicited clipboard write", info, shouldBlock);
        if (shouldBlock) return Promise.reject(new Error("Blocked by TAF Workbench Shield"));
      }}
      return origClipWrite(text);
    }};
  }}

  // 7 & 8. overlay-trap & phishing-marker check
  const scanDomSecurity = () => {{
    if (!document.body) return;
    const els = document.body.querySelectorAll("iframe, div, a");
    for (const el of els) {{
      if (el === hostEl) continue;
      const st = window.getComputedStyle(el);
      const z = parseInt(st.zIndex, 10);
      const op = parseFloat(st.opacity);
      if (!isNaN(z) && z >= 1000 && !isNaN(op) && op < 0.05 && st.pointerEvents !== "none") {{
        const rect = el.getBoundingClientRect();
        if (rect.width >= 100 && rect.height >= 40) {{
          const shouldBlock = (secMode === "shield");
          raiseSecurityAlert(
            "overlay-trap",
            "Transparent high-z-index overlay (" + el.tagName.toLowerCase() + ")",
            {{ thirdParty: true, reason: "invisible-overlay", frame: el.outerHTML.slice(0, 120) }},
            shouldBlock
          );
          if (shouldBlock) el.style.pointerEvents = "none";
        }}
      }}
    }}
    const baseOrigin = CFG.security["base-origin"];
    if (baseOrigin && location.origin !== "null" && location.origin !== baseOrigin && !allowedOrigins.has(location.origin)) {{
      for (const [stName, stDef] of Object.entries(CFG.states || {{}})) {{
        const marker = (stDef && stDef.marker) || {{}};
        let matched = false;
        if (marker.text && document.body.innerText && document.body.innerText.includes(marker.text)) {{
          matched = true;
        }} else if (marker.css && document.querySelector(marker.css)) {{
          matched = true;
        }}
        if (matched) {{
          raiseSecurityAlert(
            "phishing-marker",
            "Untrusted origin " + location.origin + " matches state marker '" + stName + "'",
            {{ thirdParty: true, reason: "untrusted-origin:" + location.origin, frame: location.href }},
            false
          );
        }}
      }}
    }}
  }};

  // Mark-only selection highlight (PLAN-ikc-v3-086-01 §3.2 & Q13: never put noteText in DOM)
  const captureHighlight = (noteText) => {{
    const sel = window.getSelection && window.getSelection();
    if (!sel || sel.isCollapsed) return null;
    const exact = sel.toString().trim();
    if (!exact) return null;
    const anchorNode = sel.anchorNode && (sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement);
    const loc = ladder(anchorNode);
    const fullText = (anchorNode && anchorNode.textContent) || "";
    const idx = fullText.indexOf(exact);
    const prefix = idx > 0 ? fullText.slice(Math.max(0, idx - 24), idx) : "";
    const suffix = idx >= 0 ? fullText.slice(idx + exact.length, idx + exact.length + 24) : "";
    const hl = {{
      type: "highlight",
      exact: exact,
      prefix: prefix,
      suffix: suffix,
      loc: loc,
      note: noteText || "",
      ts: Date.now()
    }};
    emit(hl);
    if (hudMode !== "detached" && anchorNode) {{
      try {{
        const range = sel.getRangeAt(0);
        const mark = document.createElement("mark");
        mark.setAttribute("data-taf-wb-highlight", "1");
        mark.style.cssText = "background:#fde047;color:#0f172a;padding:0 2px;border-radius:2px;";
        // Q13: Paint the mark only. Never set mark.title = noteText in the page DOM.
        range.surroundContents(mark);
      }} catch (_e) {{}}
    }}
    return hl;
  }};

  const rehydrateHighlights = (customItems) => {{
    if (hudMode === "detached" || !document.body) return 0;
    const list = Array.isArray(customItems)
      ? customItems
      : ((CFG.highlights && CFG.highlights[location.href]) || []);
    if (!list.length) return 0;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    let n;
    while ((n = walker.nextNode())) textNodes.push(n);
    let count = 0;
    for (const h of list) {{
      if (!h.exact) continue;
      for (const tn of textNodes) {{
        const i = tn.nodeValue.indexOf(h.exact);
        if (i >= 0 && tn.parentElement && !tn.parentElement.hasAttribute("data-taf-wb-highlight")) {{
          try {{
            const range = document.createRange();
            range.setStart(tn, i);
            range.setEnd(tn, i + h.exact.length);
            const mark = document.createElement("mark");
            mark.setAttribute("data-taf-wb-highlight", "1");
            mark.style.cssText = "background:#fde047;color:#0f172a;padding:0 2px;border-radius:2px;";
            // Q13: Paint the mark only. Never write h.note into mark.title.
            range.surroundContents(mark);
            count += 1;
            break;
          }} catch (_e) {{}}
        }}
      }}
    }}
    return count;
  }};

  origAddEv.call(window, "click", (e) => {{
    trustedUserGestureUntil = Date.now() + 1000;
    if (hostEl && (e.target === hostEl || hostEl.contains(e.target))) return;
    const a = e.target && e.target.closest && e.target.closest("a[href]");
    emit({{
      type: "click",
      loc: ladder(e.target),
      href: a ? a.href : "",
      anchorText: a ? (a.innerText || "").trim().slice(0, 80) : ""
    }});
  }}, true);

  origAddEv.call(window, "change", (e) => {{
    if (hostEl && (e.target === hostEl || hostEl.contains(e.target))) return;
    const pw = e.target.type === "password";
    emit({{
      type: "fill",
      loc: ladder(e.target),
      pw: pw,
      value: pw ? "" : e.target.value
    }});
  }}, true);

  origAddEv.call(window, "DOMContentLoaded", () => {{
    if (hudMode === "docked") ensureShadowHost();
    rehydrateHighlights();
    scanDomSecurity();
    emit({{
      type: "visit",
      referrer: document.referrer || "",
      title: document.title || ""
    }});
  }});

  Object.defineProperty(window, "__tafWorkbenchControl", {{
    configurable: false,
    enumerable: false,
    writable: false,
    value: Object.freeze({{
      getMode: () => secMode,
      getHud: () => hudMode,
      setHud: (m) => setHudMode(m),
      setMode: (m) => {{ secMode = m; emit({{ type: "config-change", mode: secMode, hud: hudMode }}); renderDock(); }},
      highlightSelection: (note) => captureHighlight(note || ""),
      markSelection: (note) => captureHighlight(note || ""),
      rehydrateHighlights: (items) => rehydrateHighlights(items),
      scanSecurity: () => scanDomSecurity(),
      getAlerts: () => alerts.slice()
    }})
  }});
}})();
"""


def render_dashboard_html(sut_name, sec_cfg, states=None):
    """Render the standalone Tab 1 Workbench Dashboard HTML when running without IKC3."""
    states = states or {}
    state_nodes = []
    for i, name in enumerate(states):
        x = 80 + (i % 4) * 160
        y = 60 + (i // 4) * 90
        state_nodes.append(
            f'<g transform="translate({x},{y})">'
            f'<rect x="-55" y="-22" width="110" height="44" rx="8" fill="#1e293b" stroke="#38bdf8" stroke-width="2"/>'
            f'<text text-anchor="middle" dy="5" fill="#f8fafc" font-size="12" font-family="system-ui">{name}</text>'
            f'</g>'
        )
    svg_content = "".join(state_nodes) or (
        '<text x="20" y="40" fill="#94a3b8" font-size="13">No states declared yet</text>'
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>TAF Workbench — {sut_name}</title>
<style>
  body {{ margin: 0; background: #0f172a; color: #f8fafc; font-family: system-ui, sans-serif; }}
  header {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 20px;
            background: #1e293b; border-bottom: 1px solid #334155; }}
  .badge {{ padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; text-transform: uppercase; background: #065f46; color: #a7f3d0; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 16px; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px; }}
  h2 {{ margin: 0 0 10px 0; font-size: 14px; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em; }}
  ul {{ margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.6; }}
</style>
</head>
<body>
<header>
  <div><strong>TAF Standalone Workbench</strong> — <span>{sut_name}</span></div>
  <div>
    <span class="badge" id="dash-mode">Security: {sec_cfg["mode"]}</span>
    <span class="badge" id="dash-hud" style="background:#334155;color:#e2e8f0;margin-left:8px;">HUD: {sec_cfg["hud"]}</span>
  </div>
</header>
<div class="grid">
  <div class="card">
    <h2>Mode 1: State Machine &amp; Trail Graph</h2>
    <svg width="100%" height="200" viewBox="0 0 680 200">{svg_content}</svg>
  </div>
  <div class="card">
    <h2>Mode 3: Page Watchdog Feed</h2>
    <ul id="security-feed">
      <li>Watchdog active ({sec_cfg["mode"]} mode, HUD: {sec_cfg["hud"]})</li>
    </ul>
  </div>
  <div class="card">
    <h2>Recorded Journey Steps &amp; Fault Reports</h2>
    <ul id="steps-feed"></ul>
  </div>
  <div class="card">
    <h2>Mode 2: Standalone Reader Highlights &amp; Archives</h2>
    <ul id="reader-feed"></ul>
  </div>
</div>
</body>
</html>"""


class WorkbenchSession:
    """Host coordinator for a standalone `taf studio` session (with optional IKC3 sink)."""

    def __init__(self, m=None, library_dir=None, results_dir=None,
                 mode_override=None, hud_override=None, ws_url=None):
        self.model = m or {"sut": {"name": "session", "base-url": ""}, "states": {}, "journeys": {}}
        self.sec_cfg = resolve_security_config(
            self.model, mode_override=mode_override, hud_override=hud_override
        )
        self.library_dir = (library_dir
                            or os.environ.get("TAF_LIBRARY_DIR")
                            or "reader-library")
        self.results_dir = (results_dir
                            or os.environ.get("TAF_RESULTS")
                            or "results")
        self.ws_url = ws_url or os.environ.get("TAF_IKC3_WS")
        self.events = []
        self.security_alerts = []
        self.highlights = self._load_highlights()
        self.marks = []
        self.trails = []
        self.elements = {}
        self.steps = []
        self.secrets = record._secret_locators(self.model)

    def _highlights_path(self):
        return os.path.join(self.library_dir, "highlights.json")

    def _trails_path(self):
        return os.path.join(self.library_dir, "history-trails.jsonl")

    def _stall_queue_path(self):
        return os.path.join(self.results_dir, "unstalled-reports.json")

    def _load_highlights(self):
        path = self._highlights_path()
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_highlights(self):
        os.makedirs(self.library_dir, exist_ok=True)
        with open(self._highlights_path(), "w", encoding="utf-8") as f:
            json.dump(self.highlights, f, indent=2)

    def _enqueue_stalled_report(self, repro):
        """PLAN-ikc-v3-086-01 §4.4: keep unsent fault reports on disk when `/bus-ws` is absent."""
        path = self._stall_queue_path()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        queue = []
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    queue = json.load(f)
            except Exception:
                queue = []
        queue.append(repro)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2)
        return path

    @staticmethod
    def _source_page_url(source_info):
        """PLAN-ikc-v3-086-01 §3.1: read the address from `source.page`, never from the call payload."""
        if isinstance(source_info, dict):
            pg = source_info.get("page")
            if pg is not None and hasattr(pg, "url"):
                return pg.url
        return ""

    def handle_event(self, source_info, ev):
        """Callback bound to `context.expose_binding('__tafWorkbenchBridge', ...)`."""
        if not isinstance(ev, dict):
            return
        page_url = self._source_page_url(source_info)
        ev_copy = dict(ev)
        ev_copy["url"] = page_url
        self.events.append(ev_copy)
        etype = ev_copy.get("type")

        if etype == "config-change":
            if ev_copy.get("mode") in model.SECURITY_MODES:
                self.sec_cfg["mode"] = ev_copy["mode"]
            if ev_copy.get("hud") in model.SECURITY_HUDS:
                self.sec_cfg["hud"] = ev_copy["hud"]
            return

        if etype == "security-alert":
            self.security_alerts.append(ev_copy)
            journal_runtime.event(
                "security-alert",
                sink=ev_copy.get("sink"),
                mode=ev_copy.get("mode"),
                blocked=ev_copy.get("blocked"),
                reason=ev_copy.get("reason"),
                detail=ev_copy.get("detail"),
                url=page_url,
            )
            return

        if etype in ("click", "fill"):
            step = record._to_step(ev_copy, self.elements, self.secrets)
            self.steps.append(step)
            journal_runtime.event("step", step=step, url=page_url)
            return

        if etype == "visit":
            trail = {
                "url": page_url,
                "referrer": ev_copy.get("referrer", ""),
                "title": ev_copy.get("title", ""),
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            self.trails.append(trail)
            os.makedirs(self.library_dir, exist_ok=True)
            with open(self._trails_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(trail) + "\n")
            return

        if etype in ("highlight", "mark-selection"):
            entry = {
                "url": page_url,
                "exact": ev_copy.get("exact", ""),
                "prefix": ev_copy.get("prefix", ""),
                "suffix": ev_copy.get("suffix", ""),
                "loc": ev_copy.get("loc"),
                "note": ev_copy.get("note", ""),
            }
            self.marks.append(entry)
            self.highlights.setdefault(page_url, []).append(entry)
            self._save_highlights()
            label = entry["note"] or f"highlight: {entry['exact'][:60]}"
            journal_runtime.note(label)
            return

        if etype == "note":
            journal_runtime.note(ev_copy.get("text", "note"))
            return

        if etype == "archive-request":
            self.archive_article(
                url=page_url,
                title=ev_copy.get("title", "article"),
                text=ev_copy.get("text", ""),
            )
            return

        if etype == "fault-report":
            self.file_exploratory_fault(
                what=ev_copy.get("what", "Exploratory fault"),
                url=page_url,
                dom=ev_copy.get("dom", ""),
            )

    def archive_article(self, url, title, text, html=""):
        """Write an offline Reader bundle (`article.md` + optional `snapshot.html`) under library_dir."""
        slug = record._slug(title or url or "article")
        day = time.strftime("%Y-%m-%d")
        folder = os.path.join(self.library_dir, "archive", f"{day}-{slug}")
        os.makedirs(folder, exist_ok=True)
        hls = self.highlights.get(url) or []
        hl_lines = "\n".join(
            f"- > {h['exact']}" + (f" *(Note: {h['note']})*" if h.get("note") else "")
            for h in hls
        )
        md = (
            f"---\nurl: {url}\ntitle: {title}\narchived_at: {day}\n---\n\n"
            f"# {title}\n\n"
            f"## Highlights ({len(hls)})\n{hl_lines or '_None_'}\n\n"
            f"## Content\n\n{text.strip()}\n"
        )
        md_path = os.path.join(folder, "article.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        if html:
            with open(os.path.join(folder, "snapshot.html"), "w", encoding="utf-8") as f:
                f.write(html)
        return md_path

    def file_exploratory_fault(self, what, url="", dom=""):
        """Send `:support/file-report` if `TAF_IKC3_WS` is set; otherwise save to `unstalled-reports.json`."""
        repro = {
            "what": what,
            "url": url,
            "steps_so_far": list(self.steps),
            "elements": {name: loc for name, loc in self.elements.values()},
            "security_alerts": list(self.security_alerts),
            "report_id": None,
            "stalled": False,
        }
        if self.ws_url:
            try:
                rid = sink_ikc3.file_report(self.ws_url, what, url=url, dom=dom)
                repro["report_id"] = rid
            except Exception as err:
                repro["sink_error"] = str(err)
                repro["stalled"] = True
                self._enqueue_stalled_report(repro)
        else:
            repro["stalled"] = True
            self._enqueue_stalled_report(repro)
        journal_runtime.event("fault-report", **repro)
        return repro

    def attach_to_context(self, context):
        """Attach the closure-isolated bridge and watchdog init script to a BrowserContext."""
        context.expose_binding("__tafWorkbenchBridge", self.handle_event)
        script = build_init_script(
            self.sec_cfg,
            states=self.model.get("states") or {},
            secret_locators=self.secrets,
            saved_highlights=self.highlights,
        )
        context.add_init_script(script)


def launch_studio(m, base_url=None, out=None, title="studio",
                  security_mode=None, hud_mode=None, library_dir=None,
                  cdp_url=None, headless=False):
    """Launch the standalone two-tab Browser Workbench (or attach via `--cdp`)."""
    from playwright.sync_api import sync_playwright

    sut_name = (m.get("sut") or {}).get("name", "sut")
    base = base_url or os.environ.get("TAF_BASE_URL") or (m.get("sut") or {}).get("base-url", "about:blank")
    session = WorkbenchSession(
        m=m,
        library_dir=library_dir,
        mode_override=security_mode,
        hud_override=hud_mode,
    )
    print(f"taf studio — {sut_name} at {base} "
          f"[security={session.sec_cfg['mode']}, hud={session.sec_cfg['hud']}]",
          flush=True)
    with sync_playwright() as p:
        if cdp_url:
            browser = p.chromium.connect_over_cdp(cdp_url)
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        else:
            browser = launch_browser(p, headless=headless, slow_mo=50)
            ctx = browser.new_context()
            dash = ctx.new_page()
            dash.set_content(render_dashboard_html(
                sut_name, session.sec_cfg, states=m.get("states")
            ))
        session.attach_to_context(ctx)
        sut_page = ctx.new_page()
        sut_page.goto(base)
        if not headless:
            print("Press Enter in the console to finish the studio session...", flush=True)
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                pass
        if not cdp_url:
            browser.close()

    out_path = record._unique_out(out or f"recorded-{title}.json")
    draft = {
        "title": title,
        "steps": session.steps,
        "elements": {name: loc for name, loc in session.elements.values()},
        "marks": session.marks,
        "trails": session.trails,
        "security_alerts": session.security_alerts,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2)
        f.write("\n")
    return out_path
