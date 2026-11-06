"""The contract section — env vars and refusal names declared in
taf/dsl/framework-spec.dsl must cover what the code actually uses."""

import os as _os
import re
import tempfile
from taf import model, spec
from taf.codegen.java import emitter as jem
from taf.codegen.python import emitter as pem
from taf.codegen.ts import emitter as tem
from taf.codegen.js import emitter as jsem


def test_refusal_names_declared():
    declared = set(spec.spec()["contract"]["refusals"])
    used = set(re.findall(r'_refusal\([^,]+,\s*"([a-z-]+)"',
                          open("taf/model.py").read()))
    assert used <= declared, \
        "refusal names used but undeclared: %s" % (used - declared)


def test_env_contract_covers_profile_vars():
    declared = set(spec.spec()["contract"]["env"])
    for v in ("TAF_BASE_URL", "TAF_RESULTS", "TAF_HEADLESS", "TAF_SLOWMO",
              "TAF_ARRIVE_MS", "TAF_VIDEO", "TAF_DEBUG", "TAF_RERUN",
              "TAF_IKC3_WS"):
        assert v in declared, "profile var %s not in the contract" % v


def test_every_declared_artifact_is_emitted():
    """The artifacts section's names must reach the generated files in
    all four target languages — substrate literals are pinned to the
    spec's declaration."""
    m = model.load("suts/ikc3-tracker.sut.model.json")
    suites = {}
    with tempfile.TemporaryDirectory() as d:
        for lang, em in (("python", pem), ("java", jem), ("ts", tem), ("js", jsem)):
            suites[lang] = "".join(
                open(f, encoding="utf-8").read()
                for f in em.emit(m, _os.path.join(d, lang))
            )
    for name, fname in spec.artifacts().items():
        for lang, text in suites.items():
            assert fname in text, "artifact %s (%s) missing from %s suite" % (name, fname, lang)
