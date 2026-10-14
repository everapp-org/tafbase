// codelinks.mjs — the links from source code to documents.
//
//
// A Python or Java project links code to a document by an annotation in a
// comment, for example `# @feature F-shop-v1-003-01-login`. This module finds
// those annotations. The `code` key of gaks.json declares the file extensions,
// the folders to skip and the pattern. The Python checker reads the same key
// and must find the same annotations.

import { readdirSync, readFileSync } from 'node:fs';
import { join, posix } from 'node:path';

/** The extension of a file name: the text from its last dot, or ''. */
export function extensionOf(name) {
  const i = name.lastIndexOf('.');
  return i <= 0 ? '' : name.slice(i);
}

/**
 * Every source file under `dir`, as sorted posix paths relative to it. A
 * file is a source file when its extension is in `code.extensions`. A
 * directory whose name starts with a dot or is in `code.skip-dirs` is skipped.
 */
export function walkCode(code, dir) {
  const exts = new Set(code.extensions);
  const skip = new Set(code['skip-dirs'] || []);
  const out = [];
  const visit = (abs, rel) => {
    let entries;
    try { entries = readdirSync(abs, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      const r = rel ? posix.join(rel, e.name) : e.name;
      if (e.isDirectory()) {
        if (e.name.startsWith('.') || skip.has(e.name)) continue;
        visit(join(abs, e.name), r);
      } else if (e.isFile() && exts.has(extensionOf(e.name))) {
        out.push(r);
      }
    }
  };
  visit(dir, '');
  return out.sort();
}

/**
 * The annotations of one text: [{line, tag, target}], `line` 1-based. Each
 * match of `code.annotation-pattern` on a line is one annotation. Group 1 is
 * the tag (feature, adr, plan), group 2 is the target.
 */
export function findAnnotations(code, text) {
  const out = [];
  const lines = String(text).split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    const re = new RegExp(code['annotation-pattern'], 'g');
    let m;
    while ((m = re.exec(lines[i])) !== null) {
      out.push({ line: i + 1, tag: m[1], target: m[2] });
      if (m[0] === '') re.lastIndex++;
    }
  }
  return out;
}

/** Every annotation of every source file under `dir`: [{path, line, tag, target}]. */
export function scanCode(code, dir) {
  const out = [];
  for (const path of walkCode(code, dir)) {
    const text = readFileSync(join(dir, ...path.split('/')), 'utf8');
    for (const a of findAnnotations(code, text)) out.push({ path, ...a });
  }
  return out;
}
