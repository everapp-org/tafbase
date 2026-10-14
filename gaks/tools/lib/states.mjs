// states.mjs — a status word, and the page state it belongs to.
//
//
// case, and each run of whitespace or underscores becomes one hyphen. Both
// sides of a match are normalised, so `In Progress` and `in-progress` are one
// word. A value with a `|` is a list of words, not a status, so it is unknown.

/** A raw status → its normal form, or null when it is absent or blank. */
export function normaliseStatus(status) {
  if (status === null || status === undefined) return null;
  const t = String(status).trim();
  if (t === '') return null;
  return t.toLowerCase().replace(/[\s_]+/g, '-');
}

/** Does the field hold a list of words (`a | b`) instead of one value? */
export function isPipeList(status) {
  return status !== null && status !== undefined && String(status).includes('|');
}

/** The lookup tables of a rules object, built once per rules object. */
const cache = new WeakMap();
function tables(rules) {
  let t = cache.get(rules);
  if (t) return t;
  const ps = rules['page-states'] || {};
  const wordState = new Map();
  for (const [state, words] of Object.entries(ps.words || {})) {
    for (const w of words) {
      const n = normaliseStatus(w);
      if (n !== null) wordState.set(n, state);
    }
  }
  const known = new Set(wordState.keys());
  const st = rules.statuses || {};
  for (const w of [...(st.editable || []), ...(st.frozen || [])]) {
    const n = normaliseStatus(w);
    if (n !== null) known.add(n);
  }
  const prefixes = Object.entries(ps['prefix-words'] || {})
    .map(([p, state]) => [normaliseStatus(p), state])
    .filter(([p]) => p !== null);
  t = { wordState, known, prefixes };
  cache.set(rules, t);
  return t;
}

/**
 * The page state of a raw status: a state name, or null when the status is
 * absent, a list, or not a declared word.
 */
export function pageState(rules, status) {
  const n = normaliseStatus(status);
  if (n === null || isPipeList(status)) return null;
  const { wordState, prefixes } = tables(rules);
  if (wordState.has(n)) return wordState.get(n);
  for (const [p, state] of prefixes) if (n === p || n.startsWith(p + '-')) return state;
  return null;
}

/** Is the raw status a declared status word, or does it start with a prefix word? */
export function isKnownStatus(rules, status) {
  const n = normaliseStatus(status);
  if (n === null || isPipeList(status)) return false;
  const { known, prefixes } = tables(rules);
  if (known.has(n)) return true;
  return prefixes.some(([p]) => n === p || n.startsWith(p + '-'));
}
