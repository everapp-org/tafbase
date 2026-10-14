// check.mjs — the ten rules of the GAKS checker, as functions.
//
//
// The CLI (gaks/js/check.mjs) and the site import this. The conformance cases
// of gaks-cert/conformance/ hold it to the expected findings.

import { readCorpus } from './corpus.mjs';
import { isKnownStatus, isPipeList } from './states.mjs';
import { parseDecisions } from './decisions.mjs';
import { scanCode } from './codelinks.mjs';
import { RULES } from './rules.mjs';

// RULES is declared in rules.mjs, because validateRules reads it too.
export { RULES };

/**
 * The detail of a decision-malformed finding: `line <n>: <head>`, and for a
 * repeated key `line <n>: <head> (the key repeats)`. The reason in words stays
 * out of it, so a second implementation gives the same text.
 */
export function decisionDetail(problem) {
  const base = `line ${problem.line}: ${problem.head}`;
  return problem.kind === 'repeat' ? `${base} (the key repeats)` : base;
}

/** Sort findings by rule, then path, then detail. */
export function sortFindings(findings) {
  const key = (f) => [f.rule, f.path, f.detail];
  return [...findings].sort((a, b) => {
    const ka = key(a), kb = key(b);
    for (let i = 0; i < 3; i++) {
      if (ka[i] < kb[i]) return -1;
      if (ka[i] > kb[i]) return 1;
    }
    return 0;
  });
}

/**
 * Check a corpus that is already read (see readCorpus).
 * `annotations` is the result of scanCode, or null when no code is read.
 * Returns {findings, counts, decisions, ratchets, exitCode}:
 *   findings   [{rule, path, detail}], sorted
 *   counts     {rule: n} for each of the ten rules
 *   decisions  every parsed decision block, in path order
 *   ratchets   {rule: {count, ceiling, over}} for each declared ratchet
 *   exitCode   0 or 1, as the plan says
 */
export function checkEntries(rules, corpus, annotations = null) {
  const findings = [];
  const add = (rule, path, detail) => findings.push({ rule, path, detail });
  const kinds = new Set(rules.kinds.map((k) => k.prefix));
  const subprojects = new Set(rules.subprojects);
  const listed = new Set((rules.collisions || []).map((c) => c.id));
  const byId = new Map();
  const decisions = [];
  // A document is in the wrong folder only when its parent folder belongs to
  // another declared kind. Other folders (notes, archive) are free.
  const ownFolder = new Map(rules.kinds.map((k) => [k.prefix, k.folder]));
  const kindFolders = new Set(rules.kinds.map((k) => k.folder).filter((f) => f));
  const targets = new Set();

  for (const e of corpus.entries) {
    if (e.isDocument) {
      targets.add(e.stem);
      targets.add(e.docId);
      if (!kinds.has(e.prefix)) add('kind-undeclared', e.path, e.prefix);
      if (!e.hasFrontmatter) add('frontmatter-missing', e.path, 'no frontmatter');
      const parts = e.path.split('/');
      const parent = parts.length > 1 ? parts[parts.length - 2] : '';
      const own = ownFolder.get(e.prefix);
      if (kinds.has(e.prefix) && kindFolders.has(parent) && parent !== own) {
        add('kind-folder', e.path, `${e.prefix} in ${parent}, declared ${own}`);
      }
      if (e.id !== null && e.id.trim() !== '' && e.id.trim() !== e.stem) add('id-not-filename', e.path, e.id);
      if (!byId.has(e.docId)) byId.set(e.docId, []);
      byId.get(e.docId).push(e.path);
      if (e.status !== null && e.status.trim() !== '' && !isKnownStatus(rules, e.status)) {
        add('status-unknown', e.path, e.status);
      }
      if (e.subproject !== null && e.subproject.trim() !== ''
          && (isPipeList(e.subproject) || !subprojects.has(e.subproject.trim()))) {
        add('subproject-unknown', e.path, e.subproject);
      }
    }
    const { decisions: ds, problems } = parseDecisions(rules, e.text, { doc: e.stem, path: e.path });
    decisions.push(...ds);
    for (const p of problems) add('decision-malformed', e.path, decisionDetail(p));
    for (const w of e.wikilinks) {
      if (!corpus.resolve(w.target)) add('wikilink-unresolved', e.path, w.target);
    }
  }
  for (const a of annotations || []) {
    if (!targets.has(a.target)) add('code-link-unresolved', a.path, `line ${a.line}: ${a.target}`);
  }
  for (const [id, paths] of byId) {
    if (paths.length > 1 && !listed.has(id)) {
      for (const p of paths) add('id-duplicate', p, id);
    }
  }

  const counts = Object.fromEntries(RULES.map((r) => [r, 0]));
  for (const f of findings) counts[f.rule] = (counts[f.rule] || 0) + 1;
  const ceilings = rules.ratchets || {};
  const ratchets = {};
  for (const [rule, ceiling] of Object.entries(ceilings)) {
    const count = counts[rule] || 0;
    ratchets[rule] = { count, ceiling, over: count > ceiling };
  }
  const hard = RULES.some((r) => !(r in ceilings) && counts[r] > 0);
  const over = Object.values(ratchets).some((r) => r.over);
  return { findings: sortFindings(findings), counts, decisions, ratchets, exitCode: hard || over ? 1 : 0 };
}

/**
 * Read the corpus under `root` and check it. With `opts.code`, also read the
 * source files under that folder for annotations. Same return shape as
 * checkEntries.
 */
export function checkCorpus(rules, root, opts = {}) {
  const annotations = opts.code ? scanCode(rules.code, opts.code) : null;
  return checkEntries(rules, readCorpus(rules, root), annotations);
}
