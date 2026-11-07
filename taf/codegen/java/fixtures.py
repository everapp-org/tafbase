"""The user side of the Java contract: SutConfig — the SutProfile the
framework's ServiceLoader finds — and its META-INF/services entry."""

import json

from .common import *


def _sut_config(m):
    """taf.generated.SutConfig — implements taf.runtime.SutProfile: the
    base-url, whether the SUT signs in, and how."""
    auth = m["sut"].get("auth")
    lines = [_HEADER, f"package {_PKG};\n\n",
             "// @concept CONCEPT-dsl-v1-016-01-the-auth-clause\n\n",
             "import com.microsoft.playwright.Page;\n"
             "import taf.runtime.SutProfile;\n\n",
             "/** The SUT facts the framework asks for — the only SUT\n"
             " * knowledge outside the journey steps themselves. */\n",
             "public final class SutConfig implements SutProfile {\n\n",
             "    @Override\n"
             "    public String baseUrl() {\n"
             "        return %s;\n"
             "    }\n\n" % json.dumps(m["sut"]["base-url"]),
             "    @Override\n"
             "    public boolean requiresAuth() {\n"
             "        return %s;\n"
             "    }\n\n" % ("true" if auth else "false"),
             "    @Override\n"
             "    public void signIn(Page page, String baseUrl) {\n"]
    if auth:
        act = auth["action"]
        cls = _state_class(m["actions"][act]["from"])
        lines.append(
            "        new %s(page).gotoRoute(baseUrl);\n"
            "        Actions.%s(page, baseUrl, null);\n" % (cls, _j(act)))
    lines.append("    }\n}\n")
    return "".join(lines)


def _services_entry(m):
    """META-INF/services/taf.runtime.SutProfile — ServiceLoader reads
    the implementation class name; one line per provider."""
    return "%s.SutConfig\n" % _PKG
