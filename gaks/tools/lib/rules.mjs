// rules.mjs — load gaks.json and check its shape.
//
//
// gaks.json is generated from four declarations of the active GAKS (src/gaks/declaration.clj).
// This module refuses a file that lacks a key the checker needs, so a broken
// file is a usage error (exit 2), not a run that finds nothing.

import { readFileSync } from 'node:fs';

/** The rule names, in the order of the plan. */
export const RULES = [
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
];

/** Thrown for a rules file that cannot be used. */
export class RulesError extends Error {}

/** Check the shape of a parsed rules object. Returns it, or throws RulesError. */
export function validateRules(rules) {
  const problems = [];
  if (rules === null || typeof rules !== 'object' || Array.isArray(rules)) {
    throw new RulesError('the rules are not a JSON object');
  }
  if (typeof rules['id-pattern'] !== 'string') problems.push('"id-pattern" is not a string');
  else {
    try { new RegExp(rules['id-pattern']); } catch (e) { problems.push(`"id-pattern" is not a regex: ${e.message}`); }
  }
  if (!Array.isArray(rules.kinds) || rules.kinds.some((k) => !k || typeof k.prefix !== 'string')) {
    problems.push('"kinds" is not a list of {prefix, ...}');
  }
  if (!Array.isArray(rules.subprojects)) problems.push('"subprojects" is not a list');
  const ps = rules['page-states'];
  if (!ps || typeof ps !== 'object' || typeof ps.words !== 'object') {
    problems.push('"page-states" has no "words"');
  }
  if (rules.statuses !== undefined && typeof rules.statuses !== 'object') {
    problems.push('"statuses" is not an object');
  }
  const d = rules.decision;
  if (!d || typeof d.callout !== 'string' || !Array.isArray(d.states) || !Array.isArray(d.fields)
      || typeof d['key-pattern'] !== 'string') {
    problems.push('"decision" needs "callout", "states", "fields" and "key-pattern"');
  }
  if (rules.collisions !== undefined && !Array.isArray(rules.collisions)) {
    problems.push('"collisions" is not a list');
  }
  if (rules.ratchets !== undefined
      && (typeof rules.ratchets !== 'object' || Object.values(rules.ratchets).some((n) => !Number.isInteger(n)))) {
    problems.push('"ratchets" is not a map of integers');
  } else if (rules.ratchets) {
    // A ceiling for a name that is no rule changes nothing, and nothing says so.
    const unknown = Object.keys(rules.ratchets).filter((k) => !RULES.includes(k));
    if (unknown.length) {
      problems.push(`"ratchets" names no rule: ${unknown.join(', ')}. The rules: ${RULES.join(', ')}`);
    }
  }
  const c = rules.code;
  if (c !== undefined) {
    if (!c || !Array.isArray(c.extensions) || typeof c['annotation-pattern'] !== 'string'
        || (c['skip-dirs'] !== undefined && !Array.isArray(c['skip-dirs']))) {
      problems.push('"code" needs "extensions", "skip-dirs" and "annotation-pattern"');
    } else {
      try { new RegExp(c['annotation-pattern']); } catch (e) {
        problems.push(`"code" "annotation-pattern" is not a regex: ${e.message}`);
      }
    }
  }
  if (problems.length) throw new RulesError(problems.join('; '));
  return rules;
}

/** Read and check a gaks.json file. Throws RulesError on any problem. */
export function loadRules(path) {
  let text;
  try { text = readFileSync(path, 'utf8'); } catch (e) {
    throw new RulesError(`cannot read ${path}: ${e.code || e.message}`);
  }
  let rules;
  try { rules = JSON.parse(text); } catch (e) {
    throw new RulesError(`${path} is not JSON: ${e.message}`);
  }
  return validateRules(rules);
}

/**
 * The id of a file name, by the id pattern. Returns null when the name does
 * not match, else {series, number, revision, id, prefix}. `id` is the unique
 * key: the series, the number and the revision. `prefix` is the kind.
 */
export function parseDocId(rules, fileName) {
  const m = new RegExp(rules['id-pattern']).exec(fileName);
  if (!m) return null;
  const [, series, number, revision] = m;
  return { series, number, revision, id: `${series}-${number}-${revision}`, prefix: series.split('-')[0] };
}
