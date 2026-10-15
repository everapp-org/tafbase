# Hacking on tafbase

The contract for *what* the framework does is
[`arch-root/specs/SPEC-taf-v1-001-02-the-sut-model.md`](arch-root/specs/SPEC-taf-v1-001-02-the-sut-model.md).
This file is how to work *on* it.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install pytest playwright websocket-client
.venv/bin/python -m playwright install chromium   # for live runs
```

Always invoke `.venv/bin/python`, never the system interpreter.

## Tests

```bash
.venv/bin/python -m pytest -q          # 37 fast, no browser needed
TAF_LIVE=1 .venv/bin/python -m pytest tests/test_live.py -v
```

The live tests need a SUT at `TAF_BASE_URL` (default
`http://127.0.0.1:4856`) — e.g. an IKC3 probe bus — and
`TAF_IKC3_WS` (default `ws://127.0.0.1:4856/bus-ws`) for the
fault-report filing tests. They are opt-in because they write real
frames into a real tracker; run them against a probe, not a deployment.

## Regenerating the emitted suites

`generated/` is committed — emitted code is reviewed in diffs like any
other change. After touching the model or an emitter:

```bash
.venv/bin/python -m taf emit --lang python suts/ikc3-tracker.sut.model.json -o generated/python/ikc3-tracker
.venv/bin/python -m taf emit --lang java   suts/ikc3-tracker.sut.model.json -o generated/java/ikc3-tracker
diff generated/python/ikc3-tracker/taf.manifest.json generated/java/ikc3-tracker/taf.manifest.json
```

The diff must be empty — SM-9's parity contract. `tests/test_parity.py`
enforces it; regenerate when emission changes so the committed copy is
what a fresh emit produces.

## The learning-surface rule

Generated code carries `@concept CONCEPT-taf-v1-NNN-NN-*` lines, and the
corpus checker refuses a citation with no page. When you add a construct
a newcomer must understand, add the concept page under
`arch-root/concepts/` and cite it — a concept used but uncited is a gap
the current checker cannot see, so the discipline is manual for now.

## Checking the corpus

```bash
python3 gaks/tools/py/gaks_check.py --rules gaks/gaks.json --root arch-root --code taf
python3 gaks/tools/py/gaks_check.py --rules gaks/gaks.json --root arch-root --code generated
```

`gaks/` is a generated bundle — never edit it. Rebuild it with
`gaks-bundle --update` from a GAKS tools checkout (IKC3's devbox script;
see `bin/gaks-bundle` there) after corpus changes.

## Conventions

- JSON is the only authoring format; EDN is not.
- Refuse ambiguity with a named reason; never guess (`SPEC …-02`, SM-7).
- Generate, don't interpret — emitted code is the artifact.
- One concept page per idea; cite where used, link where taught.
