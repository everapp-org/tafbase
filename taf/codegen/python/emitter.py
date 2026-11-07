"""The orchestrators — two artifacts, two commands.

`taf emit-framework --lang python -o <dir>` writes the vendor package
(taf_runtime/) — SUT-agnostic, driven by framework-spec.dsl alone.

`taf emit-tests <model> --lang python -o <dir>` writes the user suite —
sut_config, pages, elements, actions, and one test file per test type —
against that framework.

`taf emit` (the compat form) writes both into one self-contained dir:
the suite at the root, the framework nested under taf-runtime/.
"""

import json
import os

from taf import ops
from taf import spec as _s
from .common import _HEADER
from .fixtures import _conftest, _sut_config
from .elements import _pages, _elements
from .actions import _actions
from .journeys import _suite_file, _pytest_ini, _SUITE_FILES
from .framework import framework_files


_CUSTOM_README = """# custom/ — hand-authored tests live here

Everything in this suite EXCEPT this directory is generated: edit the
model and regenerate, never the emitted files. Tests written by hand
belong in this directory — the emitter never writes here.

Hand-written tests inherit the suite: `page`, `api`, `base_url`,
`soft` fixtures, `pages`, `elements`, `actions`, the fault-report
hook. What they do not inherit is the model's guarantees — they are
not walked, not in the manifest, not covered by parity.

This directory is also the DSL's incubator (the absorption loop,
CONCEPT-dsl-v1-013-01): a pattern that recurs here is a clause the
model should learn. It should trend toward empty.
"""


def _write(outdir, files):
    written = []
    for name, content in files.items():
        if content is None:
            continue
        for k, v in _s.artifacts().items():
            content = content.replace("@@%s@@" % k, v)
        path = os.path.join(outdir, name)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(path)
    return written


def emit_framework(outdir):
    """Vendor command — no model. The SUT-agnostic taf_runtime package."""
    return _write(outdir, framework_files())


def emit_tests(m, outdir, framework="../taf-runtime"):
    """User command — the SUT-bound suite, written against the
    framework at `framework` (recorded into conftest.py and
    taf.suite.json)."""
    files = {"conftest.py": _conftest(m, framework),
             "sut_config.py": _sut_config(m),
             "pages.py": _pages(m),
             "actions.py": _actions(m),
             "elements.py": _elements(m),
             "pytest.ini": _pytest_ini(m),
             "taf.manifest.json": _manifest(m),
             "taf.suite.json": _suite_json(m, framework),
             os.path.join("custom", "README.md"): _CUSTOM_README}
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
        ops.suite_info(m, "python", framework, _model.env_needs(m)),
        indent=2, sort_keys=True) + "\n"
