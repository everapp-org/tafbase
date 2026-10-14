# tafbase

A test automation framework that is **DSL First**: a system under test is
declared once, as data, and real test suites are generated from the
declaration — Python+Playwright first, Java second, with the generators held
to byte-for-byte parity.

The plan and the architecture decisions are the corpus:

- [`arch-root/plans/PLAN-taf-v1-001-01-tafbase.md`](arch-root/plans/PLAN-taf-v1-001-01-tafbase.md)
  — the plan, starting with the release note (draft) that is the acceptance
  criteria
- [`arch-root/decisions/`](arch-root/decisions/) — the ADRs

## Layout

```
arch-root/        the corpus: plans, decisions, features, concepts, research, specs
gaks.project.json the project's declaration of itself
tools/            generated test emitters and checkers (as they land)
```

Developed in public. MIT licensed.
