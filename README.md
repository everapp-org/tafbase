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
taf/              the framework: the model loader now, the emitters next
suts/             declared systems under test (*.sut.model.json)
tests/            pytest suite for the framework itself
```

## Hacking on it

```
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest            # the suite
python3 gaks/tools/py/gaks_check.py --rules gaks/gaks.json --root arch-root --code taf
                                      # the corpus check, code citations included
```

Developed in public. MIT licensed.
