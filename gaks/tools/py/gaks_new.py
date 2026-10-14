#!/usr/bin/env python3
# gaks_new.py: write a new GAKS document from the template of its kind.
#
#
#   python3 gaks_new.py --rules gaks.json --root <dir>/arch-root \
#       --kind ADR --subproject shop --title "the words" \
#       [--major 1] [--status draft] [--date YYYY-MM-DD] [--dry-run]
#
# The tool reads every .md file under --root, in all folders. It finds the
# highest number of the series KIND-<subproject>-v<major>. The new document
# gets the next number and revision 01. It goes to
#   <root>/<subproject>/<folder of the kind>/<KIND>-<sub>-v<major>-<NNN>-01-<slug>.md
# The file has a frontmatter block, a `# <title>` heading and one
# `## <heading>` for each template entry of the kind in gaks.json.
#
# The tool refuses a kind that gaks.json does not declare, a subproject that
# it does not declare, and a status that is not a status word. Then it exits
# with 2 and writes nothing. On success it prints the path and exits with 0.
#
# Python 3.9 or later, the standard library only. One file, so a bundle can
# copy it beside gaks_check.py.

import argparse
import datetime
import json
import os
import re
import sys
import unicodedata


class Refusal(Exception):
    """A request that the rules do not allow. The tool exits with 2."""


def load_rules(path):
    try:
        with open(path, encoding='utf-8') as f:
            rules = json.load(f)
    except (OSError, ValueError) as e:
        raise Refusal('cannot read the rules %s: %s' % (path, e))
    if not isinstance(rules, dict) or not isinstance(rules.get('kinds'), list) \
            or not isinstance(rules.get('subprojects'), list) \
            or not isinstance(rules.get('id-pattern'), str):
        raise Refusal('the rules %s have no kinds, subprojects or id-pattern' % path)
    return rules


# The status words. This mirrors gaks/js/lib/states.mjs: trim, lower case,
# and each run of whitespace or underscores becomes one hyphen.

def normalise_status(status):
    t = str(status).strip()
    if t == '':
        return None
    return re.sub(r'[\s_]+', '-', t.lower())


def status_words(rules):
    """The declared status words, in their normal form."""
    words = set()
    for ws in ((rules.get('page-states') or {}).get('words') or {}).values():
        words.update(normalise_status(w) for w in ws)
    st = rules.get('statuses') or {}
    for w in list(st.get('editable') or []) + list(st.get('frozen') or []):
        words.add(normalise_status(w))
    words.discard(None)
    return words


def is_known_status(rules, status):
    n = normalise_status(status)
    if n is None or '|' in status:
        return False
    if n in status_words(rules):
        return True
    prefixes = (rules.get('page-states') or {}).get('prefix-words') or {}
    for p in prefixes:
        pn = normalise_status(p)
        if pn is not None and (n == pn or n.startswith(pn + '-')):
            return True
    return False


def slugify(title):
    """The words of the title as a kebab-case slug of ASCII letters and digits."""
    ascii_text = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '-', ascii_text.lower()).strip('-')


def markdown_files(root):
    """Every .md file name under root. A folder whose name starts with a dot is skipped."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != 'node_modules']
        for name in filenames:
            if name.endswith('.md') and not name.startswith('.'):
                yield name


def next_number(rules, root, series):
    """The next free number of the series, from the file names under root."""
    pattern = re.compile(rules['id-pattern'])
    highest = 0
    for name in markdown_files(root):
        m = pattern.search(name)
        if m and m.group(1) == series:
            highest = max(highest, int(m.group(2)))
    if highest >= 999:
        raise Refusal('the series %s has no free number after 999' % series)
    return highest + 1


def render(doc_id, title, status, date, subproject, template):
    lines = [
        '---',
        'id: %s' % doc_id,
        'status: %s' % status,
        'date: %s' % date,
        'subproject: %s' % subproject,
        'authors: []',
        '---',
        '',
        '# %s' % title,
        '',
    ]
    for heading in template:
        lines += ['## %s' % heading, '', '']
    return '\n'.join(lines).rstrip('\n') + '\n'


def plan(rules, root, kind, subproject, title, major=1, status='draft', date=None):
    """The path and the text of the new document. Raises Refusal."""
    kinds = {k.get('prefix'): k for k in rules['kinds'] if isinstance(k, dict)}
    if kind not in kinds:
        raise Refusal('the kind %s is not declared. Declared: %s'
                      % (kind, ', '.join(sorted(p for p in kinds if p))))
    if subproject not in rules['subprojects']:
        raise Refusal('the subproject %s is not declared. Declared: %s'
                      % (subproject, ', '.join(rules['subprojects'])))
    if not is_known_status(rules, status):
        raise Refusal('the status "%s" is not a status word. Declared: %s'
                      % (status, ', '.join(sorted(status_words(rules)))))
    if major < 0:
        raise Refusal('the major version must be 0 or more')
    folder = kinds[kind].get('folder')
    if not folder:
        raise Refusal('the kind %s declares no folder' % kind)
    slug = slugify(title)
    if not slug:
        raise Refusal('the title "%s" gives no slug of letters or digits' % title)
    if not os.path.isdir(root):
        raise Refusal('the root %s is not a folder' % root)
    series = '%s-%s-v%d' % (kind, subproject, major)
    number = next_number(rules, root, series)
    stem = '%s-%03d-01-%s' % (series, number, slug)
    m = re.compile(rules['id-pattern']).search(stem + '.md')
    if not m or m.group(1) != series:
        raise Refusal('the file name %s.md does not match the id-pattern' % stem)
    path = os.path.join(root, subproject, folder, stem + '.md')
    if os.path.exists(path):
        raise Refusal('the file %s exists' % path)
    date = date or datetime.date.today().isoformat()
    text = render(stem, title, status, date, subproject, kinds[kind].get('template') or [])
    return path, text


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog='gaks_new.py',
        description='Write a new GAKS document from the template of its kind.')
    ap.add_argument('--rules', required=True, help='the gaks.json file')
    ap.add_argument('--root', required=True, help='the corpus root, for example arch-root')
    ap.add_argument('--kind', required=True, help='a declared kind prefix, for example ADR')
    ap.add_argument('--subproject', required=True, help='a declared subproject')
    ap.add_argument('--title', required=True, help='the title, also the source of the slug')
    ap.add_argument('--major', type=int, default=1, help='the major version (default 1)')
    ap.add_argument('--status', default='draft', help='a status word (default draft)')
    ap.add_argument('--date', default=None, help='the date, YYYY-MM-DD (default today)')
    ap.add_argument('--dry-run', action='store_true', help='print the path, write nothing')
    args = ap.parse_args(argv)
    try:
        rules = load_rules(args.rules)
        path, text = plan(rules, args.root, args.kind, args.subproject, args.title,
                          major=args.major, status=args.status, date=args.date)
    except Refusal as e:
        print('gaks_new: %s' % e, file=sys.stderr)
        return 2
    if not args.dry_run:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'x', encoding='utf-8', newline='\n') as f:
            f.write(text)
    print(path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
