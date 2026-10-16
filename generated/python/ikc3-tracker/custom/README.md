# custom/ — hand-authored tests live here

Everything in this suite EXCEPT this directory is generated: edit the
model and regenerate, never the emitted files. Tests written by hand
belong in this directory — the emitter never writes here.

Hand-written tests inherit the suite: `page`, `base_url` fixtures,
`pages`, `elements`, `actions`, the fault-report hook. What they do not
inherit is the model's guarantees — they are not walked, not in the
manifest, not covered by parity.

This directory is also the DSL's incubator (the absorption loop,
CONCEPT-dsl-v1-013-01): a pattern that recurs here is a clause the
model should learn. It should trend toward empty.
