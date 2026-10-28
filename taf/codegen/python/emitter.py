"""The orchestrator — model → file map → written suite."""

import json
import os

from taf import ops
from taf import spec as _s
from .common import _HEADER
from .fixtures import _conftest, _auth_fixture
from .elements import _pages, _elements
from .actions import _actions
from .journeys import _journeys
from .runtime import _sink_source, _journal_source


_CUSTOM_README = """# custom/ — hand-authored tests live here

Everything in this suite EXCEPT this directory is generated: edit the
model and regenerate, never the emitted files. Tests written by hand
belong in this directory — the emitter never writes here.

Hand-written tests inherit the suite: `page`, `base_url` fixtures,
`pages`, `elements`, `actions`, the fault-report hook. What they do not
inherit is the model's guarantees — they are not walked, not in the
manifest, not covered by parity.

This directory is also the DSL's incubator (the absorption loop,
CONCEPT-dsl-v1-013-01): a pattern that recurs here is a clause the
model should learn. It should trend toward empty.
"""




def emit(model, outdir):
    """Write the suite into `outdir`; returns the list of files written."""
    os.makedirs(outdir, exist_ok=True)
    files = {"conftest.py": _conftest(model),
             "ikc3_sink.py": _sink_source(),
             "taf_journal.py": _journal_source(),
             "pages.py": _pages(model),
             "actions.py": _actions(model),
             "elements.py": _elements(model),
             "test_journeys.py": _journeys(model),
             "taf.manifest.json": _manifest(model),
             os.path.join("custom", "README.md"): _CUSTOM_README}
    written = []
    for name, content in files.items():
        if content is None:
            continue
        for k, v in _s.artifacts().items():
            content = content.replace("@@%s@@" % k, v)
        path = os.path.join(outdir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(path)
    return written


def _manifest(m):
    return json.dumps(ops.manifest(m), indent=2, sort_keys=True) + "\n"
