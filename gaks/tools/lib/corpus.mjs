// corpus.mjs — read a GAKS corpus from disk.
//
//
// A DOCUMENT is a .md file whose file name matches the id pattern of the
// rules. Every other .md file is a PAGE: it is read for its wikilinks and its
// decisions, and it is not checked as a document. A directory or file whose
// name starts with a dot is skipped (.obsidian, .git).

import { readdirSync, readFileSync } from 'node:fs';
import { join, posix } from 'node:path';
import { parseFrontmatter } from './frontmatter.mjs';
import { findWikilinks, makeResolver, targetName } from './wikilinks.mjs';
import { fencedLines } from './code.mjs';
import { parseDocId } from './rules.mjs';

/** Every file under `root`, as sorted posix paths relative to it. */
export function walk(root) {
  const out = [];
  const visit = (dir, rel) => {
    let entries;
    try { entries = readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (e.name.startsWith('.') || e.name === 'node_modules') continue;
      const r = rel ? posix.join(rel, e.name) : e.name;
      if (e.isDirectory()) visit(join(dir, e.name), r);
      else if (e.isFile()) out.push(r);
    }
  };
  visit(root, '');
  return out.sort();
}

/** The text of the first `# ` heading outside code, or null. */
export function firstHeading(body) {
  const lines = String(body).split(/\r?\n/);
  const fenced = fencedLines(lines);
  for (let i = 0; i < lines.length; i++) {
    if (fenced[i]) continue;
    const m = /^#\s+(.+?)\s*#*\s*$/.exec(lines[i]);
    if (m) return m[1];
  }
  return null;
}

function str(v) {
  if (v === null || v === undefined) return null;
  return Array.isArray(v) ? v.join(', ') : String(v);
}

/**
 * Read one .md file. Returns
 *   {path, stem, isDocument, docId, prefix, hasFrontmatter, frontmatter, id,
 *    status, subproject, title, text, body, bodyLine, wikilinks}
 * `docId` is the unique key from the file name (series-NNN-RR), null for a
 * page. `id` is the frontmatter `id:` as written, or null. Wikilink line
 * numbers are lines of the whole file.
 */
export function readEntry(rules, root, path) {
  const text = readFileSync(join(root, ...path.split('/')), 'utf8');
  const name = path.split('/').pop();
  const stem = name.slice(0, -3);
  const parsed = parseDocId(rules, name);
  const fm = parseFrontmatter(text);
  const id = str(fm.data.id);
  return {
    path,
    stem,
    isDocument: parsed !== null,
    docId: parsed ? parsed.id : null,
    prefix: parsed ? parsed.prefix : null,
    hasFrontmatter: fm.present,
    frontmatter: fm.data,
    id,
    status: str(fm.data.status),
    subproject: str(fm.data.subproject),
    title: firstHeading(fm.body) || id || stem,
    text,
    body: fm.body,
    bodyLine: fm.bodyLine,
    wikilinks: findWikilinks(text, 1),
  };
}

/**
 * Read the corpus under `root`. Returns
 *   {root, entries, files, resolve}
 *   entries  the .md files, read (see readEntry), sorted by path
 *   files    the paths of every other file
 *   resolve  (target) => boolean, by file stem, `id:`, or file name
 *   lookup   (target) => {entry} | {file} | null, the same rule as resolve
 */
export function readCorpus(rules, root) {
  const all = walk(root);
  const md = all.filter((p) => p.toLowerCase().endsWith('.md'));
  const files = all.filter((p) => !p.toLowerCase().endsWith('.md'));
  const entries = md.map((p) => readEntry(rules, root, p));
  const resolve = makeResolver({
    stems: entries.map((e) => e.stem),
    ids: entries.map((e) => e.id).filter((x) => x),
    files: files.map((p) => p.split('/').pop()),
  });
  return { root, entries, files, resolve, lookup: makeLookup(entries, files) };
}

/**
 * A lookup over read entries and other files: the same rule as makeResolver,
 * but it returns what a target names. `{entry}` for a .md file (by stem first,
 * then by `id:`), `{file}` for another file (a path relative to the root), or
 * null. Two files with one stem: the first by path wins. An empty target is
 * null: the caller knows its own page.
 */
export function makeLookup(entries, files = []) {
  const byStem = new Map();
  const byId = new Map();
  for (const e of entries) {
    if (!byStem.has(e.stem)) byStem.set(e.stem, e);
    if (e.id && !byId.has(e.id)) byId.set(e.id, e);
  }
  const byFile = new Map();
  for (const f of files) {
    const name = f.split('/').pop();
    if (!byFile.has(name)) byFile.set(name, f);
  }
  return (target) => {
    const t = String(target).trim();
    if (t === '') return null;
    const n = targetName(t);
    const e = byStem.get(n) || byId.get(n);
    if (e) return { entry: e };
    const f = byFile.get(t.split('/').pop().trim());
    return f ? { file: f } : null;
  };
}
