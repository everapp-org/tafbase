"""The user side of the fixture contract: conftest.py — the framework
bootstrap + plugin binding — and sut_config.py — the SUT facts the
framework reads back (base-url, env needs, the auth bootstrap)."""

from .common import *


def _conftest(m, framework):
    """A thin bootstrap: find the emitted taf-runtime dir, put it on
    sys.path, and bind its pytest plugin. Every fixture lives in the
    framework; the suite only says where it is."""
    return _HEADER + '''"""Suite bootstrap — find taf_runtime, load its plugin.

The framework dir resolves in order: TAF_FRAMEWORK, the path this
suite was emitted against, a nested ./taf-runtime, a sibling
../taf-runtime.

@concept CONCEPT-pytest-v1-001-01-dependency-injected-fixtures
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_FRAMEWORK = %s
_CANDIDATES = [
    os.environ.get("TAF_FRAMEWORK"),
    os.path.normpath(os.path.join(_HERE, _FRAMEWORK)),
    os.path.join(_HERE, "taf-runtime"),
    os.path.join(_HERE, "..", "taf-runtime"),
]
for _cand in _CANDIDATES:
    if _cand and os.path.isdir(_cand):
        sys.path.insert(0, _cand)
        break

pytest_plugins = ["taf_runtime.fixtures"]
''' % json.dumps(framework)


def _sut_config(m):
    """The SUT facts the framework reads back — the vendor artifact
    stays SUT-agnostic; this file is the binding."""
    needs = []
    from taf import model as _model
    needs = _model.env_needs(m)
    lines = [_HEADER,
             '"""SUT binding — what the generated framework needs to\n'
             'know about this system under test.\n\n'
             "@concept CONCEPT-dsl-v1-016-01-the-auth-clause\n"
             '"""\n\n',
             'BASE_URL = %s\n' % json.dumps(m["sut"]["base-url"]),
             'ENV_NEEDS = %s\n' % json.dumps(needs)]
    auth = m["sut"].get("auth")
    if auth:
        act = auth["action"]
        cls = _state_class(m["actions"][act]["from"])
        lines.append('''

def sign_in(page, base_url):
    """One sign-in, run once per run in the framework's bootstrap
    context; the session is kept as storage state."""
    import actions
    from pages import %s
    %s(page).goto(base_url)
    actions.%s(page, base_url)


SIGN_IN = sign_in
''' % (cls, cls, _py(act)))
    else:
        lines.append("\n\nSIGN_IN = None\n")
    return "".join(lines)
