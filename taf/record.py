"""taf record — drive a browser by hand, leave with model clauses.

@concept CONCEPT-dsl-v1-001-01-the-sut-model
@concept CONCEPT-playwright-v1-001-01-the-locator-ladder

The recorder drafts; the human declares. A headed browser opens at the
SUT; every click and fill is caught, mapped to the locator ladder's
best rung (testid, label, role+name, id/data-import-id, css), and the
session's steps + elements are written as JSON the author reviews and
merges into the model — recording never writes the model itself.
"""
import json
import os

JS = r"""
window.__taf_last_nav = location.href;
const ladder = (el) => {
  if (!el || !el.closest) return ["css", "body"];
  const idOf = (v) => v && /^[A-Za-z][\w\-]*$/.test(v) ? "#" + v : '[id="' + v + '"]';
  const testid = el.closest("[data-testid],[data-test-id],[data-qa]");
  if (testid) return ["testid", testid.getAttribute("data-testid")
                     || testid.getAttribute("data-test-id")
                     || testid.getAttribute("data-qa")];
  if (el.id) return ["css", idOf(el.id)];
  const di = el.closest("[data-import-id]");
  if (di) return ["css", '[data-import-id="' + di.getAttribute("data-import-id") + '"]'];
  const lab = el.labels && el.labels[0];
  if (lab) return ["label", lab.textContent.trim()];
  const roleMap = {BUTTON: "button", A: "link", TEXTAREA: "textbox", SELECT: "combobox"};
  const tag = el.tagName;
  let role = roleMap[tag];
  if (tag === "INPUT") {
    role = {text: "textbox", password: "textbox", checkbox: "checkbox",
            radio: "radio"}[el.type] || "textbox";
  }
  if (role) {
    const name = el.getAttribute("aria-label")
        || (tag === "INPUT" && el.placeholder) || el.innerText || el.title
        || el.name || "";
    if (name.trim()) return ["role", role, name.trim().slice(0, 60)];
  }
  return ["css", tag.toLowerCase()];
};
document.addEventListener("click", (e) => {
  window.__tafEmit({type: "click", loc: ladder(e.target)});
}, true);
document.addEventListener("change", (e) => {
  window.__tafEmit({type: "fill", loc: ladder(e.target), value: e.target.value});
}, true);
setInterval(() => {
  if (location.href !== window.__taf_last_nav) {
    window.__taf_last_nav = location.href;
    window.__tafEmit({type: "navigate", url: location.href});
  }
}, 400);
"""


def _secret_locators(m):
    """Locators whose model fills read env:/env-pool: — a recorded
    value on one of these emits the env reference, never the secret
    that was typed. Returns {locator-json: env-reference}."""
    out = {}
    els = m.get("elements") or {}
    for act in (m.get("actions") or {}).values():
        for s in (act.get("do") or []):
            if not (isinstance(s, dict) and "fill" in s):
                continue
            f = s["fill"]
            v = f.get("value", "")
            el = els.get(f.get("element"))
            if el and isinstance(v, str) and (
                    v.startswith("env:") or v.startswith("env-pool:")):
                out[json.dumps(el, sort_keys=True)] = v
    return out


def _unique_out(out):
    """A recording is an artifact — never silently overwritten: an
    existing path earns a timestamp suffix."""
    if not os.path.exists(out):
        return out
    stem, ext = os.path.splitext(out)
    import time
    return "%s-%s%s" % (stem, time.strftime("%Y%m%d-%H%M%S"), ext)


def _slug(s):
    import re
    return re.sub(r"-+", "-",
                  "".join(c if c.isalnum() else "-"
                          for c in s.lower())).strip("-")[:40] or "el"


def _to_step(ev, elements, secrets=None):
    """One recorded event → a model step, pooling elements by locator."""
    if ev["type"] == "navigate":
        return {"note": "goto " + ev["url"]}  # routes are the model's job
    loc = ({"role": ev["loc"][1], "name": ev["loc"][2]}
           if ev["loc"][0] == "role" else {ev["loc"][0]: ev["loc"][1]})
    key = json.dumps(loc, sort_keys=True)
    if key not in elements:
        name = _slug(ev["loc"][2] if len(ev["loc"]) > 2 else ev["loc"][1])
        while any(n == name for n, _ in elements.values()):
            name += "-2"
        elements[key] = (name, loc)
    name = elements[key][0]
    if ev["type"] == "click":
        return {"click": name}
    if secrets and key in secrets:
        return {"fill": {"element": name, "value": secrets[key]}}
    return {"fill": {"element": name, "value": ev.get("value", "")}}


def record(base, out, title="recorded", needs=(), env=None,
           m=None, headless=False):
    """Drive the browser by hand; on exit write the drafted clauses.

    Returns the path written. Press Enter in the console to stop.
    """
    from playwright.sync_api import sync_playwright
    env = os.environ if env is None else env
    events = []
    print("taf record — %s as %s" % (title, base), flush=True)
    # the contract: values where they are safe to show, set/unset for
    # secrets — the model names the need, never its value
    bv = env.get("TAF_BASE_URL")
    print("  env  %-18s %s" % ("TAF_BASE_URL",
          "%s  (this shell)" % bv if bv else "unset → model/url flag"),
          flush=True)
    for n in needs:
        print("  env  %-18s %s" % (n, "set" if env.get(n)
              else "unset — sign in by hand if the SUT asks"),
              flush=True)
    print("drive the SUT; Enter here ends the recording", flush=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=headless, slow_mo=50)
        pg = b.new_context().new_page()
        pg.expose_function("__tafEmit", lambda e: events.append(e))
        pg.add_init_script(JS)
        pg.goto(base)
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass
        b.close()
    out = _unique_out(out)
    elements = {}
    secrets = _secret_locators(m) if m else {}
    steps = [_to_step(e, elements, secrets) for e in events]
    secreted = sum(1 for s in steps
                   if isinstance(s, dict) and "fill" in s
                   and str(s["fill"].get("value", "")).startswith(("env:", "env-pool:")))
    draft = {"title": title, "steps": steps,
             "elements": {name: loc for name, loc in elements.values()}}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2)
        f.write("\n")
    print("recorded %d step(s), %d element(s)" % (len(steps), len(elements)),
          flush=True)
    if secreted:
        print("  %d fill(s) on env: elements — the reference is kept, "
              "the typed secret is not" % secreted, flush=True)
    print("saved → %s" % os.path.abspath(out), flush=True)
    print("review and merge into the model — recording drafts, "
          "you declare", flush=True)
    return out
