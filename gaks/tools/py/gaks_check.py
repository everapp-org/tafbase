#!/usr/bin/env python3
# gaks_check.py: check a GAKS corpus against gaks.json, in Python.
#
#
# Why this file exists. A delivered Python or Java project does not accept
# Node, and decision D3 says "keep all languages". So this checker is a
# second implementation of gaks/js/check.mjs, and the same conformance cases
# hold both.
#
#   python3 gaks_check.py --rules gaks.json --root <dir>/arch-root [--code DIR] [--json]
#
# Exit 0: no finding of a rule that is not a ratchet, and each ratchet is at
# or under its ceiling. Exit 1: else. Exit 2: a usage error.
# Python 3.9 or later, the standard library only. One file, so a bundle can
# copy it. Other code can import it: see check_corpus and main.
#
# ONE BEHAVIOUR, TWO LANGUAGES. The JavaScript checker and this checker must
# give the same JSON. JavaScript and Python differ in small ways. This file
# copies the JavaScript behaviour in each of these places:
#   - a whitespace character: the JavaScript set (see JS_WS), not str.isspace
#   - `.` in a regex: it does not match a line terminator of JavaScript
#   - `$` in a regex: the end of the text only
#   - string order: by UTF-16 code units, as Array.prototype.sort does
#   - a callout name in any case: the case rule of a JavaScript regex

import json
import os
import re
import sys

__all__ = [
    'RULES', 'RulesError', 'load_rules', 'validate_rules', 'parse_doc_id',
    'parse_frontmatter', 'find_wikilinks', 'split_link', 'fenced_lines',
    'inline_code_ranges', 'parse_decisions', 'parse_head', 'normalise_status',
    'is_known_status', 'page_state', 'read_corpus', 'scan_code',
    'find_annotations', 'walk_code', 'check_entries', 'check_corpus',
    'sort_findings', 'main',
]

USAGE = 'usage: python3 gaks_check.py --rules <gaks.json> --root <dir> [--code <dir>] [--json]'

# The rule names, in the order of the plan.
RULES = [
    'kind-undeclared',
    'id-not-filename',
    'id-duplicate',
    'status-unknown',
    'subproject-unknown',
    'decision-malformed',
    'wikilink-unresolved',
    'frontmatter-missing',
    'kind-folder',
    'code-link-unresolved',
]


class RulesError(Exception):
    """A rules file or a command line that cannot be used (exit 2)."""


# ---------------------------------------------------------------------------
# JavaScript text semantics

# The whitespace of JavaScript: `\s` in a regex, and String.prototype.trim.
JS_WS = ('\t\n\x0b\x0c\r \xa0       '
         '         　﻿')
_WS_CLASS = ('\\t\\n\\x0b\\x0c\\r \\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029'
             '\\u202f\\u205f\\u3000\\ufeff')
WS = '[' + _WS_CLASS + ']'
# `.` of JavaScript without the s flag: any character but a line terminator.
DOT = '[^\\n\\r\\u2028\\u2029]'


def js_trim(s):
    return s.strip(JS_WS)


def js_trim_end(s):
    return s.rstrip(JS_WS)


def js_key(s):
    """A sort key that orders strings as JavaScript does: by UTF-16 code units."""
    return s.encode('utf-16-be', 'surrogatepass')


def split_lines(text):
    """The lines of `text`, split at LF or CRLF, as split(/\\r?\\n/) does."""
    return re.split('\r?\n', text)


def js_regex(src, dotall=False):
    """Compile a JavaScript regex source (no u flag) to a Python pattern.

    The translation keeps the meaning of the JavaScript source. Flag ASCII
    makes \\d, \\w and \\b ASCII, as in JavaScript. \\s becomes the JavaScript
    whitespace set. `.` excludes the JavaScript line terminators. `$` is the
    end of the text. Raises re.error for a source that Python cannot read.
    """
    out = []
    i = 0
    n = len(src)
    in_class = False
    while i < n:
        c = src[i]
        if c == '\\' and i + 1 < n:
            e = src[i + 1]
            i += 2
            if e == 's':
                out.append(_WS_CLASS if in_class else WS)
            elif e == 'S':
                if in_class:
                    raise re.error('\\S in a character class is not supported')
                out.append('[^' + _WS_CLASS + ']')
            elif e == '/':
                out.append('/')
            elif e == 'k' and not in_class and i < n and src[i] == '<':
                j = src.index('>', i)
                out.append('(?P=' + src[i + 1:j] + ')')
                i = j + 1
            else:
                out.append('\\' + e)
            continue
        if in_class:
            if c == ']':
                in_class = False
                out.append(']')
            elif c in '[&~|':
                out.append('\\' + c)
            else:
                out.append(c)
            i += 1
            continue
        if c == '[':
            if src.startswith('[]', i):
                out.append('(?!)')
                i += 2
                continue
            if src.startswith('[^]', i):
                out.append('[\\s\\S]')
                i += 3
                continue
            in_class = True
            out.append('[')
            i += 1
            if i < n and src[i] == '^':
                out.append('^')
                i += 1
            continue
        if c == '.':
            out.append('.' if dotall else DOT)
        elif c == '$':
            out.append('\\Z')
        elif c == '(' and src.startswith('(?<', i) and i + 3 < n and src[i + 3] not in '=!':
            out.append('(?P<')
            i += 3
            continue
        else:
            out.append(c)
        i += 1
    flags = re.ASCII | (re.DOTALL if dotall else 0)
    return re.compile(''.join(out), flags)


def _js_canon(ch):
    """The Canonicalize of a JavaScript regex with flag i and no flag u."""
    u = ch.upper()
    if len(u) != 1:
        return ch
    if ord(ch) >= 128 and ord(u) < 128:
        return ch
    return u


_CANON_CACHE = {}


def _ci_class(ch):
    """A regex for one character, matched in any case as JavaScript does."""
    if ch in _CANON_CACHE:
        return _CANON_CACHE[ch]
    if 'a' <= ch.lower() <= 'z' and ch.isascii():
        r = '[' + ch.lower() + ch.upper() + ']'
    else:
        target = _js_canon(ch)
        same = [chr(x) for x in range(0x10000)
                if not 0xD800 <= x <= 0xDFFF and _js_canon(chr(x)) == target]
        if ch not in same:
            same.append(ch)
        r = '[' + ''.join(re.escape(x) for x in same) + ']' if len(same) > 1 else re.escape(ch)
    _CANON_CACHE[ch] = r
    return r


# ---------------------------------------------------------------------------
# Rules (gaks.json)

def _is_int(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, int):
        return True
    return isinstance(v, float) and v.is_integer()


def _js_object_keys(d):
    """The keys of a JSON object in the order of Object.entries: array-index keys first."""
    def is_index(k):
        return k.isdigit() and (k == '0' or k[0] != '0') and int(k) < 4294967295
    idx = sorted((k for k in d if is_index(k)), key=int)
    return idx + [k for k in d if not is_index(k)]


def _is_object(v):
    """typeof v === 'object' in JavaScript (null and a list are objects)."""
    return v is None or isinstance(v, (dict, list))


def validate_rules(rules):
    """Check the shape of a parsed rules object. Returns it, or raises RulesError."""
    problems = []
    if not isinstance(rules, dict):
        raise RulesError('the rules are not a JSON object')
    pat = rules.get('id-pattern')
    if not isinstance(pat, str):
        problems.append('"id-pattern" is not a string')
    else:
        try:
            js_regex(pat)
        except (re.error, ValueError) as e:
            problems.append('"id-pattern" is not a regex: %s' % e)
    kinds = rules.get('kinds')
    if not isinstance(kinds, list) or any(
            not isinstance(k, dict) or not isinstance(k.get('prefix'), str) for k in kinds):
        problems.append('"kinds" is not a list of {prefix, ...}')
    if not isinstance(rules.get('subprojects'), list):
        problems.append('"subprojects" is not a list')
    ps = rules.get('page-states')
    if not isinstance(ps, dict) or 'words' not in ps or not _is_object(ps.get('words')):
        problems.append('"page-states" has no "words"')
    if 'statuses' in rules and not _is_object(rules['statuses']):
        problems.append('"statuses" is not an object')
    d = rules.get('decision')
    if (not isinstance(d, dict) or not isinstance(d.get('callout'), str)
            or not isinstance(d.get('states'), list) or not isinstance(d.get('fields'), list)
            or not isinstance(d.get('key-pattern'), str)):
        problems.append('"decision" needs "callout", "states", "fields" and "key-pattern"')
    if 'collisions' in rules and not isinstance(rules['collisions'], list):
        problems.append('"collisions" is not a list')
    if 'ratchets' in rules:
        rt = rules['ratchets']
        if not isinstance(rt, dict) or any(not _is_int(v) for v in rt.values()):
            problems.append('"ratchets" is not a map of integers')
        elif rt:
            # A ceiling for a name that is no rule changes nothing, and nothing says so.
            unknown = [k for k in _js_object_keys(rt) if k not in RULES]
            if unknown:
                problems.append('"ratchets" names no rule: %s. The rules: %s'
                                % (', '.join(unknown), ', '.join(RULES)))
    if 'code' in rules:
        c = rules['code']
        if (not isinstance(c, dict) or not isinstance(c.get('extensions'), list)
                or not isinstance(c.get('annotation-pattern'), str)
                or ('skip-dirs' in c and not isinstance(c['skip-dirs'], list))):
            problems.append('"code" needs "extensions", "skip-dirs" and "annotation-pattern"')
        else:
            try:
                js_regex(c['annotation-pattern'])
            except (re.error, ValueError) as e:
                problems.append('"code" "annotation-pattern" is not a regex: %s' % e)
    if problems:
        raise RulesError('; '.join(problems))
    return rules


def load_rules(path):
    """Read and check a gaks.json file. Raises RulesError on any problem."""
    try:
        with open(path, 'rb') as f:
            text = f.read().decode('utf-8', 'replace')
    except OSError as e:
        raise RulesError('cannot read %s: %s' % (path, e.strerror or e))
    if text.startswith('﻿'):
        raise RulesError('%s is not JSON: a byte order mark' % path)
    try:
        rules = json.loads(text)
    except ValueError as e:
        raise RulesError('%s is not JSON: %s' % (path, e))
    return validate_rules(rules)


_REGEX_CACHE = {}


def _rx(src, dotall=False):
    key = (src, dotall)
    r = _REGEX_CACHE.get(key)
    if r is None:
        r = _REGEX_CACHE[key] = js_regex(src, dotall)
    return r


def parse_doc_id(rules, file_name):
    """The id of a file name by the id pattern, or None.

    Returns {series, number, revision, id, prefix}. `id` is the unique key:
    the series, the number and the revision. `prefix` is the kind.
    """
    m = _rx(rules['id-pattern']).search(file_name)
    if not m:
        return None
    g = list(m.groups()) + [None] * 3
    series, number, revision = g[0], g[1], g[2]

    def s(v):
        return 'undefined' if v is None else v
    return {'series': series, 'number': number, 'revision': revision,
            'id': '%s-%s-%s' % (s(series), s(number), s(revision)),
            'prefix': s(series).split('-')[0]}


# ---------------------------------------------------------------------------
# Frontmatter

def unquote(s):
    """Remove one pair of matching quotes. A double-quoted string keeps \\" and \\\\."""
    t = js_trim(str(s))
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return re.sub(r'\\(["\\])', r'\1', t[1:-1])
    if len(t) >= 2 and t[0] == "'" and t[-1] == "'":
        return t[1:-1].replace("''", "'")
    return t


_COMMENT_TAIL = re.compile(WS + '+#' + DOT + '*\\Z')


def _scalar(raw):
    t = js_trim(raw)
    if t == '' or t == '~' or t == 'null':
        return None
    if t[0] != '"' and t[0] != "'":
        t = js_trim(_COMMENT_TAIL.sub('', t, count=1))
        if t.startswith('[') and t.endswith(']') and not t.startswith('[['):
            inner = js_trim(t[1:-1])
            return [] if inner == '' else [unquote(x) for x in inner.split(',')]
    return unquote(t)


_FM_COMMENT = re.compile('^' + WS + '*#')
_FM_ITEM = re.compile('^' + WS + '*-' + WS + '+(' + DOT + '*)\\Z')
_FM_KV = re.compile('^([A-Za-z0-9_][A-Za-z0-9_.-]*)' + WS + '*:(?:' + WS + '+(' + DOT + '*)|'
                    + WS + '*)\\Z')
_LEADING_WS = re.compile('^' + WS)


def parse_frontmatter(text):
    """Parse the leading `---` block of `text`.

    Returns {present, data, body, bodyLine, endLine}, as frontmatter.mjs does.
    This is not a YAML parser. It reads scalar `key: value` lines, quoted
    strings, and `- item` lists under a `key:` line. It never raises.
    """
    src = text if isinstance(text, str) else ''
    if src.startswith('﻿'):
        src = src[1:]
    none = {'present': False, 'data': {}, 'body': src, 'bodyLine': 1, 'endLine': 0}
    lines = split_lines(src)
    if js_trim(lines[0]) != '---':
        return none
    end = -1
    for i in range(1, len(lines)):
        ln = js_trim_end(lines[i])
        if ln == '---' or ln == '...':
            end = i
            break
    if end < 0:
        return none
    data = {}
    list_key = None
    for i in range(1, end):
        line = lines[i]
        if js_trim(line) == '' or _FM_COMMENT.search(line):
            continue
        item = _FM_ITEM.search(line)
        if item and list_key is not None:
            if not isinstance(data.get(list_key), list):
                data[list_key] = []
            data[list_key].append(unquote(item.group(1)))
            continue
        kv = _FM_KV.search(line)
        if kv and not _LEADING_WS.search(line):
            key = kv.group(1)
            v = kv.group(2) if kv.group(2) is not None else ''
            if js_trim(v) == '':
                data[key] = None
                list_key = key
            else:
                data[key] = _scalar(v)
                list_key = None
            continue
        # An indented line that is not a list item: skipped, and the open
        # list stays open.
    return {'present': True, 'data': data, 'body': '\n'.join(lines[end + 1:]),
            'bodyLine': end + 2, 'endLine': end + 1}


# ---------------------------------------------------------------------------
# Code in Markdown

_FENCE_OPEN = re.compile('^ {0,3}(`{3,}|~{3,})(.*)\\Z', re.S)
_FENCE_CLOSE = re.compile('^ {0,3}(`{3,}|~{3,})[ \\t]*\\Z')
_TICKS = re.compile('`+')


def fenced_lines(lines):
    """For each line, True when it is inside a fenced code block (fences included)."""
    out = [False] * len(lines)
    fence = None
    for i, ln in enumerate(lines):
        if fence is None:
            m = _FENCE_OPEN.search(ln)
            if m and not (m.group(1)[0] == '`' and '`' in m.group(2)):
                fence = (m.group(1)[0], len(m.group(1)))
                out[i] = True
        else:
            out[i] = True
            m = _FENCE_CLOSE.search(ln)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
                fence = None
    return out


def inline_code_ranges(line):
    """The [start, end) ranges of the inline code spans of one line."""
    runs = [(m.start(), len(m.group(0))) for m in _TICKS.finditer(line)]
    ranges = []
    i = 0
    while i < len(runs):
        j = i + 1
        while j < len(runs) and runs[j][1] != runs[i][1]:
            j += 1
        if j < len(runs):
            ranges.append((runs[i][0], runs[j][0] + runs[j][1]))
            i = j + 1
        else:
            i += 1
    return ranges


def _in_ranges(ranges, index):
    return any(a <= index < b for a, b in ranges)


# ---------------------------------------------------------------------------
# Wikilinks

_LINK = re.compile(r'(!?)\[\[([^\[\]\n]*?)\]\]')
_HEADING_MARK = re.compile('[#^]')


def split_link(inner):
    """Split the inside of [[...]] into {target, heading, alias}."""
    s = str(inner)
    alias = None
    bar = s.find('|')
    if bar >= 0:
        alias = js_trim(s[bar + 1:])
        s = s[:bar]
        if s.endswith('\\'):
            s = s[:-1]
    heading = None
    m = _HEADING_MARK.search(s)
    if m:
        heading = js_trim(s[m.start() + 1:])
        s = s[:m.start()]
    return {'target': js_trim(s), 'heading': heading, 'alias': alias}


def find_wikilinks(text, first_line=1):
    """All wikilinks of `text` outside code: [{raw, target, heading, alias, embed, line}]."""
    lines = split_lines(str(text))
    fenced = fenced_lines(lines)
    out = []
    for i, line in enumerate(lines):
        if fenced[i] or '[[' not in line:
            continue
        code = inline_code_ranges(line)
        for m in _LINK.finditer(line):
            if _in_ranges(code, m.start()):
                continue
            link = split_link(m.group(2))
            link.update({'raw': m.group(0), 'embed': m.group(1) == '!', 'line': first_line + i})
            out.append(link)
    return out


def target_name(target):
    """The last segment of a target, without a `.md` extension."""
    seg = js_trim(str(target).split('/')[-1])
    return seg[:-3] if seg.lower().endswith('.md') else seg


def make_resolver(stems=(), ids=(), files=()):
    """A function target -> True when the target names a stem, an id or a file."""
    names = set(stems) | set(ids)
    others = set(files)

    def resolve(target):
        t = js_trim(str(target))
        if t == '':
            return True
        seg = js_trim(t.split('/')[-1])
        return target_name(t) in names or seg in others
    return resolve


# ---------------------------------------------------------------------------
# Status words

def normalise_status(status):
    if status is None:
        return None
    t = js_trim(str(status))
    if t == '':
        return None
    return re.sub('[' + _WS_CLASS + '_]+', '-', t.lower())


def is_pipe_list(status):
    return status is not None and '|' in str(status)


_TABLES = {}


def _tables(rules):
    hit = _TABLES.get(id(rules))
    if hit is not None and hit[0] is rules:
        return hit[1]
    ps = rules.get('page-states') or {}
    words = ps.get('words') or {}
    word_state = {}
    if isinstance(words, dict):
        for state in _js_object_keys(words):
            for w in words[state] or []:
                n = normalise_status(w)
                if n is not None:
                    word_state[n] = state
    known = set(word_state)
    st = rules.get('statuses') or {}
    if isinstance(st, dict):
        for w in list(st.get('editable') or []) + list(st.get('frozen') or []):
            n = normalise_status(w)
            if n is not None:
                known.add(n)
    pw = ps.get('prefix-words') or {}
    prefixes = []
    for p in _js_object_keys(pw) if isinstance(pw, dict) else []:
        n = normalise_status(p)
        if n is not None:
            prefixes.append((n, pw[p]))
    t = (word_state, known, prefixes)
    _TABLES[id(rules)] = (rules, t)
    return t


def page_state(rules, status):
    """The page state of a raw status, or None."""
    n = normalise_status(status)
    if n is None or is_pipe_list(status):
        return None
    word_state, _, prefixes = _tables(rules)
    if n in word_state:
        return word_state[n]
    for p, state in prefixes:
        if n == p or n.startswith(p + '-'):
            return state
    return None


def is_known_status(rules, status):
    """Is the raw status a declared word, or does it start with a prefix word?"""
    n = normalise_status(status)
    if n is None or is_pipe_list(status):
        return False
    _, known, prefixes = _tables(rules)
    if n in known:
        return True
    return any(n == p or n.startswith(p + '-') for p, _ in prefixes)


# ---------------------------------------------------------------------------
# Decision blocks

_DATE = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}\\Z')
_QUOTE = re.compile('^ {0,3}>')
_QUOTE_PREFIX = re.compile('^ {0,3}>[ \\t]?')


def _trim_ws(s):
    return str(s).strip(' \t')


def _words(s):
    return [t for t in re.split('[ \t]+', _trim_ws(s)) if t != '']


def parse_head(rules, head):
    """Parse a head. Returns {key, state, date, who} or {error: <reason>}."""
    d = rules['decision']
    tokens = _words(head)
    if not tokens:
        return {'error': 'the head is empty'}
    key = tokens[0]
    state = tokens[1] if len(tokens) > 1 else None
    date = tokens[2] if len(tokens) > 2 else None
    who = tokens[3:]
    joined = ' '.join(tokens)
    if not _rx(d['key-pattern']).search(key):
        return {'error': 'the key "%s" does not match the key pattern' % key}
    if state is None:
        return {'error': 'the head "%s" has no state' % joined}
    if state not in d['states']:
        return {'error': 'the state "%s" is not a declared state' % state}
    if state == 'open':
        if len(tokens) != 2:
            return {'error': 'an open head has only a key and a state: "%s"' % joined}
        return {'key': key, 'state': state, 'date': None, 'who': None}
    if date is None or not _DATE.search(date):
        return {'error': 'a %s head needs a date yyyy-mm-dd: "%s"' % (state, joined)}
    if not who:
        return {'error': 'a %s head needs who: "%s"' % (state, joined)}
    return {'key': key, 'state': state, 'date': date, 'who': ' '.join(who)}


def _decision_regexes(rules):
    d = rules['decision']
    key = ('\0decision', d['callout'], tuple(d['fields']))
    r = _REGEX_CACHE.get(key)
    if r is None:
        callout = ''.join(_ci_class(ch) for ch in d['callout'])
        head = re.compile('^ {0,3}>[ \\t]*\\[!' + callout + '\\][+-]?(.*)\\Z', re.S)
        field = re.compile('^(' + '|'.join(re.escape(f) for f in d['fields'])
                           + ')[ \\t]*:[ \\t]*(.*)\\Z', re.S)
        r = _REGEX_CACHE[key] = (head, field)
    return r


def parse_decisions(rules, text, doc=None, path=None):
    """All decision blocks of `text`.

    Returns {decisions: [{doc, key, state, date, who, question, fields, path,
    line}], problems: [{line, head, kind, reason}]}, as decisions.mjs does.
    """
    head_re, field_re = _decision_regexes(rules)
    lines = split_lines(str(text))
    fenced = fenced_lines(lines)
    decisions = []
    problems = []
    seen = set()
    i = 0
    while i < len(lines):
        if fenced[i]:
            i += 1
            continue
        m = head_re.search(lines[i])
        if not m:
            i += 1
            continue
        line = i + 1
        head = parse_head(rules, m.group(1))
        question = []
        fields = {}
        j = i + 1
        while j < len(lines) and _QUOTE.search(lines[j]) and not head_re.search(lines[j]):
            content = _trim_ws(_QUOTE_PREFIX.sub('', lines[j], count=1))
            f = field_re.search(content)
            if f:
                fields[f.group(1)] = _trim_ws(f.group(2))
            elif content != '':
                question.append(content)
            j += 1
        i = j
        head_text = ' '.join(_words(m.group(1)))
        if 'error' in head:
            problems.append({'line': line, 'head': head_text, 'kind': 'head',
                             'reason': head['error']})
            continue
        if head['key'] in seen:
            problems.append({'line': line, 'head': head_text, 'kind': 'repeat',
                             'reason': 'the key "%s" repeats in this document' % head['key']})
            continue
        seen.add(head['key'])
        decisions.append({'doc': doc, 'key': head['key'], 'state': head['state'],
                          'date': head['date'], 'who': head['who'],
                          'question': ' '.join(question), 'fields': fields,
                          'path': path, 'line': line})
    return {'decisions': decisions, 'problems': problems}


def decision_detail(problem):
    """The detail of a decision-malformed finding: `line <n>: <head>`."""
    base = 'line %d: %s' % (problem['line'], problem['head'])
    return base + ' (the key repeats)' if problem['kind'] == 'repeat' else base


# ---------------------------------------------------------------------------
# The corpus on disk

def _display_name(name):
    """A file name as Node gives it: the bytes decoded as UTF-8, with U+FFFD."""
    try:
        name.encode('utf-8')
        return name
    except UnicodeEncodeError:
        return name.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')


def _read_text(path):
    with open(path, 'rb') as f:
        return f.read().decode('utf-8', 'replace')


def _walk(root, accept_dir, accept_file):
    """Every file under `root` as sorted (posix relative path, path on disk) pairs.

    A symbolic link is neither a file nor a directory, as for a Node Dirent.
    """
    out = []

    def visit(abs_dir, rel):
        try:
            with os.scandir(abs_dir) as it:
                entries = list(it)
        except OSError:
            return
        for e in entries:
            name = _display_name(e.name)
            r = rel + '/' + name if rel else name
            try:
                is_dir = e.is_dir(follow_symlinks=False)
                is_file = e.is_file(follow_symlinks=False)
            except OSError:
                continue
            if is_dir:
                if accept_dir(name):
                    visit(e.path, r)
            elif is_file and accept_file(name):
                out.append((r, e.path))
    visit(root, '')
    out.sort(key=lambda p: js_key(p[0]))
    return out


def walk(root):
    """Every file under `root`, as sorted posix paths. A name with a leading dot is skipped."""
    def ok(name):
        return not name.startswith('.') and name != 'node_modules'
    return _walk(root, ok, ok)


def _str(v):
    if v is None:
        return None
    if isinstance(v, list):
        return ', '.join(v)
    return str(v)


def read_entry(rules, rel, abs_path):
    """Read one .md file. Returns a dict with the keys of corpus.mjs readEntry that the checker uses."""
    text = _read_text(abs_path)
    name = rel.split('/')[-1]
    stem = name[:-3]
    parsed = parse_doc_id(rules, name)
    fm = parse_frontmatter(text)
    data = fm['data']
    return {
        'path': rel,
        'stem': stem,
        'isDocument': parsed is not None,
        'docId': parsed['id'] if parsed else None,
        'prefix': parsed['prefix'] if parsed else None,
        'frontmatter': data,
        'hasFrontmatter': fm['present'],
        'id': _str(data.get('id')),
        'status': _str(data.get('status')),
        'subproject': _str(data.get('subproject')),
        'text': text,
        'wikilinks': find_wikilinks(text, 1),
    }


def read_corpus(rules, root):
    """Read the corpus under `root`. Returns {root, entries, files, resolve}."""
    all_files = walk(root)
    md = [p for p in all_files if p[0].lower().endswith('.md')]
    files = [p[0] for p in all_files if not p[0].lower().endswith('.md')]
    entries = [read_entry(rules, rel, ab) for rel, ab in md]
    resolve = make_resolver(stems=[e['stem'] for e in entries],
                            ids=[e['id'] for e in entries if e['id']],
                            files=[p.split('/')[-1] for p in files])
    return {'root': root, 'entries': entries, 'files': files, 'resolve': resolve}


# ---------------------------------------------------------------------------
# Links from source code

def extension_of(name):
    """The extension of a file name: the text from its last dot, or ''."""
    i = name.rfind('.')
    return '' if i <= 0 else name[i:]


def walk_code(code, root):
    """Every source file under `root`, as sorted (posix relative path, path on disk) pairs."""
    exts = set(code['extensions'])
    skip = set(code.get('skip-dirs') or [])
    return _walk(root,
                 lambda name: not name.startswith('.') and name not in skip,
                 lambda name: extension_of(name) in exts)


def find_annotations(code, text):
    """The annotations of one text: [{line, tag, target}], `line` 1-based."""
    pat = _rx(code['annotation-pattern'])
    out = []
    for i, line in enumerate(split_lines(str(text))):
        for m in pat.finditer(line):
            out.append({'line': i + 1, 'tag': m.group(1), 'target': m.group(2)})
    return out


def scan_code(code, root):
    """Every annotation of every source file under `root`: [{path, line, tag, target}]."""
    out = []
    for rel, ab in walk_code(code, root):
        for a in find_annotations(code, _read_text(ab)):
            a['path'] = rel
            out.append(a)
    return out


# ---------------------------------------------------------------------------
# The check

def sort_findings(findings):
    """Sort findings by rule, then path, then detail, in JavaScript string order."""
    return sorted(findings, key=lambda f: (js_key(f['rule']), js_key(f['path']),
                                           js_key(f['detail'])))


_UNDEFINED = object()


def _js_str(v):
    """A value as a JavaScript template string gives it."""
    if v is _UNDEFINED:
        return 'undefined'
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, str):
        return v
    return json.dumps(v)


def check_entries(rules, corpus, annotations=None):
    """Check a corpus that is already read.

    `annotations` is the list of scan_code, or None when no --code is given.
    Returns {findings, counts, decisions, ratchets, exitCode}, as check.mjs does.
    """
    findings = []

    def add(rule, path, detail):
        findings.append({'rule': rule, 'path': path, 'detail': detail})

    kinds = set(k['prefix'] for k in rules['kinds'])
    # A document is in the wrong folder only when its parent folder belongs
    # to another declared kind. Other folders (notes, archive) are free. As
    # in a JavaScript Map, the last kind with a prefix gives its folder.
    own_folder = {}
    for k in rules['kinds']:
        own_folder[k['prefix']] = k.get('folder', _UNDEFINED)
    folders = set(k['folder'] for k in rules['kinds']
                  if isinstance(k.get('folder'), str) and k['folder'] != '')
    subprojects = set(rules['subprojects'])
    listed = set(c.get('id') for c in (rules.get('collisions') or []) if isinstance(c, dict))
    by_id = {}
    decisions = []

    for e in corpus['entries']:
        if e['isDocument']:
            if e['prefix'] not in kinds:
                add('kind-undeclared', e['path'], e['prefix'])
            if e['id'] is not None and js_trim(e['id']) != '' and js_trim(e['id']) != e['stem']:
                add('id-not-filename', e['path'], e['id'])
            by_id.setdefault(e['docId'], []).append(e['path'])
            if (e['status'] is not None and js_trim(e['status']) != ''
                    and not is_known_status(rules, e['status'])):
                add('status-unknown', e['path'], e['status'])
            sp = e['subproject']
            if sp is not None and js_trim(sp) != '' and (is_pipe_list(sp) or js_trim(sp) not in subprojects):
                add('subproject-unknown', e['path'], sp)
            if not e['hasFrontmatter']:
                add('frontmatter-missing', e['path'], 'no frontmatter')
            parts = e['path'].split('/')
            parent = parts[-2] if len(parts) > 1 else None
            own = own_folder.get(e['prefix'], _UNDEFINED)
            if e['prefix'] in kinds and parent is not None and parent in folders and parent != own:
                add('kind-folder', e['path'], '%s in %s, declared %s' % (e['prefix'], parent, _js_str(own)))
        r = parse_decisions(rules, e['text'], doc=e['stem'], path=e['path'])
        decisions.extend(r['decisions'])
        for p in r['problems']:
            add('decision-malformed', e['path'], decision_detail(p))
        for w in e['wikilinks']:
            if not corpus['resolve'](w['target']):
                add('wikilink-unresolved', e['path'], w['target'])
    for doc_id, paths in by_id.items():
        if len(paths) > 1 and doc_id not in listed:
            for p in paths:
                add('id-duplicate', p, doc_id)

    if annotations is not None:
        names = set()
        for e in corpus['entries']:
            if e['isDocument']:
                names.add(e['stem'])
                names.add(e['docId'])
        for a in annotations:
            if a['target'] not in names:
                add('code-link-unresolved', a['path'], 'line %d: %s' % (a['line'], a['target']))

    counts = dict((r, 0) for r in RULES)
    for f in findings:
        counts[f['rule']] = counts.get(f['rule'], 0) + 1
    ceilings = rules.get('ratchets') or {}
    ratchets = {}
    for rule in _js_object_keys(ceilings):
        ceiling = int(ceilings[rule])
        count = counts.get(rule, 0)
        ratchets[rule] = {'count': count, 'ceiling': ceiling, 'over': count > ceiling}
    hard = any(r not in ceilings and counts[r] > 0 for r in RULES)
    over = any(r['over'] for r in ratchets.values())
    return {'findings': sort_findings(findings), 'counts': counts, 'decisions': decisions,
            'ratchets': ratchets, 'exitCode': 1 if hard or over else 0}


def check_corpus(rules, root, code_dir=None):
    """Read the corpus under `root` (and the code under `code_dir`) and check it."""
    annotations = None
    if code_dir is not None:
        annotations = scan_code(rules['code'], code_dir)
    return check_entries(rules, read_corpus(rules, root), annotations)


# ---------------------------------------------------------------------------
# The command line

def parse_args(argv):
    opts = {'rules': None, 'root': None, 'code': None, 'json': False, 'help': False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--json':
            opts['json'] = True
        elif a in ('--help', '-h'):
            opts['help'] = True
        elif a in ('--rules', '--root', '--code'):
            v = argv[i + 1] if i + 1 < len(argv) else None
            if v is None or v.startswith('--'):
                raise RulesError('%s needs a value' % a)
            opts[a[2:]] = v
            i += 1
        else:
            raise RulesError('unknown argument: %s' % a)
        i += 1
    return opts


def to_json(result):
    """The --json text: the same text as JSON.stringify(x, null, 2) gives."""
    return json.dumps({'findings': result['findings'], 'counts': result['counts']},
                      indent=2, ensure_ascii=False) + '\n'


def main(argv, out=None, err=None):
    """Run the checker on the arguments `argv` (no program name). Returns the exit code."""
    out = out or sys.stdout
    err = err or sys.stderr
    try:
        opts = parse_args(argv)
        if opts['help']:
            out.write(USAGE + '\n')
            return 0
        if not opts['rules'] or not opts['root']:
            raise RulesError('--rules and --root are both needed')
        if not os.path.isdir(opts['root']):
            raise RulesError('--root %s is not a directory' % opts['root'])
        if opts['code'] is not None and not os.path.isdir(opts['code']):
            raise RulesError('--code %s is not a directory' % opts['code'])
        rules = load_rules(opts['rules'])
        if opts['code'] is not None and 'code' not in rules:
            raise RulesError('%s has no "code" key, and --code needs it' % opts['rules'])
    except RulesError as e:
        err.write('check: %s\n%s\n' % (e, USAGE))
        return 2
    r = check_corpus(rules, opts['root'], opts['code'])
    if opts['json']:
        out.write(to_json(r))
    else:
        for f in r['findings']:
            out.write('%s  %s  %s\n' % (f['rule'], f['path'], f['detail']))
        for rule in RULES:
            rt = r['ratchets'].get(rule)
            tail = ''
            if rt:
                tail = '  (ratchet, ceiling %d%s)' % (rt['ceiling'], ', OVER' if rt['over'] else '')
            out.write('%s: %d%s\n' % (rule, r['counts'][rule], tail))
    return r['exitCode']


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='backslashreplace', newline='\n')
        except (AttributeError, ValueError):
            pass
    sys.exit(main(sys.argv[1:]))
