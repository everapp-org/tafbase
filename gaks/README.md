# tafbase — the GAKS corpus

This folder is a **static GAKS bundle**, GAKS 0.11.0, made on 2026-10-15.
It holds 12 Markdown files. The last check found the corpus clean.

GAKS keeps the architecture knowledge of a project: decisions, features, plans,
research and specifications. Each one is a typed Markdown document with
wikilinks. This copy needs no server and no package manager.

| folder | what it holds |
|---|---|
| `corpus/arch-root/` | the Markdown documents |
| `gaks.json` | the rules. A generated file |
| `tools/` | the checker and the site generator, for Node 22 |
| `tools/py/` | the checker and the template tool, for Python 3.9 |
| `skill/gaks.md` | the skill for an assistant, such as Claude Code |
| `site/` | the site, built |

## Read it

- **In a browser:** open `site/index.html`. It works from the disk, with no
  server. It has the tree of each kind, each document with its backlinks, the
  decision log, a report of each kind, and a search.
- **In an editor:** open `corpus/arch-root/` in Obsidian, Foam or VS Code. The
  wikilinks and the decision callouts work there.

## Check it

With Python 3.9 or later. You need no installation:

```
python3 tools/py/gaks_check.py --rules gaks.json --root corpus/arch-root
```

With Node 22. You need no npm install:

```
node tools/check.mjs --rules gaks.json --root corpus/arch-root
```

The two checkers give the same findings. The exit code is 0 when the corpus
obeys the rules of `gaks.json`. Add `--json` for a report that a program can
read.

To check the links from the source code to the documents, add `--code <src>`.
An annotation in a comment of a Python or Java file, for example
`# @feature F-shop-v1-002-01-order-history`, must name a document:

```
python3 tools/py/gaks_check.py --rules gaks.json --root corpus/arch-root --code <src>
node tools/check.mjs --rules gaks.json --root corpus/arch-root --code <src>
```

## Write a new document

The template tool finds the next free number. It writes the frontmatter and the
headings of the template of the kind:

```
python3 tools/py/gaks_new.py --rules gaks.json --root corpus/arch-root \
    --kind ADR --subproject <subproject> --title "Pick a store"
```

## Give the rules to an assistant

`skill/gaks.md` gives an assistant the rules of this corpus: the ids, the kinds,
the status words, the decision block and the commands. For Claude Code, copy it
to `.claude/skills/gaks.md` in the repository of the project.

## Build the site again

After you change a document, use Node 22:

```
node tools/site.mjs --rules gaks.json --root corpus/arch-root --out site
```

## The rules

`gaks.json` is generated from `gaks.project.json`, the declaration of the project. **Do not edit `gaks.json` by hand.**

A project keeps its declaration in its own repository, as one JSON file,
`gaks.project.json`:

```json
{"name": "Shop",
 "subprojects": ["shop"],
 "kinds": ["ADR", "PLAN", "F",
           {"prefix": "RUNBOOK", "name": "Runbook", "folder": "runbooks",
            "template": ["Purpose", "Steps"]}],
 "ratchets": {}}
```

- `kinds`: a string takes a kind of `tools/gaks.base.json`. An object is a new
  kind of the project. Omit the key to get every kind of the base.
- `ratchets`: a ceiling for a rule. Each rule with no ceiling is a hard rule.

To add a kind, a subproject or a ceiling, change the declaration. Then make
the rules again, with Python 3.9 and nothing else:

```
python3 tools/py/gaks_rules.py --project gaks.project.json --out gaks.json
```

`tools/gaks.base.json` holds what every project takes from the active GAKS: the
id pattern, the core kinds, the status words and the decision block. Do not
edit it. An update of the bundle by the active GAKS (`--update`) replaces the
tools, the base, `gaks.json`, this README, the skill and the site. It keeps
`corpus/`.

`gaks.json` names:

- the id of a document: `KIND-subproject-vN-NNN-RR-words.md`
- the kinds of document, and the folder of each
- the status words, and the page state of each: draft, review, accepted,
  superseded, archived
- the subprojects
- the decision block:

```
> [!decision] D1 open
> The question.
> Recommendation: the answer we recommend.
> Opens: what it makes possible
```

When the decision is made, the head changes to
`> [!decision] D1 decided 2026-10-12 <who>`, and an `Answer:` line is added.

## The last check

```
kind-undeclared: 0
id-not-filename: 0
id-duplicate: 0
status-unknown: 0
subproject-unknown: 0
decision-malformed: 0
wikilink-unresolved: 0  (ratchet, ceiling 0)
frontmatter-missing: 0
kind-folder: 0
code-link-unresolved: 0
```
