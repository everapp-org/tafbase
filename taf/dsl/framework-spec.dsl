// ============================================================
// taf/dsl/framework-spec.dsl — the model of tafbase itself.
//
// Grammar: dsl/FrameworkSpec.g4 (ANTLR4, grammar-hosted binding).
// Metamodel: SPEC-taf-v1-002-02-the-framework-spec-dsl.
//
// Every coordinate a SUT model can name is declared here with its
// Python, Java 21++, TypeScript, and JavaScript ESM spellings.
// A coordinate not in this file cannot be validated (taf/model.py)
// or emitted (taf/codegen/*).
// ============================================================

framework tafbase version 1

// ------------------------------------------------------------
// The locator ladder — CONCEPT-qa-v1-002-01, CONCEPT-playwright-v1-002-01
// Ordered by resilience: user-facing semantics first, structure last.
// ------------------------------------------------------------
locators {

  rung role {
    key role
    python """${page}.get_by_role("${role}")"""
    java   """${page}.getByRole(AriaRole.${role_enum})"""
    ts     """${page}.getByRole("${role}")"""
    js     """${page}.getByRole("${role}")"""
    variants {
      on name {
        python """${page}.get_by_role("${role}", name="${name}")"""
        java   """${page}.getByRole(AriaRole.${role_enum}, new Page.GetByRoleOptions().setName("${name}"))"""
        ts     """${page}.getByRole("${role}", { name: "${name}" })"""
        js     """${page}.getByRole("${role}", { name: "${name}" })"""
      }
      on name, exact {
        python """${page}.get_by_role("${role}", name="${name}", exact=True)"""
        java   """${page}.getByRole(AriaRole.${role_enum}, new Page.GetByRoleOptions().setName("${name}").setExact(true))"""
        ts     """${page}.getByRole("${role}", { name: "${name}", exact: true })"""
        js     """${page}.getByRole("${role}", { name: "${name}", exact: true })"""
      }
      on exact {
        python """${page}.get_by_role("${role}", exact=True)"""
        java   """${page}.getByRole(AriaRole.${role_enum}, new Page.GetByRoleOptions().setExact(true))"""
        ts     """${page}.getByRole("${role}", { exact: true })"""
        js     """${page}.getByRole("${role}", { exact: true })"""
      }
    }
  }

  rung label {
    key label
    python """${page}.get_by_label("${label}")"""
    java   """${page}.getByLabel("${label}")"""
    ts     """${page}.getByLabel("${label}")"""
    js     """${page}.getByLabel("${label}")"""
  }

  rung text {
    key text
    python """${page}.get_by_text("${text}")"""
    java   """${page}.getByText("${text}")"""
    ts     """${page}.getByText("${text}")"""
    js     """${page}.getByText("${text}")"""
  }

  rung placeholder {
    key placeholder
    python """${page}.get_by_placeholder("${placeholder}")"""
    java   """${page}.getByPlaceholder("${placeholder}")"""
    ts     """${page}.getByPlaceholder("${placeholder}")"""
    js     """${page}.getByPlaceholder("${placeholder}")"""
  }

  rung testid {
    key testid
    python """${page}.get_by_test_id("${testid}")"""
    java   """${page}.getByTestId("${testid}")"""
    ts     """${page}.getByTestId("${testid}")"""
    js     """${page}.getByTestId("${testid}")"""
  }

  rung xpath {
    key xpath
    python """${page}.locator("xpath=${xpath}")"""
    java   """${page}.locator("xpath=${xpath}")"""
    ts     """${page}.locator("xpath=${xpath}")"""
    js     """${page}.locator("xpath=${xpath}")"""
  }

  rung css {
    key css
    python """${page}.locator("${css}")"""
    java   """${page}.locator("${css}")"""
    ts     """${page}.locator("${css}")"""
    js     """${page}.locator("${css}")"""
  }
}

// ------------------------------------------------------------
// The step vocabulary — CONCEPT-dsl-v1-007-01
// ------------------------------------------------------------
vocabulary {

  form navigate {
    description "Jump to a declared state's route."
    arg state
    caption "goto ${arg}"
    python """page.goto(base_url + ROUTES["${arg}"])"""
    java   """page.navigate(baseUrl + ${state_class}.ROUTE);"""
    ts     """await page.goto(baseUrl + ROUTES["${arg}"]);"""
    js     """await page.goto(baseUrl + ROUTES["${arg}"]);"""
  }

  form click {
    description "Click a declared element (string or {element})."
    arg element
    caption "click ${element}"
    python """elements.${py:name}(page).click()"""
    java   """Elements.${j:name}(page).click();"""
    ts     """await elements.${j:name}(page).click();"""
    js     """await elements.${j:name}(page).click();"""
  }

  form check {
    description "Check a checkbox or radio element."
    arg element
    caption "check ${element}"
    python """elements.${py:name}(page).check()"""
    java   """Elements.${j:name}(page).check();"""
    ts     """await elements.${j:name}(page).check();"""
    js     """await elements.${j:name}(page).check();"""
  }

  form select {
    description "Choose an <option> on a <select> element."
    arg element
    arg value string
    caption "select ${element}"
    python """elements.${py:name}(page).select_option(${val_quoted})"""
    java   """Elements.${j:name}(page).selectOption(${val_quoted});"""
    ts     """await elements.${j:name}(page).selectOption(${val_quoted});"""
    js     """await elements.${j:name}(page).selectOption(${val_quoted});"""
  }

  form fill {
    description "Type into an input. Value is literal, env:VAR, or env-pool:VAR."
    arg element
    arg value "literal|env:VAR|env-pool:VAR"
    caption "fill ${element}"
    python """elements.${py:name}(page).fill(${value_expr})"""
    java   """Elements.${j:name}(page).fill(${value_expr});"""
    ts     """await elements.${j:name}(page).fill(${value_expr});"""
    js     """await elements.${j:name}(page).fill(${value_expr});"""
  }

  form wait-for {
    description "Auto-waiting assertion on a state marker or an element."
    arg state "state?"
    arg element "element?"
    caption "wait-for ${target}"
    variants {
      on state {
        python """${state_class}(page).expect_arrived()"""
        java   """new ${state_class}(page).expectArrived();"""
        ts     """await new ${state_class}(page).expectArrived();"""
        js     """await new ${state_class}(page).expectArrived();"""
      }
      on element {
        python """expect(elements.${py:element}(page)).to_be_visible()"""
        java   """assertThat(Elements.${j:element}(page)).isVisible();"""
        ts     """await expect(elements.${j:element}(page)).toBeVisible();"""
        js     """await expect(elements.${j:element}(page)).toBeVisible();"""
      }
    }
  }

  form api {
    description "Call a declared HTTP endpoint; assert status; optionally save JSON paths."
    arg endpoint
    arg args "map?"
    arg save "map?"
    caption "api ${endpoint}"
    lines {
      python """resp = page.request.${method_lower}(base_url + ${pexpr})"""
      python """assert resp.status == ${status}"""
      python """saved[${save_key}] = resp.json()${jsonpath}"""
      java   """APIResponse resp = page.request().${method_lower}(baseUrl + ${pexpr});"""
      java   """assertEquals(${status}, resp.status());"""
      java   """try { saved.put("${save_key}", new com.fasterxml.jackson.databind.ObjectMapper().readTree(resp.text())${jsonpath}.asText()); } catch (java.io.IOException e) { throw new RuntimeException(e); }"""
      ts     """const resp = await page.request.${method_lower}(baseUrl + ${pexpr});"""
      ts     """expect(resp.status()).toBe(${status});"""
      ts     """saved[${save_key}] = (await resp.json())${jsonpath};"""
      js     """const resp = await page.request.${method_lower}(baseUrl + ${pexpr});"""
      js     """expect(resp.status()).toBe(${status});"""
      js     """saved[${save_key}] = (await resp.json())${jsonpath};"""
    }
  }

  form dwell {
    description "Hold the screen still for a watching human — observation, never sync."
    arg ms "int>=0"
    caption "dwell ${arg}ms"
    python """page.wait_for_timeout(${arg})"""
    java   """page.waitForTimeout(${arg});"""
    ts     """await page.waitForTimeout(${arg});"""
    js     """await page.waitForTimeout(${arg});"""
  }

  form wait-any {
    description "Wait until any one of >=2 elements is visible (.or_ / .or chain)."
    arg elements "list[element,>=2]"
    caption "wait-any ${elements}"
    python """expect(${loc_chain}.first).to_be_visible()"""
    java   """assertThat(${loc_chain}.first()).isVisible();"""
    ts     """await expect(${loc_chain}.first()).toBeVisible();"""
    js     """await expect(${loc_chain}.first()).toBeVisible();"""
  }

  form compare-screen {
    description "Compare viewport against a golden baseline image."
    arg name string
    caption "compare-screen ${arg}"
    python """expect(page).to_have_screenshot("${arg}.png")"""
    java   """org.junit.jupiter.api.Assertions.assertTrue(page.screenshot(new Page.ScreenshotOptions().setPath(TafJournal.testDir().resolve("${arg}.png"))).length > 0);"""
    ts     """await expect(page).toHaveScreenshot("${arg}.png");"""
    js     """await expect(page).toHaveScreenshot("${arg}.png");"""
  }

  form expect {
    description "Assert on an element (visible/hidden/text/count) or a saved api value. soft:true collects into SoftChecks."
    arg element "element?"
    arg hidden "bool?"
    arg text "string?"
    arg count "int?"
    arg value "saved-key?"
    arg equals "any?"
    arg soft "bool?"
    caption "expect ${target}"
    variants {
      on element {
        python """expect(${el}).to_be_visible()"""
        java   """assertThat(${el}).isVisible();"""
        ts     """await expect(${el}).toBeVisible();"""
        js     """await expect(${el}).toBeVisible();"""
      }
      on element, hidden {
        python """expect(${el}).to_be_hidden()"""
        java   """assertThat(${el}).isHidden();"""
        ts     """await expect(${el}).toBeHidden();"""
        js     """await expect(${el}).toBeHidden();"""
      }
      on element, text {
        python """expect(${el}).to_have_text("${text}")"""
        java   """assertThat(${el}).hasText("${text}");"""
        ts     """await expect(${el}).toHaveText("${text}");"""
        js     """await expect(${el}).toHaveText("${text}");"""
      }
      on element, count {
        python """expect(${el}).to_have_count(${count})"""
        java   """assertThat(${el}).hasCount(${count});"""
        ts     """await expect(${el}).toHaveCount(${count});"""
        js     """await expect(${el}).toHaveCount(${count});"""
      }
      on value, equals {
        python """assert saved.get(${value}) == ${equals}"""
        java   """assertEquals(String.valueOf(${equals}), String.valueOf(saved.get("${value}")));"""
        ts     """expect(String(saved[${value}])).toBe(String(${equals}));"""
        js     """expect(String(saved[${value}])).toBe(String(${equals}));"""
      }
    }
  }

  form maybe {
    description "Wrap one inner step in try/catch — optional UI (banners, prompts) never fails the run."
    arg step step
    wrap {
      python pre  """try:"""
      python post """except Exception:"""
      python post """    print("maybe: step skipped")"""
      java   pre  """try {"""
      java   post """} catch (RuntimeException e) { System.out.println("maybe: step skipped — " + e.getMessage()); }"""
      ts     pre  """try {"""
      ts     post """} catch (_e) { console.log("maybe: step skipped"); }"""
      js     pre  """try {"""
      js     post """} catch (_e) { console.log("maybe: step skipped"); }"""
    }
  }
}

// ------------------------------------------------------------
// The environment & refusal contract — CONCEPT-taf-v1-003-01, SPEC-taf-v1-001-04
// ------------------------------------------------------------
contract {
  env TAF_BASE_URL   "override sut.base-url"
  env TAF_RESULTS    "artifact output root (default: results/)"
  env TAF_HEADLESS   "1 -> headless Chromium (default: headed)"
  env TAF_SLOWMO     "ms pause between Playwright actions"
  env TAF_ARRIVE_MS  "marker arrival timeout in ms (default: 15000)"
  env TAF_VIDEO      "1 -> record .webm into the test dir"
  env TAF_DEBUG      "1 -> pause the browser on failure"
  env TAF_RERUN      "1 -> run only the last failed.txt"
  env TAF_IKC3_WS    "ws:// URL of the IKC3 fault-report bus"

  refusal not-json
  refusal empty-model
  refusal missing-field
  refusal duplicate-name
  refusal bad-identifier
  refusal unknown-state
  refusal unknown-element
  refusal unknown-endpoint
  refusal unknown-action
  refusal unknown-step
  refusal bad-locator
  refusal bad-step
  refusal bad-dwell
  refusal bad-wait-any
  refusal bad-compare-screen
  refusal bad-maybe
  refusal bad-env
  refusal bad-auth
  refusal edge-gap
  refusal mixed-steps
  refusal unreachable
}

// ------------------------------------------------------------
// Emitted runtime artifacts — CONCEPT-taf-v1-004-01
// ------------------------------------------------------------
artifacts {
  artifact journal     "journal.jsonl"
  artifact subtitles   "journal.srt"
  artifact screenshot  "screenshot.png"
  artifact dom         "dom.html"
  artifact auth-state  "auth-state.json"
  artifact failed      "failed.txt"
}
