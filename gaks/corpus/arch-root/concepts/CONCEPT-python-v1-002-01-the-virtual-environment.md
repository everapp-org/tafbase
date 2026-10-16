---
id: CONCEPT-python-v1-002-01-the-virtual-environment
status: draft
subproject: python
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The virtual environment

## Definition

A **virtual environment** — `.venv/` in this repo — is a directory that
redirects where Python looks for packages. It is not a copy of Python.
Inside:

```
.venv/
├── bin/python        # a stub — the same interpreter, different eyes
├── bin/pip           # installs into THIS directory
├── pyvenv.cfg        # home = /usr/bin — where the real interpreter lives
└── lib/python3.12/site-packages/   # this project's own package store
```

Running `.venv/bin/python` *is* the mechanism: the interpreter reads
`pyvenv.cfg` beside itself, learns `include-system-site-packages =
false`, and resolves imports in `.venv/lib/.../site-packages` only.
"Activating" (`source .venv/bin/activate`) is merely a convenience that
puts `.venv/bin` first on `PATH` so a bare `python` resolves there —
this repo never relies on it and always names `.venv/bin/python`
explicitly. The path is the activation.

## Why it exists

Packages collide. `pip install playwright` without a venv writes into
*one* shared `site-packages` for the whole system: a second project
needing another version, or an OS tool written in Python, now fights
for the same slots. A venv gives each project its own package store, so
`pytest 9` here and `pytest 7` elsewhere coexist, and so
`python3 -m venv .venv && .venv/bin/pip install pytest playwright`
reproduces this toolchain on any machine without touching — or needing
permission to touch — the system Python.

## In this project

`.venv/` is gitignored — it is recreated, never committed. It holds
`pytest`, `playwright`, `websocket-client`, and nothing else; every
command in this corpus and in CONTRIBUTING.md calls `.venv/bin/python`
(or `.venv/bin/python -m pytest`, `.venv/bin/python -m taf`), never the
bare `python`, so a run cannot silently pick up the system's package
set. The generated suites it runs are in `generated/`; the emitters it
runs are `taf/`.

## Touch it

```bash
cat .venv/pyvenv.cfg          # which interpreter it shadows, and how it was made
.venv/bin/python -m pip list  # what this project alone has installed
python3 -m venv /tmp/other    # make a second one — the cost is seconds
```

Delete `.venv/` entirely and nothing is lost: `python3 -m venv .venv`
plus the README's install line rebuilds it.

## Neighbors

Environment variables are a different thing sharing the word —
[[CONCEPT-taf-v1-003-01-the-environment]]. What the venv installs is
pytest and Playwright: [[CONCEPT-pytest-v1-001-01-the-pytest-fixture]],
[[CONCEPT-playwright-v1-002-01-the-browser-context]].
