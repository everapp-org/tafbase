#!/usr/bin/env python3
# gaks_rules.py: make gaks.json of a project from its declaration, in Python.
#
#
# Why this file exists. A delivered Python or Java project declares its kinds,
# its subprojects and its ceilings in one JSON file, gaks.project.json, in its
# own repository. No tool of such a project reads EDN, so the declaration is
# JSON. This tool makes gaks.json from that file and from gaks.base.json, the
# file of what every project takes from the active GAKS. So the project
# changes a kind and makes its rules again with Python 3.9 and nothing else.
#
#   python3 gaks_rules.py --project gaks.project.json [--base FILE] [--out FILE]
#
# --base   the default is gaks.base.json in the folder above this file, where
#          a bundle holds it (tools/gaks.base.json).
# --out    the default is gaks.json in the current folder. "-" is stdout.
#
# A declaration:
#
#   {"name": "Shop",
#    "subprojects": ["shop"],
#    "kinds": ["ADR", "PLAN", "F",
#              {"prefix": "RUNBOOK", "name": "Runbook", "folder": "runbooks",
#               "template": ["Purpose", "Steps"]}],
#    "ratchets": {}}
#
# "kinds": a string takes the kind of the base. An object is a new kind of the
# project. With no "kinds", the project gets every kind of the base.
# "ratchets": a ceiling for a rule. Each rule with no ceiling is a hard rule.
#
# This is the function project-from-base of the generator of the active GAKS,
# in a second language. A parity test holds the two to the same bytes. Change
# both, or neither.
#
# Exit 0: gaks.json is written. Exit 2: a file or a declaration that cannot be
# used, with the reason on stderr. Nobody edits gaks.json by hand.

import json
import os
import re
import sys

__all__ = ['RefusedError', 'project_rules', 'dumps', 'main']

USAGE = 'usage: python3 gaks_rules.py --project <gaks.project.json> [--base <gaks.base.json>] [--out <gaks.json>]'

KIND_PREFIX = re.compile(r'[A-Z]+\Z')
SUBPROJECT = re.compile(r'[a-z0-9][a-z0-9-]*\Z')


class RefusedError(Exception):
    """A declaration or a file that cannot be used (exit 2)."""


def _compact(v):
    """A value as one line of JSON, for a message."""
    return json.dumps(v, ensure_ascii=False, separators=(',', ':'))


def _is_whole_number(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _kind(by_prefix, entry):
    """One entry of "kinds" of a project, as a kind of gaks.json."""
    if isinstance(entry, str):
        if entry not in by_prefix:
            raise RefusedError(
                'the kind %s is not a kind of the base. Declared: %s. Write an object with '
                '"prefix", "name" and "folder" for a new kind'
                % (_compact(entry), ', '.join(sorted(by_prefix))))
        return by_prefix[entry]
    if isinstance(entry, dict):
        prefix, folder, template = entry.get('prefix'), entry.get('folder'), entry.get('template')
        if not isinstance(prefix, str) or not KIND_PREFIX.match(prefix):
            raise RefusedError('a new kind needs "prefix", capital letters A to Z only, with no digit: %s'
                               % _compact(entry))
        if not isinstance(folder, str) or not folder:
            raise RefusedError('the kind %s needs "folder": %s' % (prefix, _compact(entry)))
        if template is not None and not (isinstance(template, list)
                                         and all(isinstance(h, str) for h in template)):
            raise RefusedError('the "template" of the kind %s is not a list of headings' % prefix)
        name = entry.get('name')
        kind = {'prefix': prefix, 'name': name if isinstance(name, str) else prefix, 'folder': folder}
        if template:
            kind['template'] = list(template)
        return kind
    raise RefusedError('a kind is a prefix string or an object, not %s' % _compact(entry))


def project_rules(base, project):
    """The gaks.json object of a project, from the base and its declaration.

    Raises RefusedError for a declaration that cannot be used.
    """
    if not isinstance(project, dict):
        raise RefusedError('the declaration is not a JSON object')
    name = project.get('name')
    if not isinstance(name, str) or not name.strip():
        raise RefusedError('the project needs "name", a string')
    if 'subprojects' not in project:
        raise RefusedError('the project needs "subprojects", a list of words, for example ["shop"]')
    subs = project['subprojects']
    if not (isinstance(subs, list) and subs
            and all(isinstance(s, str) and SUBPROJECT.match(s) for s in subs)):
        raise RefusedError('"subprojects" is not a list of lower case words: %s' % _compact(subs))
    kinds = project.get('kinds')
    if 'kinds' in project and not (isinstance(kinds, list) and kinds):
        raise RefusedError('"kinds" is not a list. Omit it to get the core kinds')
    ratchets = project.get('ratchets')
    if ratchets is not None and not (isinstance(ratchets, dict)
                                     and all(_is_whole_number(v) for v in ratchets.values())):
        raise RefusedError('"ratchets" is not a map of rule names to whole numbers: %s' % _compact(ratchets))
    ratchets = ratchets or {}
    rules = base['rules']
    unknown = sorted(k for k in ratchets if k not in rules)
    if unknown:
        raise RefusedError('a ratchet names no rule: %s. The rules: %s'
                           % (', '.join(unknown), ', '.join(rules)))
    by_prefix = dict((k['prefix'], k) for k in base['kinds'])
    chosen = [_kind(by_prefix, e) for e in kinds] if 'kinds' in project else list(base['kinds'])
    seen, dupes = set(), set()
    for k in chosen:
        (dupes if k['prefix'] in seen else seen).add(k['prefix'])
    if dupes:
        raise RefusedError('the kinds name a prefix twice: %s' % ', '.join(sorted(dupes)))
    ceilings = dict(base['ratchets'])
    ceilings.update(ratchets)
    out = {'project': name.strip()}
    for key in ('gaks-version', 'root', 'id-pattern'):
        out[key] = base[key]
    out['collisions'] = []
    out['kinds'] = chosen
    out['subprojects'] = sorted(set(subs))
    for key in ('statuses', 'page-states', 'decision', 'code'):
        out[key] = base[key]
    out['ratchets'] = dict((k, ceilings[k]) for k in sorted(ceilings))
    return out


def dumps(value, level=0):
    """`value` as JSON text, in the layout of the generator of the active GAKS.

    An object has one key on each line, with " : " after the key. A list is on
    one line. So the two generators write the same bytes for the same rules.
    """
    if isinstance(value, dict):
        if not value:
            return '{ }'
        pad = '  ' * (level + 1)
        body = ',\n'.join('%s%s : %s' % (pad, json.dumps(k, ensure_ascii=False), dumps(v, level + 1))
                          for k, v in value.items())
        return '{\n%s\n%s}' % (body, '  ' * level)
    if isinstance(value, list):
        if not value:
            return '[ ]'
        return '[ %s ]' % ', '.join(dumps(v, level) for v in value)
    return json.dumps(value, ensure_ascii=False)


def _read_json(path, what):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except OSError as e:
        raise RefusedError('cannot read %s %s: %s' % (what, path, e.strerror or e))
    except ValueError as e:
        raise RefusedError('%s %s is not JSON: %s' % (what, path, e))


def _read_base(path):
    base = _read_json(path, 'the base')
    need = ('gaks-version', 'root', 'id-pattern', 'kinds', 'statuses', 'page-states',
            'decision', 'code', 'rules', 'ratchets')
    if not isinstance(base, dict) or any(k not in base for k in need):
        raise RefusedError('%s is not a gaks.base.json: it needs %s' % (path, ', '.join(need)))
    return base


def main(argv=None, stdout=None, stderr=None):
    argv = sys.argv[1:] if argv is None else argv
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    here = os.path.dirname(os.path.abspath(__file__))
    opts = {'--project': None, '--base': os.path.join(os.path.dirname(here), 'gaks.base.json'),
            '--out': 'gaks.json'}
    if argv in (['--help'], ['-h']):
        stdout.write(USAGE + '\n')
        return 0
    i = 0
    while i < len(argv):
        if argv[i] not in opts or i + 1 >= len(argv):
            stderr.write('gaks_rules: unknown or incomplete option %s\n%s\n' % (argv[i], USAGE))
            return 2
        opts[argv[i]] = argv[i + 1]
        i += 2
    if not opts['--project']:
        stderr.write(USAGE + '\n')
        return 2
    try:
        rules = project_rules(_read_base(opts['--base']), _read_json(opts['--project'], 'the declaration'))
    except RefusedError as e:
        stderr.write('gaks_rules: REFUSED: %s\n%s\n' % (e, USAGE))
        return 2
    text = dumps(rules) + '\n'
    if opts['--out'] == '-':
        stdout.write(text)
        return 0
    with open(opts['--out'], 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    stderr.write('gaks.json: %d kinds, project %s -> %s\n'
                 % (len(rules['kinds']), rules['project'], opts['--out']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
