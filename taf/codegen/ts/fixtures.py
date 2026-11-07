"""The user side of the TS contract: sut.config.ts — the facts
makeTafTest() asks for — and fixtures.ts — the two-line binding."""

import json

from .common import *


def _sut_config(m):
    """sut.config.ts — BASE_URL + SIGN_IN. The vendor artifact stays
    SUT-agnostic; this file is the binding."""
    auth = m["sut"].get("auth")
    lines = [_HEADER,
             "// @concept CONCEPT-dsl-v1-016-01-the-auth-clause\n\n",
             "import { Page } from \"@playwright/test\";\n"]
    if auth:
        act = auth["action"]
        cls = _state_class(m["actions"][act]["from"])
        lines.append("import { %s } from \"./pages\";\n"
                     "import * as actions from \"./actions\";\n" % cls)
    lines.append("\nexport const BASE_URL = %s;\n\n" % json.dumps(m["sut"]["base-url"]))
    if auth:
        lines.append(
            "export async function signIn(page: Page, baseUrl: string): Promise<void> {\n"
            "  const pageObj = new %s(page);\n"
            "  await pageObj.goto(baseUrl);\n"
            "  await actions.%s(page, baseUrl);\n"
            "}\n\n"
            "export const SIGN_IN: ((page: Page, baseUrl: string) => Promise<void>) | null = signIn;\n"
            % (cls, ops.camel(act)))
    else:
        lines.append(
            "export const SIGN_IN: ((page: Page, baseUrl: string) => Promise<void>) | null = null;\n")
    return "".join(lines)


def _user_fixtures(framework):
    """fixtures.ts — bind the framework's factory to this SUT. Every
    fixture lives in taf-runtime; the suite only says where it is."""
    return _HEADER + """// @concept CONCEPT-pwtest-v1-001-01-test-extend-fixtures

import { makeTafTest } from "%s/fixtures";
import { BASE_URL, SIGN_IN } from "./sut.config";

export const { test, expect } = makeTafTest({
  baseUrl: BASE_URL,
  signIn: SIGN_IN,
});

export { SoftChecks } from "%s/soft-checks";
""" % (_fw_fixtures(framework), _fw_fixtures(framework))


def _fw_fixtures(framework):
    """The import root for framework modules — the baked --framework."""
    return framework.rstrip("/")
