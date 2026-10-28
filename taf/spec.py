"""The framework-spec model, loaded once — dsl/framework-spec.dsl
parsed via the ANTLR grammar. Every consumer (validator, ops,
emitters) reads the same artifact."""

import os

_cache = {}


def spec():
    if "m" not in _cache:
        from taf import dsl_parse
        path = os.path.join(os.path.dirname(__file__), "..",
                            "dsl", "framework-spec.dsl")
        _cache["m"] = dsl_parse.parse(open(path).read())
    return _cache["m"]


def rungs():
    """Locator ladder rungs in preference order — last listed is the
    fallback rung."""
    return tuple(spec()["locators"].keys())


def forms():
    """Step forms in declaration order."""
    return tuple(spec()["vocabulary"].keys())


def artifacts():
    """Generated-file names a framework leaves behind."""
    return spec()["artifacts"]


def entry(section, name):
    return spec()[section][name]
