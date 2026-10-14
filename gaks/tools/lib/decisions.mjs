// decisions.mjs — read the decision blocks of a Markdown text.
//
//
// As dsl/platform/gaks.edn :decision declares:
//
//   > [!decision] T1 open
//   > Which names: Jira Cloud now, or the classic names?
//   > Recommendation: Jira Cloud now.
//
// The head is `<key> open`, `<key> decided <yyyy-mm-dd> <who>` or
// `<key> withdrawn <yyyy-mm-dd> <who>`. A line that starts with a declared
// field name and a colon is a field. The other lines are the question. The
// block ends at the first line that is not a quote line. A block inside a
// fenced code block is an example and is ignored.
//
// ONE GRAMMAR, TWO PARSERS. src/gaks/decisions.clj reads the same block for
// the decision log of the active GAKS, and test/gaks/conformance_test.clj holds the two
// equal. So the grammar uses no character class whose meaning differs between
// JavaScript and Java: a space of the grammar is a space or a tab (WS), an
// indent is 0 to 3 spaces, and `.` matches any character (flag s). A
// no-break space is text. The callout name is matched in any case, and a
// foldable callout `[!decision]-` or `[!decision]+` is a decision.

import { fencedLines } from './code.mjs';

const DATE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;
const WS = '[ \\t]';

/** `s` without the spaces and tabs at its two ends. */
function trimWs(s) {
  return String(s).replace(/^[ \t]+|[ \t]+$/g, '');
}

/** The words of `s`, split at runs of spaces and tabs. */
function words(s) {
  return trimWs(s).split(/[ \t]+/).filter((t) => t !== '');
}

function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Parse a head. Returns {key, state, date, who} or {error: <reason>}.
 */
export function parseHead(rules, head) {
  const d = rules.decision;
  const tokens = words(head);
  if (tokens.length === 0) return { error: 'the head is empty' };
  const [key, state, date, ...who] = tokens;
  if (!new RegExp(d['key-pattern']).test(key)) return { error: `the key "${key}" does not match the key pattern` };
  if (state === undefined) return { error: `the head "${tokens.join(' ')}" has no state` };
  if (!d.states.includes(state)) return { error: `the state "${state}" is not a declared state` };
  if (state === 'open') {
    if (tokens.length !== 2) return { error: `an open head has only a key and a state: "${tokens.join(' ')}"` };
    return { key, state, date: null, who: null };
  }
  if (date === undefined || !DATE.test(date)) return { error: `a ${state} head needs a date yyyy-mm-dd: "${tokens.join(' ')}"` };
  if (who.length === 0) return { error: `a ${state} head needs who: "${tokens.join(' ')}"` };
  return { key, state, date, who: who.join(' ') };
}

/**
 * All decision blocks of `text`.
 *   opts.doc   the document id put into each decision
 *   opts.path  the path put into each decision
 * Returns {decisions: [{doc, key, state, date, who, question, fields, path, line}],
 *          problems: [{line, head, kind, reason}]}. `kind` is "head" for a head
 * that does not parse and "repeat" for a key seen before. `head` is the head
 * as written, with single spaces. A head that does not parse and a key
 * that repeats are problems. The first block with a key is the decision.
 */
export function parseDecisions(rules, text, { doc = null, path = null } = {}) {
  const d = rules.decision;
  const lines = String(text).split(/\r?\n/);
  const fenced = fencedLines(lines);
  const headRe = new RegExp(`^ {0,3}>${WS}*\\[!${escapeRe(d.callout)}\\][+-]?(.*)$`, 'is');
  const fieldRe = new RegExp(`^(${d.fields.map(escapeRe).join('|')})${WS}*:${WS}*(.*)$`, 's');
  const decisions = [];
  const problems = [];
  const seen = new Set();
  for (let i = 0; i < lines.length; i++) {
    if (fenced[i]) continue;
    const m = headRe.exec(lines[i]);
    if (!m) continue;
    const line = i + 1;
    const head = parseHead(rules, m[1]);
    const question = [];
    const fields = {};
    let j = i + 1;
    while (j < lines.length && /^ {0,3}>/.test(lines[j]) && !headRe.test(lines[j])) {
      const content = trimWs(lines[j].replace(/^ {0,3}>[ \t]?/, ''));
      const f = fieldRe.exec(content);
      if (f) fields[f[1]] = trimWs(f[2]);
      else if (content !== '') question.push(content);
      j++;
    }
    i = j - 1;
    const headText = words(m[1]).join(' ');
    if (head.error) {
      problems.push({ line, head: headText, kind: 'head', reason: head.error });
      continue;
    }
    if (seen.has(head.key)) {
      problems.push({ line, head: headText, kind: 'repeat', reason: `the key "${head.key}" repeats in this document` });
      continue;
    }
    seen.add(head.key);
    decisions.push({
      doc, key: head.key, state: head.state, date: head.date, who: head.who,
      question: question.join(' '), fields, path, line,
    });
  }
  return { decisions, problems };
}
