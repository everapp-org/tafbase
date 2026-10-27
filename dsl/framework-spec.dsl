# framework-spec — the model of tafbase's test-automation framework.
# A project DSL (DSL-First §2.4): grammar-hosted binding, SPEC-taf-v1-002-02.
# Consumers: emit_java (done); emit_python + model.py next.

framework tafbase
version 1

locators {
  rung role {
    key role
    variants {
      on exact, name {
        python """{page}.get_by_role("${role}", name="${name}", exact=True)"""
        java """page.getByRole("${role}", new Page.GetByRoleOptions().setName("${name}").setExact(true))"""
      }
      on name {
        python """{page}.get_by_role("${role}", name="${name}")"""
        java """page.getByRole("${role}", new Page.GetByRoleOptions().setName("${name}"))"""
      }
      on exact {
        python """{page}.get_by_role("${role}", exact=True)"""
        java """page.getByRole("${role}", new Page.GetByRoleOptions().setExact(true))"""
      }
      on {
        python """{page}.get_by_role("${role}")"""
        java """page.getByRole("${role}")"""
      }
    }
  }
  rung label {
    key label
    python """{page}.get_by_label("${label}")"""
    java """page.getByLabel("${label}")"""
  }
  rung text {
    key text
    python """{page}.get_by_text("${text}")"""
    java """page.getByText("${text}")"""
  }
  rung placeholder {
    key placeholder
    python """{page}.get_by_placeholder("${placeholder}")"""
    java """page.getByPlaceholder("${placeholder}")"""
  }
  rung testid {
    key testid
    python """{page}.get_by_test_id("${testid}")"""
    java """page.getByTestId("${testid}")"""
  }
  rung xpath {
    key xpath
    python """{page}.locator("xpath=${xpath}")"""
    java """page.locator("xpath=${xpath}")"""
  }
  rung css {
    key css
    python """{page}.locator("${css}")"""
    java """page.locator("${css}")"""
  }
}

vocabulary {
  form navigate {
    arg state-name
    caption """goto ${arg}"""
    python """page.goto(base_url + ROUTES["${arg}"])"""
    java """page.navigate(baseUrl + ${state_class}.ROUTE);"""
  }
  form click {
    arg element name
    caption """click ${element}"""
    python """elements.${py:name}(page).click()"""
    java """Elements.${j:name}(page).click();"""
  }
  form check {
    arg element name
    caption """check ${element}"""
    python """elements.${py:name}(page).check()"""
    java """Elements.${j:name}(page).check();"""
  }
  form select {
    arg element name
    arg value string
    caption """select ${element}"""
    python """elements.${py:name}(page).select_option(${val_quoted})"""
    java """Elements.${j:name}(page).selectOption(${val_quoted});"""
  }
  form fill {
    arg element name
    arg value "string|env:|env-pool:"
    caption """fill ${element}"""
    python """elements.${py:name}(page).fill(${value_expr})"""
    java """Elements.${j:name}(page).fill(${value_expr});"""
  }
  form wait-for {
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
    arg ms number
    caption """dwell ${arg}ms"""
    python """page.wait_for_timeout(${arg})"""
    java """page.waitForTimeout(${arg});"""
  }
  form wait-any {
    arg list-of element-name
    caption """wait-any ${arg}"""
    python """expect(${loc_chain}).to_be_visible()"""
    java """assertThat(${loc_chain}).isVisible();"""
  }
  form compare-screen {
    arg name string
    caption """compare-screen ${arg}"""
    python """expect(page).to_have_screenshot("${arg}.png")"""
    java """assertThat(page).hasScreenshot();  // baseline: ${arg}.png"""
  }
  form expect {
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
