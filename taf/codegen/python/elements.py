"""pages + elements — routes and locator spellings."""

from .common import *


def _pages(m):
    lines = [_HEADER,
             '"""One page object per declared state.\n\n'
             "@concept CONCEPT-pom-v1-001-01-the-page-object\n"
             "@concept CONCEPT-qa-v1-005-01-page-object-model\n"
             "@concept CONCEPT-playwright-v1-003-01-auto-waiting-and-actionability\n"
             '"""\n\nfrom playwright.sync_api import expect\nimport os\n\n',
             "ROUTES = {%s}\n\n" % ", ".join(f'"{n}": "{s.get("route", "")}"'
                                             for n, s in m["states"].items())]
    for name, st in m["states"].items():
        lines.append(
            f"class {_state_class(name)}:\n"
            f'    """The \'{name}\' state. Its marker proves arrival."""\n\n'
            f"    def __init__(self, page):\n"
            f"        self.page = page\n"
            f"        self.marker = {_loc(st['marker'])}\n\n"
            f"    def goto(self, base_url):\n"
            f'        self.page.goto(base_url + ROUTES["{name}"])\n\n'
            f"    def expect_arrived(self):\n"
            f"        expect(self.marker).to_be_visible("
            f"timeout=float(os.environ.get(\"TAF_ARRIVE_MS\", \"15000\")))\n\n")
    return "".join(lines)


def _elements(m):
    if not m.get("elements"):
        return None
    lines = [_HEADER,
             '"""Named locators, one function each — the locator ladder.\n\n'
             "@concept CONCEPT-qa-v1-002-01-the-locator-ladder\n"
             "@concept CONCEPT-playwright-v1-002-01-semantic-locators\n"
             '"""\n\n']
    for name, loc in m["elements"].items():
        lines.append(f"def {_py(name)}(page):\n    return {_loc(loc)}\n\n")
    return "".join(lines)
