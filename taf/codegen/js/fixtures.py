"""The user side of the JS contract: sut.config.mjs — the facts
makeTafTest() asks for — and fixtures.mjs — the two-line binding."""

import json

from .common import *


def _sut_config(m):
    """sut.config.mjs — BASE_URL + SIGN_IN. The vendor artifact stays
    SUT-agnostic; this file is the binding."""
    auth = m["sut"].get("auth")
    lines = [_HEADER,
             "// @concept CONCEPT-dsl-v1-016-01-the-auth-clause\n\n"]
    if auth:
        act = auth["action"]
        cls = _state_class(m["actions"][act]["from"])
        lines.append("import { %s } from \"./pages.mjs\";\n"
                     "import * as actions from \"./actions.mjs\";\n\n" % cls)
    else:
        lines.append("\n")
    lines.append("export const BASE_URL = %s;\n\n" % json.dumps(m["sut"]["base-url"]))
    if auth:
        lines.append(
            "/**\n"
            " * @param {import(\"@playwright/test\").Page} page\n"
            " * @param {string} baseUrl\n"
            " */\n"
            "export async function signIn(page, baseUrl) {\n"
            "  const pageObj = new %s(page);\n"
            "  await pageObj.goto(baseUrl);\n"
            "  await actions.%s(page, baseUrl);\n"
            "}\n\n"
            "export const SIGN_IN = signIn;\n"
            % (cls, ops.camel(act)))
    else:
        lines.append("export const SIGN_IN = null;\n")
    return "".join(lines)


def _user_fixtures(framework):
    """fixtures.mjs — bind the framework's factory to this SUT. Every
    fixture lives in taf-runtime; the suite only says where it is."""
    fw = framework.rstrip("/")
    return _HEADER + """// @concept CONCEPT-pwtest-v1-001-01-test-extend-fixtures

import { makeTafTest } from "%s/fixtures.mjs";
import { BASE_URL, SIGN_IN } from "./sut.config.mjs";

export const { test, expect } = makeTafTest({
  baseUrl: BASE_URL,
  signIn: SIGN_IN,
});

export { SoftChecks } from "%s/soft-checks.mjs";
""" % (fw, fw)
