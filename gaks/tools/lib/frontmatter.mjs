// frontmatter.mjs — read the leading `---` YAML block of a Markdown file.
//
//
// This is not a YAML parser. It reads what the GAKS corpus writes: scalar
// `key: value` lines, quoted strings, and `- item` lists under a `key:` line.
// Other lines (nested maps, block scalars) are skipped. It never throws.

/** Remove one pair of matching quotes. A double-quoted string keeps its
 *  escapes simple: \" and \\ only. */
export function unquote(s) {
  const t = String(s).trim();
  if (t.length >= 2 && t[0] === '"' && t[t.length - 1] === '"') {
    return t.slice(1, -1).replace(/\\(["\\])/g, '$1');
  }
  if (t.length >= 2 && t[0] === "'" && t[t.length - 1] === "'") {
    return t.slice(1, -1).replace(/''/g, "'");
  }
  return t;
}

/** A scalar value. An empty value is null. A `# comment` after a space is
 *  removed from an unquoted value. A flow list `[a, b]` becomes an array. */
function scalar(raw) {
  let t = raw.trim();
  if (t === '' || t === '~' || t === 'null') return null;
  if (t[0] !== '"' && t[0] !== "'") {
    t = t.replace(/\s+#.*$/, '').trim();
    if (t.startsWith('[') && t.endsWith(']') && !t.startsWith('[[')) {
      const inner = t.slice(1, -1).trim();
      return inner === '' ? [] : inner.split(',').map((x) => unquote(x));
    }
  }
  return unquote(t);
}

/**
 * Parse the frontmatter of `text`.
 * Returns {present, data, body, bodyLine, endLine}:
 *   present   true when the file starts with a closed `---` block
 *   data      the keys, {key: string | string[] | null}
 *   body      the text after the block (the whole text when absent)
 *   bodyLine  the 1-based line number of the first line of `body`
 *   endLine   the 1-based line of the closing `---` (0 when absent)
 */
export function parseFrontmatter(text) {
  const src = typeof text === 'string' ? text.replace(/^\uFEFF/, '') : '';
  const none = { present: false, data: {}, body: src, bodyLine: 1, endLine: 0 };
  const lines = src.split(/\r?\n/);
  if (lines.length === 0 || lines[0].trim() !== '---') return none;
  let end = -1;
  for (let i = 1; i < lines.length; i++) {
    const l = lines[i].trimEnd();
    if (l === '---' || l === '...') { end = i; break; }
  }
  if (end < 0) return none;

  const data = {};
  let listKey = null;
  for (let i = 1; i < end; i++) {
    const line = lines[i];
    if (line.trim() === '' || /^\s*#/.test(line)) continue;
    const item = /^\s*-\s+(.*)$/.exec(line);
    if (item && listKey !== null) {
      if (!Array.isArray(data[listKey])) data[listKey] = [];
      data[listKey].push(unquote(item[1]));
      continue;
    }
    const kv = /^([A-Za-z0-9_][A-Za-z0-9_.-]*)\s*:(?:\s+(.*)|\s*)$/.exec(line);
    if (kv && !/^\s/.test(line)) {
      const key = kv[1];
      const v = kv[2] === undefined ? '' : kv[2];
      if (v.trim() === '') {
        data[key] = null;
        listKey = key;
      } else {
        data[key] = scalar(v);
        listKey = null;
      }
      continue;
    }
    // An indented line that is not a list item (a nested map, a block
    // scalar): skipped, and the open list stays open.
  }
  return {
    present: true,
    data,
    body: lines.slice(end + 1).join('\n'),
    bodyLine: end + 2,
    endLine: end + 1,
  };
}
