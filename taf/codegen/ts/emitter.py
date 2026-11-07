"""The orchestrators — two artifacts, two commands (TypeScript lane).

`taf emit-framework --lang ts -o <dir>` writes the vendor package
(taf-runtime/) — SUT-agnostic.

`taf emit-tests <model> --lang ts -o <dir>` writes the user suite —
sut.config, pages, elements, actions, one spec per test type — importing
runtime modules from the framework dir.

`taf emit` (compat) writes both into one dir: suite at the root,
framework nested under taf-runtime/.
"""

import json
import os

from taf import ops, spec as _s
from .common import _HEADER, set_framework, _fw
from .elements import _pages, _elements
from .actions import _actions
from .journeys import _suite_file, _SUITE_FILES
from .fixtures import _sut_config, _user_fixtures
from .framework import framework_files


_CUSTOM_README = """# custom/ — hand-authored tests live here (TypeScript)

Everything in this suite EXCEPT this directory is generated: edit the
model and regenerate, never the emitted files. Tests written by hand
belong in this directory — the emitter never writes here.

Hand-written tests inherit the suite: `test` runner, `page`, `request`,
`baseUrl`, `soft` fixtures from `fixtures`, `pages`, `elements`,
`actions`, the fault-report hook. What they do not inherit is the
model's guarantees — they are not walked, not in the manifest, not
covered by parity.

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
            "@types/node": "^22.0.0",
            "typescript": "^5.6.0"
        }
    }, indent=2) + "\n"


def _tsconfig_json():
    return json.dumps({
        "compilerOptions": {
            "target": "ES2022",
            "module": "ESNext",
            "moduleResolution": "bundler",
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True
        }
    }, indent=2) + "\n"


def _playwright_config(m):
    return f"""{_HEADER}import {{ defineConfig }} from "@playwright/test";

export default defineConfig({{
  testDir: ".",
  testMatch: /.*\\.spec\\.ts$/,
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


def _write(outdir, files):
    written = []
    art = _s.artifacts()
    for rel, content in files.items():
        if content is None:
            continue
        for aname, fname in art.items():
            content = content.replace("@@%s@@" % aname, fname)
        p = os.path.join(outdir, rel)
        parent = os.path.dirname(p)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(p)
    return written


def emit_framework(outdir):
    """Vendor command — no model. The SUT-agnostic taf-runtime package."""
    return _write(outdir, framework_files())


def emit_tests(m, outdir, framework="../taf-runtime"):
    """User command — the SUT-bound suite, importing runtime modules
    from `framework` (baked into the emitted imports)."""
    set_framework(framework)
    files = {
        "package.json": _package_json(m),
        "tsconfig.json": _tsconfig_json(),
        "playwright.config.ts": _playwright_config(m),
        "sut.config.ts": _sut_config(m),
        "fixtures.ts": _user_fixtures(framework),
        "pages.ts": _pages(m),
        "actions.ts": _actions(m),
        "elements.ts": _elements(m),
        "taf.manifest.json": _manifest(m),
        "taf.suite.json": _suite_json(m, framework),
        os.path.join("custom", "README.md"): _CUSTOM_README,
    }
    for jtype, fname in _SUITE_FILES.items():
        files[fname] = _suite_file(m, jtype)
    return _write(outdir, files)


def emit(model, outdir):
    """The compat single dir — suite at the root, framework nested.
    `taf emit` keeps working; emit-framework + emit-tests is the
    separated form."""
    written = emit_tests(model, outdir, framework="./taf-runtime")
    written += emit_framework(os.path.join(outdir, "taf-runtime"))
    return written


def _manifest(m):
    return json.dumps(ops.manifest(m), indent=2, sort_keys=True) + "\n"


def _suite_json(m, framework):
    from taf import model as _model
    return json.dumps(
        ops.suite_info(m, "ts", framework, _model.env_needs(m)),
        indent=2, sort_keys=True) + "\n"
