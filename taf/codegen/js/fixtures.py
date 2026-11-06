"""fixtures.mjs — the fixture layer, auth bootstrap, hooks (JavaScript ESM)."""

from .common import *


def _auth_fixture(m):
    act = m["sut"]["auth"]["action"]
    from_state = m["actions"][act]["from"]
    cls = _state_class(from_state)
    act_fn = ops.camel(act)
    return f"""
// @concept CONCEPT-dsl-v1-016-01-the-auth-clause
// @concept CONCEPT-playwright-v1-008-01-storage-state-reuse
let authStatePath = null;

/**
 * @param {{import("@playwright/test").Browser}} browser
 * @param {{string}} targetBaseUrl
 * @returns {{Promise<string>}}
 */
async function performAuthOnce(browser, targetBaseUrl) {{
  if (authStatePath) return authStatePath;
  const storagePath = path.join(runDir, "@@auth-state@@");
  const ctx = await browser.newContext();
  const pg = await ctx.newPage();
  try {{
    const pageObj = new {cls}(pg);
    await pageObj.goto(targetBaseUrl);
    await actions.{act_fn}(pg, targetBaseUrl);
  }} catch (err) {{
    const setupDir = path.join(runDir, "setup");
    fs.mkdirSync(setupDir, {{ recursive: true }});
    try {{
      const dom = await pg.content();
      fs.writeFileSync(path.join(setupDir, "@@dom@@"), dom, "utf-8");
      await pg.screenshot({{ path: path.join(setupDir, "@@screenshot@@") }});
    }} catch (_ignored) {{}}
    if (process.env["TAF_DEBUG"] === "1") {{
      await pg.pause();
    }}
    await ctx.close();
    throw err;
  }}
  await ctx.storageState({{ path: storagePath }});
  await ctx.close();
  authStatePath = storagePath;
  return storagePath;
}}
"""


def _fixtures(m):
    has_auth = bool(m.get("sut", {}).get("auth"))
    auth_concepts = ""
    auth_imports = ""
    auth_code = ""
    auth_call = ""
    if has_auth:
        auth_concepts = (
            "// @concept CONCEPT-dsl-v1-016-01-the-auth-clause\n"
            "// @concept CONCEPT-playwright-v1-008-01-storage-state-reuse\n"
        )
        act = m["sut"]["auth"]["action"]
        from_state = m["actions"][act]["from"]
        cls = _state_class(from_state)
        auth_imports = f"import {{ {cls} }} from \"./pages.mjs\";\nimport * as actions from \"./actions.mjs\";\n"
        auth_code = _auth_fixture(m)
        auth_call = "authStorage = await performAuthOnce(browser, baseUrl);"
    else:
        auth_code = "\n// Auth artifact reference: @@auth-state@@\n"

    base_url_model = m["sut"]["base-url"]

    return f"""{_HEADER}
// @concept CONCEPT-pwtest-v1-001-01-test-extend-fixtures
// @concept CONCEPT-playwright-v1-001-01-browser-context-page-hierarchy
// @concept CONCEPT-taf-v1-003-01-the-environment
// @concept CONCEPT-taf-v1-004-01-the-artifacts
// @concept CONCEPT-testing-v1-002-01-the-failure-funnel
// @concept CONCEPT-testing-v1-004-01-the-rerun
// @concept CONCEPT-taf-v1-002-01-the-result-sink
// @concept CONCEPT-js-v1-001-01-object-freeze-and-destructuring
// @concept CONCEPT-js-v1-006-01-async-fixture-callback
// @concept CONCEPT-js-v1-010-01-process-env-binding
{auth_concepts}
import * as fs from "node:fs";
import * as path from "node:path";
import {{ test as base, expect }} from "@playwright/test";
import {{ tafJournal }} from "./taf_journal.mjs";
import * as ikc3Sink from "./ikc3_sink.mjs";
{auth_imports}
const _MODEL_BASE_URL = "{base_url_model}";

function makeRunDir() {{
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  const stamp = `${{d.getFullYear()}}${{pad(d.getMonth() + 1)}}${{pad(d.getDate())}}-${{pad(d.getHours())}}${{pad(d.getMinutes())}}${{pad(d.getSeconds())}}`;
  return path.join(process.env["TAF_RESULTS"] || "results", stamp);
}}

const runDir = makeRunDir();
const baseUrl = process.env["TAF_BASE_URL"] || _MODEL_BASE_URL;
const headless = process.env["TAF_HEADLESS"] === "1";
const slowmo = process.env["TAF_SLOWMO"] || "0";
const video = process.env["TAF_VIDEO"] ? "on" : "off";
const arriveMs = process.env["TAF_ARRIVE_MS"] || "15000";

console.log(
  `taf env: base_url=${{baseUrl}} headless=${{headless}} slowmo=${{slowmo}} video=${{video}} arrive_ms=${{arriveMs}} results=${{runDir}}`
);

export class SoftChecks {{
  constructor() {{
    /** @type {{string[]}} */
    this.failures = [];
  }}

  /**
   * @param {{string}} label
   * @param {{() => Promise<void> | void}} fn
   */
  async check(label, fn) {{
    try {{
      await fn();
    }} catch (e) {{
      this.failures.push(`${{label}} — ${{e?.message ?? e}}`);
    }}
  }}

  assertAll() {{
    if (this.failures.length > 0) {{
      throw new Error(`${{this.failures.length}} soft check(s) failed: ${{this.failures.join("; ")}}`);
    }}
  }}

  flush() {{
    this.assertAll();
  }}
}}

/** @type {{string[]}} */
const FAILED_TESTS = [];

function getLastFailed() {{
  try {{
    const resultsRoot = process.env["TAF_RESULTS"] || "results";
    if (!fs.existsSync(resultsRoot)) return null;
    const entries = fs.readdirSync(resultsRoot, {{ withFileTypes: true }})
      .filter((e) => e.isDirectory())
      .map((e) => path.join(resultsRoot, e.name, "@@failed@@"))
      .filter((p) => fs.existsSync(p))
      .sort();
    if (entries.length === 0) return null;
    const latest = entries[entries.length - 1];
    const lines = fs.readFileSync(latest, "utf-8").trim().split(/\\s+/).filter(Boolean);
    return new Set(lines);
  }} catch {{
    return null;
  }}
}}

process.on("exit", () => {{
  try {{
    fs.mkdirSync(runDir, {{ recursive: true }});
    fs.writeFileSync(path.join(runDir, "@@failed@@"), FAILED_TESTS.join("\\n") + (FAILED_TESTS.length ? "\\n" : ""), "utf-8");
    // Artifact manifest: @@manifest@@
    console.log("\\nresults → " + runDir);
    if (FAILED_TESTS.length > 0) {{
      console.log("failed → " + FAILED_TESTS.join(", ") + "  (rerun: TAF_RERUN=1 npx playwright test)");
    }}
  }} catch (_ignored) {{}}
}});
{auth_code}
export const test = base.extend({{
  baseUrl: async ({{}}, use) => {{
    await use(baseUrl);
  }},
  soft: async ({{}}, use) => {{
    const s = new SoftChecks();
    await use(s);
    s.assertAll();
  }},
  context: async ({{ browser }}, use) => {{
    let authStorage = undefined;
    {auth_call}
    const contextOptions = {{}};
    if (authStorage) {{
      contextOptions.storageState = authStorage;
    }}
    if (process.env["TAF_VIDEO"] === "1") {{
      contextOptions.recordVideo = {{ dir: tafJournal.testDir() }};
    }}
    const ctx = await browser.newContext(contextOptions);
    await use(ctx);
    await ctx.close();
  }},
  page: async ({{ context }}, use, testInfo) => {{
    if (process.env["TAF_RERUN"] === "1") {{
      const lastFailed = getLastFailed();
      if (lastFailed && !lastFailed.has(testInfo.title)) {{
        testInfo.skip(true, "TAF_RERUN: not in last @@failed@@");
        return;
      }}
    }}
    tafJournal.begin(runDir, testInfo.title);
    const pg = await context.newPage();
    let failed = false;
    try {{
      await use(pg);
    }} catch (err) {{
      failed = true;
      throw err;
    }} finally {{
      const isFailed = testInfo.status !== testInfo.expectedStatus || failed;
      if (isFailed) {{
        failed = true;
        FAILED_TESTS.push(testInfo.title);
        const d = tafJournal.testDir();
        try {{
          await pg.screenshot({{ path: path.join(d, "@@screenshot@@") }});
          const dom = await pg.content();
          fs.writeFileSync(path.join(d, "@@dom@@"), dom, "utf-8");
        }} catch (_ignored) {{}}
        tafJournal.event("fail", {{ test: testInfo.title }});
        const wsUrl = process.env["TAF_IKC3_WS"];
        if (wsUrl) {{
          try {{
            const errStr = (testInfo.error?.message || "test failed").split("\\n")[0].slice(0, 200);
            const fp = ikc3Sink.fingerprint(testInfo.title, errStr);
            const old = ikc3Sink.filed(fp);
            if (old) {{
              console.log(`fault report already filed: ${{old}} (fp ${{fp}})`);
              tafJournal.note(`fault report already filed: ${{old}}`);
            }} else {{
              const rid = await ikc3Sink.fileReport(
                wsUrl,
                `taf journey failed: ${{testInfo.title}} — ${{errStr}}`,
                {{ url: pg.url(), dom: await pg.content().catch(() => "") }}
              );
              ikc3Sink.record(fp, rid);
              console.log("fault report filed:", rid);
            }}
          }} catch (sinkErr) {{
            console.log("ikc3 sink could not file the report:", sinkErr);
          }}
        }}
        if (process.env["TAF_DEBUG"] === "1") {{
          await pg.pause();
        }}
      }}
      tafJournal.end(isFailed ? "failed" : "passed");
    }}
  }},
}});

export {{ expect }};
"""
