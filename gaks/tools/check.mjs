#!/usr/bin/env node
// check.mjs — check a GAKS corpus against gaks.json.
//
//
//   node check.mjs --rules gaks.json --root <dir>/arch-root [--code <dir>] [--json]
//
// With --code, the checker also reads the source files under that folder. An
// annotation that names no document is a finding of code-link-unresolved.
//
// Exit 0: no finding of a rule that is not a ratchet, and each ratchet is at
// or under its ceiling. Exit 1: else. Exit 2: a usage error.
// Node 22, the standard library only.

import { statSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { loadRules, RulesError } from './lib/rules.mjs';
import { checkCorpus, RULES } from './lib/check.mjs';

const USAGE = 'usage: node check.mjs --rules <gaks.json> --root <dir> [--code <dir>] [--json]';

export function parseArgs(argv) {
  const opts = { rules: null, root: null, code: null, json: false, help: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--json') opts.json = true;
    else if (a === '--help' || a === '-h') opts.help = true;
    else if (a === '--rules' || a === '--root' || a === '--code') {
      const v = argv[i + 1];
      if (v === undefined || v.startsWith('--')) throw new RulesError(`${a} needs a value`);
      opts[a.slice(2)] = v;
      i++;
    } else throw new RulesError(`unknown argument: ${a}`);
  }
  return opts;
}

export function main(argv, out = process.stdout, err = process.stderr) {
  let opts, rules;
  try {
    opts = parseArgs(argv);
    if (opts.help) { out.write(USAGE + '\n'); return 0; }
    if (!opts.rules || !opts.root) throw new RulesError('--rules and --root are both needed');
    let st;
    try { st = statSync(opts.root); } catch { st = null; }
    if (!st || !st.isDirectory()) throw new RulesError(`--root ${opts.root} is not a directory`);
    if (opts.code !== null) {
      let cs;
      try { cs = statSync(opts.code); } catch { cs = null; }
      if (!cs || !cs.isDirectory()) throw new RulesError(`--code ${opts.code} is not a directory`);
    }
    rules = loadRules(opts.rules);
    if (opts.code !== null && !rules.code) throw new RulesError(`${opts.rules} has no "code" key, and --code needs it`);
  } catch (e) {
    if (!(e instanceof RulesError)) throw e;
    err.write(`check: ${e.message}\n${USAGE}\n`);
    return 2;
  }
  const r = checkCorpus(rules, opts.root, { code: opts.code });
  if (opts.json) {
    out.write(JSON.stringify({ findings: r.findings, counts: r.counts }, null, 2) + '\n');
  } else {
    for (const f of r.findings) out.write(`${f.rule}  ${f.path}  ${f.detail}\n`);
    for (const rule of RULES) {
      const rt = r.ratchets[rule];
      const tail = rt ? `  (ratchet, ceiling ${rt.ceiling}${rt.over ? ', OVER' : ''})` : '';
      out.write(`${rule}: ${r.counts[rule]}${tail}\n`);
    }
  }
  return r.exitCode;
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) {
  process.exitCode = main(process.argv.slice(2));
}
