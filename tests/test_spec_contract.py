"""The contract section — env vars and refusal names declared in
dsl/framework-spec.dsl must cover what the code actually uses."""

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
