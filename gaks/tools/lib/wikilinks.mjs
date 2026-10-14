// wikilinks.mjs — find the wikilinks of a Markdown text, and resolve them.
//
//
// Forms: [[target]], [[target|alias]], [[target#heading]], [[target^block]],
// [[folder/target]], and the embed ![[target]]. In a table the pipe is often
// escaped, [[target\|alias]]. A link inside inline code or a fenced code
// block is ignored.

import { fencedLines, inlineCodeRanges, inRanges } from './code.mjs';

const LINK = /(!?)\[\[([^\[\]\n]*?)\]\]/g;

/**
 * Split the inside of [[...]] into {target, heading, alias}.
 * `target` keeps a folder prefix as written. An empty target is a link to a
 * heading of the same document.
 */
export function splitLink(inner) {
  let s = String(inner);
  let alias = null;
  const bar = s.indexOf('|');
  if (bar >= 0) {
    alias = s.slice(bar + 1).trim();
    s = s.slice(0, bar);
    if (s.endsWith('\\')) s = s.slice(0, -1);
  }
  let heading = null;
  const hash = s.search(/[#^]/);
  if (hash >= 0) {
    heading = s.slice(hash + 1).trim();
    s = s.slice(0, hash);
  }
  return { target: s.trim(), heading, alias };
}

/**
 * All wikilinks of `text`. Line numbers count from `firstLine` (1 by default).
 * Returns [{raw, target, heading, alias, embed, line}] in text order.
 */
export function findWikilinks(text, firstLine = 1) {
  const lines = String(text).split(/\r?\n/);
  const fenced = fencedLines(lines);
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    if (fenced[i]) continue;
    const line = lines[i];
    if (!line.includes('[[')) continue;
    const code = inlineCodeRanges(line);
    LINK.lastIndex = 0;
    let m;
    while ((m = LINK.exec(line)) !== null) {
      if (inRanges(code, m.index)) continue;
      const { target, heading, alias } = splitLink(m[2]);
      out.push({ raw: m[0], target, heading, alias, embed: m[1] === '!', line: firstLine + i });
    }
  }
  return out;
}

/** The last segment of a target, without a `.md` extension. */
export function targetName(target) {
  const seg = String(target).split('/').pop().trim();
  return seg.toLowerCase().endsWith('.md') ? seg.slice(0, -3) : seg;
}

/**
 * Build a resolver over a corpus index.
 *   stems  the file names of the .md files without `.md`
 *   ids    the frontmatter `id:` values
 *   files  the file names (with extension) of every other file
 * Returns (target) => true when it resolves. An empty target resolves: it is
 * a heading of the same document.
 */
export function makeResolver({ stems = [], ids = [], files = [] }) {
  const names = new Set([...stems, ...ids]);
  const others = new Set(files);
  return (target) => {
    const t = String(target).trim();
    if (t === '') return true;
    const seg = t.split('/').pop().trim();
    return names.has(targetName(t)) || others.has(seg);
  };
}

/**
 * Replace each wikilink of `text` outside code with `fn(link)`, where `link`
 * is {raw, target, heading, alias, embed, line} as findWikilinks gives it.
 * Code (fenced blocks and inline spans) is left as it is. The site uses this,
 * so it finds exactly the links that the checker finds.
 */
export function replaceWikilinks(text, fn, firstLine = 1) {
  const lines = String(text).split(/\r?\n/);
  const fenced = fencedLines(lines);
  for (let i = 0; i < lines.length; i++) {
    if (fenced[i] || !lines[i].includes('[[')) continue;
    const line = lines[i];
    const code = inlineCodeRanges(line);
    let out = '';
    let last = 0;
    const re = new RegExp(LINK.source, 'g');
    let m;
    while ((m = re.exec(line)) !== null) {
      if (inRanges(code, m.index)) continue;
      const { target, heading, alias } = splitLink(m[2]);
      out += line.slice(last, m.index) + fn({ raw: m[0], target, heading, alias, embed: m[1] === '!', line: firstLine + i });
      last = m.index + m[0].length;
    }
    lines[i] = out + line.slice(last);
  }
  return lines.join('\n');
}
