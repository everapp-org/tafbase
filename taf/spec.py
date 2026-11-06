"""The framework-spec model, loaded once — taf/dsl/framework-spec.dsl
parsed via the ANTLR grammar. The file is package data: an installed
taf reads it the same way a checkout does. Every consumer (validator,
ops, emitters) reads the same artifact."""

_cache = {}


def spec():
    if "m" not in _cache:
        from importlib.resources import files
        from taf import dsl_parse
        text = (files("taf") / "dsl" / "framework-spec.dsl") \
            .read_text(encoding="utf-8")
        _cache["m"] = dsl_parse.parse(text)
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
