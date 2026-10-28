// framework-spec — the model of tafbase's test-automation framework.
// A project DSL (DSL-First §2.4): grammar-hosted binding, SPEC-taf-v1-002-02.
// Consumers: emit_java (done); emit_python + model.py next.

framework tafbase
version 1

locators {
  rung role {
    description "the a11y rung — role plus optional name/exact"
    key role
    variants {
      on exact, name {
        python """{page}.get_by_role("${role}", name="${name}", exact=True)"""
        java """page.getByRole(AriaRole.${role_enum}, new Page.GetByRoleOptions().setName("${name}").setExact(true))"""
      }
      on name {
        python """{page}.get_by_role("${role}", name="${name}")"""
        java """page.getByRole(AriaRole.${role_enum}, new Page.GetByRoleOptions().setName("${name}"))"""
      }
      on exact {
        python """{page}.get_by_role("${role}", exact=True)"""
        java """page.getByRole(AriaRole.${role_enum}, new Page.GetByRoleOptions().setExact(true))"""
      }
      on {
        python """{page}.get_by_role("${role}")"""
        java """page.getByRole(AriaRole.${role_enum})"""
      }
    }
  }
  rung label {
    description "an input named by its label"
    key label
    python """{page}.get_by_label("${label}")"""
    java """page.getByLabel("${label}")"""
  }
  rung text {
    description "visible text — markers and errors"
    key text
    python """{page}.get_by_text("${text}")"""
    java """page.getByText("${text}")"""
  }
  rung placeholder {
    description "input placeholder text"
    key placeholder
    python """{page}.get_by_placeholder("${placeholder}")"""
    java """page.getByPlaceholder("${placeholder}")"""
  }
  rung testid {
    description "the test hook — data-testid style"
    key testid
    python """{page}.get_by_test_id("${testid}")"""
    java """page.getByTestId("${testid}")"""
  }
  rung xpath {
    description "the escape hatch — brittle, rare"
    key xpath
    python """{page}.locator("xpath=${xpath}")"""
    java """page.locator("xpath=${xpath}")"""
  }
  rung css {
    description "ids, data-* attrs, structure — the working rung"
    key css
    python """{page}.locator("${css}")"""
    java """page.locator("${css}")"""
  }
}

vocabulary {
  form navigate {
    description "go to a state by route"
    arg state-name
    caption """goto ${arg}"""
    python """page.goto(base_url + ROUTES["${arg}"])"""
    java """page.navigate(baseUrl + ${state_class}.ROUTE);"""
  }
  form click {
    description "press an element"
    arg element name
    caption """click ${element}"""
    python """elements.${py:name}(page).click()"""
    java """Elements.${j:name}(page).click();"""
  }
  form check {
    description "tick a checkbox element"
    arg element name
    caption """check ${element}"""
    python """elements.${py:name}(page).check()"""
    java """Elements.${j:name}(page).check();"""
  }
  form select {
    description "choose a select option"
    arg element name
    arg value string
    caption """select ${element}"""
    python """elements.${py:name}(page).select_option(${val_quoted})"""
    java """Elements.${j:name}(page).selectOption(${val_quoted});"""
  }
  form fill {
    description "type a value — env:/env-pool: name the need, never the secret"
    arg element name
    arg value "string|env:|env-pool:"
    caption """fill ${element}"""
    python """elements.${py:name}(page).fill(${value_expr})"""
    java """Elements.${j:name}(page).fill(${value_expr});"""
  }
  form wait-for {
    description "synchronize on a state marker or element"
    arg state name
    arg element name
    caption """wait-for ${arg}"""
    variants {
      on state {
        python """${state_class}(page).expect_arrived()"""
        java """new ${state_class}(page).expectArrived();"""
      }
      on element {
        python """expect(elements.${py:element}(page)).to_be_visible()"""
        java """assertThat(Elements.${j:element}(page)).isVisible();"""
      }
    }
  }
  form api {
    description "call a declared endpoint, assert status, save fields"
    arg endpoint name
    arg args map
    arg save map
    caption """api ${arg}"""
    lines {
      python """resp = page.request.${method_lower}(base_url + ${pexpr})"""
      python """assert resp.status == ${status}"""
      python """saved[${save_key}] = resp.json()${jsonpath}"""
      java """APIResponse resp = page.request().${method_lower}(baseUrl + ${pexpr});"""
      java """assertEquals(${status}, resp.status());"""
      java """saved.put("${save_key}", resp.json()${jsonpath});"""
    }
  }
  form dwell {
    description "a pause for a watching human — observation, not synchronization"
    arg ms number
    caption """dwell ${arg}ms"""
    python """page.wait_for_timeout(${arg})"""
    java """page.waitForTimeout(${arg});"""
  }
  form wait-any {
    description "the first of several elements to appear wins"
    arg list-of element-name
    caption """wait-any ${arg}"""
    python """expect(${loc_chain}).to_be_visible()"""
    java """assertThat(${loc_chain}).isVisible();"""
  }
  form compare-screen {
    description "pixel-compare against a golden baseline"
    arg name string
    caption """compare-screen ${arg}"""
    python """expect(page).to_have_screenshot("${arg}.png")"""
    java """assertThat(page).hasScreenshot();  // baseline: ${arg}.png"""
  }
  form expect {
    description "assert visibility, text, count, or a saved value — soft collects for end-of-test flush"
    arg element name
    arg text string
    arg count number
    arg hidden bool
    arg value saved
    arg equals any
    arg soft wraps-element
    caption """expect ${arg}"""
    variants {
      on element, hidden {
        python """expect(${el}).to_be_hidden()"""
        java """assertThat(${el}).isHidden();"""
      }
      on element, text {
        python """expect(${el}).to_have_text("${text}")"""
        java """assertThat(${el}).hasText("${text}");"""
      }
      on element, count {
        python """expect(${el}).to_have_count(${count})"""
        java """assertThat(${el}).hasCount(${count});"""
      }
      on element {
        python """expect(${el}).to_be_visible()"""
        java """assertThat(${el}).isVisible();"""
      }
      on equals, value {
        python """assert saved[${value}] == ${equals}"""
        java """assertEquals(${equals}, saved.get("${value}"));"""
      }
    }
  }
  form maybe {
    description "ifPresent semantics — try a step, never fail on it"
    arg step nested
    caption """maybe ${inner}"""
    wrap {
      python pre """try:"""
      python post """except Exception:"""
      python post """    pass  # maybe: the step did not apply"""
      java pre """try {"""
      java post """} catch (Exception ignored) { /* maybe: not applicable */ }"""
    }
  }
}

contract {
  env TAF_BASE_URL "effective base url — flag > env > model"
  env TAF_RESULTS "results root"
  env TAF_HEADLESS "headed runs when unset"
  env TAF_SLOWMO "playwright slow_mo, milliseconds"
  env TAF_ARRIVE_MS "arrival patience per state, ms — default 15000"
  env TAF_VIDEO "record .webm into the test dir"
  env TAF_DEBUG "pause on failure"
  env TAF_RERUN "replay the last failed.txt only"
  env TAF_IKC3_WS "fault-report websocket url"
  refusal bad-locator
  refusal unknown-step
  refusal unknown-element
  refusal unknown-state
  refusal unknown-endpoint
  refusal bad-dwell
  refusal bad-wait-any
  refusal bad-compare-screen
  refusal bad-maybe
  refusal bad-env
  refusal bad-auth
  refusal duplicate-name
  refusal missing-field
  refusal mixed-steps
  refusal unknown-action
  refusal edge-gap
}

artifacts {
  // what a generated framework leaves behind — names, not paths:
  // per-test artifacts resolve inside the test's own dir
  artifact journal    "journal.jsonl"   // the event log, one per test
  artifact subtitles  "journal.srt"     // timed narration, copied to the video name
  artifact screenshot "screenshot.png"  // the screen at failure
  artifact dom        "dom.html"        // the page DOM at failure
  artifact auth-state "auth-state.json" // the signed-in session, once per run
  artifact failed     "failed.txt"      // the rerun manifest, per run dir
}
