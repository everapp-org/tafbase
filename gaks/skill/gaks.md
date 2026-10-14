---
name: gaks
description: GAKS 0.11.0 for tafbase. Use it before you write or change a document of the corpus (a decision, feature, plan, research or specification), and before you add an annotation such as `@feature F-...` to code. It gives the id of a document, the kinds and their folders, the status words, the decision block, wikilinks, code annotations, and the commands that check the corpus and write a new document.
---

<!-- The bundle fills the fields in double braces. Do not edit this copy.
     A new bundle replaces it. -->

# GAKS 0.11.0 for tafbase

GAKS keeps the architecture knowledge of tafbase as typed Markdown documents.
The documents link to each other with wikilinks. Code links to them with
annotations in comments. A checker tests the corpus against the rules in
`gaks.json`.

**Read this skill before you write a document. Do not guess the rules.**

## The reader comes first

A person who is new to the project and an assistant in a new session are one
audience. Both need the words of the project, the reasons in the text, and the
decisions where the code uses them. Write each document for that reader.

## Where the documents are

- The corpus is `corpus/arch-root/`.
- A document is at `corpus/arch-root/<subproject>/<folder of its kind>/<id>.md`.
- A Markdown file whose name is not an id is a page. The checker reads its
  wikilinks and its decision blocks. It does not check its frontmatter.

## The id of a document

The file name is the id, with `.md` added:

```
KIND-subproject-vN-NNN-RR-words.md
```

| part | meaning | example |
|---|---|---|
| `KIND` | the prefix of a declared kind | `ADR` |
| `subproject` | a declared subproject | `shop` |
| `vN` | the major version of the subproject, only the major | `v1` |
| `NNN` | three digits. The next free number of the series `KIND-subproject-vN` | `004` |
| `RR` | two digits, the revision. A new document starts at `01` | `01` |
| `words` | lower case words with hyphens | `pick-a-store` |

Example: `ADR-shop-v1-004-01-pick-a-store.md`.

- The frontmatter `id:` is the file name without `.md`.
- Do not rename a document. To change an accepted document, write a new file
  with the next `RR`, for example `-02`. Keep the old file.
- Do not count the numbers yourself. The template tool finds the next free
  number (see "Write a new document").

## The kinds

| prefix | name | folder | template headings |
|---|---|---|---|
| `ADR` | Decision record | `decisions/` | `Context` · `Decision` · `Consequences` · `The pillars, tested` |
| `CONCEPT` | Concept | `concepts/` | `Definition` · `Why it exists` |
| `PLAN` | Plan | `plans/` | `Release note (draft)` · `The pillars, tested` · `The lanes` |
| `F` | Feature | `features/` | `Summary` · `Acceptance criteria` |
| `RESEARCH` | Research | `research/` | `Why this exists` · `How it was measured` · `The summary` · `The decisions that are George's` |
| `SPEC` | Specification | `specs/` | none |

A document of a kind goes into the folder of that kind. The checker gives the
finding `kind-folder` when a document is in the folder of another kind.

## The subprojects

- `taf`

The frontmatter `subproject:` holds one of these words. Do not write a list.

## The frontmatter

Each document starts with a frontmatter block. Line 1 is `---`, and a second
`---` line closes the block:

```
---
id: ADR-shop-v1-004-01-pick-a-store
status: draft
date: 2026-10-13
subproject: shop
authors: []
---

# Pick a store
```

A document with no frontmatter block gives the finding `frontmatter-missing`.

## The page states and the status words

A document is in one of five page states: draft, review, accepted, superseded,
archived. The `status:` field holds a word, and each word belongs to one state:

| page state | meaning | status words |
|---|---|---|
| draft | Being written. | `backlog`, `brainstorm`, `captured`, `draft`, `in-progress`, `not yet specified`, `open`, `planned`, `pre-item`, `proposed`, `queued`, `running`, `shaping` |
| review | Written, and it waits for a person to accept it. | `awaiting-answers`, `needs-triage`, `review`, `spec-ready`, `specified` |
| accepted | Accepted. A change is a new -VV sibling. | `accepted`, `accepted-with-known-limitation`, `active`, `approved`, `closed`, `complete`, `done`, `frozen`, `graduated`, `implemented`, `informational`, `investigated`, `met` |
| superseded | A newer document replaces it. | `deprecated`, `superseded`, a word that starts with `superseded by` |
| archived | Kept for the record. | `abandoned`, `archived`, `dropped`, `parked` |

A status that is not in this table gives the finding `status-unknown`. Do not
write a list of words such as `draft | accepted`.

## The decision block

Write an open question as a decision block. The block is a quote with a callout
head:

```
> [!decision] D1 open
> Which store do we use for the orders?
> Recommendation: the database of the project.
> Opens: the order history page.
```

- The key, here `D1`, is capital letters and digits, and it ends with a digit.
  It is unique in the document.
- The head is one of three forms:
  - `<key> open`
  - `<key> decided <yyyy-mm-dd> <who>`
  - `<key> withdrawn <yyyy-mm-dd> <who>`
- A line that starts with `Recommendation:`, `Answer:`, `Opens:` or `Why:` is a
  field. The other lines are the question.
- The block stops at the first line that is not a quote line.

When a person decides, change the head and add the answer:

```
> [!decision] D1 decided 2026-10-14 Ann
> Which store do we use for the orders?
> Recommendation: the database of the project.
> Answer: the database of the project.
```

A block that does not obey this grammar gives the finding `decision-malformed`.
A block inside a fenced code block is an example, and the checker ignores it.

## Wikilinks

Link a document to a document with a wikilink. Write the full id, with the words:

```
[[ADR-shop-v1-004-01-pick-a-store]]
[[ADR-shop-v1-004-01-pick-a-store|the store decision]]
[[ADR-shop-v1-004-01-pick-a-store#Decision]]
```

A link to a name that no file has gives the finding `wikilink-unresolved`. A
link inside code is ignored.

## Annotations in code

Link code to a document with an annotation in a comment. Write `@`, a word, a
space and the id:

```python
# @feature F-shop-v1-002-01-order-history
def order_history(customer):
    ...
```

```java
// @feature F-shop-v1-002-01-order-history
// @adr ADR-shop-v1-004-01-pick-a-store
public class OrderHistory {
}
```

- The id is the full id with the words, or the id up to the revision, for
  example `F-shop-v1-002-01`.
- Use the full id. Do not shorten it.
- With `--code <src>`, the checker reads each source file. An id that is no
  document gives the finding `code-link-unresolved`.

## Check the corpus

Python 3.9 or later, no installation:

```
python3 tools/py/gaks_check.py --rules gaks.json --root corpus/arch-root
python3 tools/py/gaks_check.py --rules gaks.json --root corpus/arch-root --code <src>
```

Node 22, no installation:

```
node tools/check.mjs --rules gaks.json --root corpus/arch-root [--code <src>]
```

The two checkers give the same findings. Add `--json` for a report that a
program can read. The exit code is 0 when the corpus obeys the rules. Run a
check after each change, and repair each finding before you stop.

## Write a new document

```
python3 tools/py/gaks_new.py --rules gaks.json --root corpus/arch-root \
    --kind ADR --subproject <subproject> --title "Pick a store"
```

The tool finds the next free number. It writes the file into the folder of the
kind, with the frontmatter and one heading for each section of the template of
the kind. It prints the path. Options: `--major N` (default 1), `--status <word>`
(default `draft`), `--dry-run`. It refuses a kind, a subproject or a status that
`gaks.json` does not declare.

## Build the site

Node 22:

```
node tools/site.mjs --rules gaks.json --root corpus/arch-root --out site
```

## The rules are generated

`gaks.json` is generated from a declaration. Do not edit it. To add a kind, a
subproject or a ceiling, change `gaks.project.json`, the declaration in the
repository of the project. Then make the rules again:

```
python3 tools/py/gaks_rules.py --project gaks.project.json --out gaks.json
```

A status word comes from `tools/gaks.base.json`, which the project does not
edit.

## Before you stop

1. Each new document has its id from the template tool.
2. Each document has frontmatter, a declared status and a declared subproject.
3. Each open question is a decision block.
4. New code names its document in an annotation.
5. The checker exits with 0.
