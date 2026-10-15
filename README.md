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
arch-root/        the corpus: plans, decisions, concepts, specs
gaks.project.json the project's declaration of itself
gaks/             the delivered static GAKS bundle (generated — never edit)
taf/              the framework: model loader, canonical ops, emitters
suts/             declared systems under test (*.sut.model.json)
generated/        emitted suites, committed for review
  python/<sut>/   pytest + Playwright
  java/<sut>/     JUnit 5 + Playwright-Java (Maven)
tests/            pytest suite for the framework itself
```

## What it does today

```
.venv/bin/python -m taf check suts/ikc3-tracker.sut.model.json   # validate
.venv/bin/python -m taf emit --lang python suts/ikc3-tracker.sut.model.json -o generated/python/ikc3-tracker
.venv/bin/python -m taf emit --lang java   suts/ikc3-tracker.sut.model.json -o generated/java/ikc3-tracker
diff generated/python/ikc3-tracker/taf.manifest.json generated/java/ikc3-tracker/taf.manifest.json
                                                # identical — the parity contract
```

## Hacking on it

See [CONTRIBUTING.md](CONTRIBUTING.md) — setup, tests (incl. the opt-in
live run), regenerating emitted suites, and the corpus check.

Developed in public. MIT licensed.
