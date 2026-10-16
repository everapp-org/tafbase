---
id: CONCEPT-dsl-v1-008-01-the-image-step
status: draft
subproject: dsl
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The image step

## Definition

A step that acts on pixels, not the DOM: find a template image on the
screen and click it — the old framework's OpenCV `matchTemplate` used
to clear CloudFlare's "verify you are human" checkbox, and its Sikuli
layer did wait/highlight/click-by-image and OCR.

## Why it exists

Some surfaces have no accessible DOM — anti-bot gates, canvas apps,
native dialogs. The image step is the *last rung past the last rung*:
fragile by nature, and honest only when it says so. The better fix is
always cooperation — the old framework also sent a `tradu-test` header
so the backend whitelisted automation. Keep both: negotiate when you
can, match pixels when you cannot.

## In this project

Deferred — niche. The locator ladder's `css`/`xpath` rung is fragile
the same way; an image step would carry `fragile` in the manifest like
they do. See RESEARCH-taf-v1-002-01, harvest item 19.

## Touch it

Not implemented. The honest placeholder: treat it as a `fragile`
locator when it arrives.

## Neighbors

[[CONCEPT-playwright-v1-001-01-the-locator-ladder]],
[[CONCEPT-testing-v1-003-01-the-golden-file]] (image comparison done
right).
