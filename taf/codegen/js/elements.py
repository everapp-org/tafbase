"""pages + elements — routes and locator spellings (JavaScript ESM)."""

from .common import *


def _pages(m):
    lines = [
        _HEADER,
        "// @concept CONCEPT-pom-v1-001-01-the-page-object\n",
        "// @concept CONCEPT-qa-v1-005-01-page-object-model\n",
        "// @concept CONCEPT-playwright-v1-003-01-auto-waiting-and-actionability\n",
        "// @concept CONCEPT-js-v1-001-01-object-freeze-and-destructuring\n\n",
        "import { expect } from \"@playwright/test\";\n\n",
        "export const ROUTES = Object.freeze({\n",
        ",\n".join(f'  "{n}": "{s.get("route", "")}"' for n, s in m["states"].items()),
        "\n});\n\n"
    ]
    for name, st in m["states"].items():
        cls = _state_class(name)
        lines.append(
            f"/** The '{name}' state. Its marker proves arrival. */\n"
            f"export class {cls} {{\n"
            f"  /** @param {{import(\"@playwright/test\").Page}} page */\n"
            f"  constructor(page) {{\n"
            f"    this.page = page;\n"
            f"    this.marker = {_loc(st['marker'])};\n"
            f"  }}\n\n"
            f"  /** @param {{string}} baseUrl */\n"
            f"  async goto(baseUrl) {{\n"
            f"    await this.page.goto(baseUrl + ROUTES[\"{name}\"]);\n"
            f"  }}\n\n"
            f"  async expectArrived() {{\n"
            f"    const ms = Number(process.env[\"TAF_ARRIVE_MS\"] || 15000);\n"
            f"    await expect(this.marker).toBeVisible({{ timeout: ms }});\n"
            f"  }}\n"
            f"}}\n\n"
        )
    return "".join(lines)


def _elements(m):
    if not m.get("elements"):
        return None
    lines = [
        _HEADER,
        "// @concept CONCEPT-qa-v1-002-01-the-locator-ladder\n",
        "// @concept CONCEPT-playwright-v1-002-01-semantic-locators\n\n",
    ]
    for name, loc in m["elements"].items():
        lines.append(
            f"/** @param {{import(\"@playwright/test\").Page}} page */\n"
            f"export function {ops.camel(name)}(page) {{\n"
            f"  return {_loc(loc)};\n"
            f"}}\n\n"
        )
    return "".join(lines)
