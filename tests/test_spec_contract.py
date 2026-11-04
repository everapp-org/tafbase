"""The contract section — env vars and refusal names declared in
taf/dsl/framework-spec.dsl must cover what the code actually uses."""

import re
from taf import spec


def test_refusal_names_declared():
    declared = set(spec.spec()["contract"]["refusals"])
    used = set(re.findall(r'_refusal\(\s*\w+,\s*"([a-z-]+)"',
                          open("taf/model.py").read()))
    assert used <= declared, \
        "refusal names used but undeclared: %s" % (used - declared)


def test_env_contract_covers_profile_vars():
    declared = set(spec.spec()["contract"]["env"])
    for v in ("TAF_BASE_URL", "TAF_RESULTS", "TAF_SLOWMO",
              "TAF_VIDEO", "TAF_DEBUG", "TAF_RERUN"):
        assert v in declared, "profile var %s not in the contract" % v


def test_every_declared_artifact_is_emitted():
    """The artifacts section's names must reach the generated files —
    substrate literals are pinned to the spec's declaration."""
    import glob, json as _json
    from taf import model
    from taf.codegen.java import emitter as jem
    from taf.codegen.python import emitter as pem
    m = model.load("suts/ikc3-tracker.sut.model.json")
    java = pem_java = ""
    import tempfile, os as _os
    with tempfile.TemporaryDirectory() as d:
        for f in jem.emit(m, _os.path.join(d, "j")):
            java += open(f).read()
        for f in pem.emit(m, _os.path.join(d, "p")):
            pem_java += open(f).read()
    for name, fname in spec.artifacts().items():
        assert fname in java, "artifact %s (%s) missing from Java suite" % (name, fname)
        assert fname in pem_java, "artifact %s (%s) missing from Python suite" % (name, fname)
