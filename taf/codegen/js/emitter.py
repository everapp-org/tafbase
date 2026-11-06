"""emit() + package.json + jsconfig.json + playwright.config.mjs — JavaScript ESM codegen."""

import json
import os

from taf import ops, spec as _s
from .common import _HEADER
from .elements import _pages, _elements
from .actions import _actions
from .journeys import _journeys
from .fixtures import _fixtures
from .runtime import _journal_source, _sink_source


_CUSTOM_README = """# custom/ — hand-authored tests live here (JavaScript ESM)

Everything in this suite EXCEPT this directory is generated: edit the
model and regenerate, never the emitted files. Tests written by hand
belong in this directory — the emitter never writes here.

Hand-written tests inherit the suite: `test` runner, `page`, `baseUrl`,
and `soft` fixtures from `fixtures`, `pages`, `elements`, `actions`.
What they do not inherit is the model's guarantees — they are not walked,
not in the manifest, not covered by parity.

This directory is also the DSL's incubator (the absorption loop,
CONCEPT-dsl-v1-013-01): a pattern that recurs here is a clause the
model should learn. It should trend toward empty.
"""


def _package_json(m):
    return json.dumps({
        "name": f"{m['sut']['name']}-tests",
        "version": "0.1.0",
        "private": True,
        "type": "module",
        "scripts": {
            "test": "playwright test"
        },
        "devDependencies": {
            "@playwright/test": "^1.49.0",
            "@types/node": "^22.0.0"
        }
    }, indent=2) + "\n"


def _jsconfig_json():
    return json.dumps({
        "compilerOptions": {
            "target": "ES2022",
            "module": "NodeNext",
            "moduleResolution": "NodeNext",
            "checkJs": True,
            "esModuleInterop": True,
            "skipLibCheck": True
        }
    }, indent=2) + "\n"


def _playwright_config(m):
    return f"""{_HEADER}import {{ defineConfig }} from "@playwright/test";

export default defineConfig({{
  testDir: ".",
  testMatch: /.*\\.spec\\.mjs$/,
  timeout: 60000,
  use: {{
    baseURL: process.env["TAF_BASE_URL"] || "{m['sut']['base-url']}",
    headless: process.env["TAF_HEADLESS"] === "1",
    launchOptions: {{
      slowMo: Number(process.env["TAF_SLOWMO"] || 0),
    }},
  }},
}});
"""


def _manifest(m):
    return json.dumps(ops.manifest(m), indent=2, sort_keys=True) + "\n"


def emit(m, outdir):
    """Write the JavaScript ESM suite into outdir; returns list of written paths."""
    os.makedirs(outdir, exist_ok=True)
    art = _s.artifacts()
    files = {
        "package.json": _package_json(m),
        "jsconfig.json": _jsconfig_json(),
        "playwright.config.mjs": _playwright_config(m),
        "pages.mjs": _pages(m),
        "fixtures.mjs": _fixtures(m),
        "journeys.spec.mjs": _journeys(m),
        "taf_journal.mjs": _journal_source(),
        "ikc3_sink.mjs": _sink_source(),
        "taf.manifest.json": _manifest(m),
        os.path.join("custom", "README.md"): _CUSTOM_README,
    }
    el = _elements(m)
    if el is not None:
        files["elements.mjs"] = el
    act = _actions(m)
    if act is not None:
        files["actions.mjs"] = act

    for k in list(files):
        for aname, fname in art.items():
            files[k] = files[k].replace("@@%s@@" % aname, fname)

    written = []
    for rel, content in sorted(files.items()):
        p = os.path.join(outdir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(p)
    return written
