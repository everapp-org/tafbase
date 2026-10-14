#!/usr/bin/env node
// site.mjs — build a static site of a GAKS corpus.
//
//
//   node site.mjs --rules gaks.json --root <dir>/arch-root --out <site dir> [--name "<project>"]
//
// Exit 0: the site is written. Exit 1: the build failed. Exit 2: a usage error.
//
// The site opens from disk (file://). So every link is relative, and no page
// fetches a file: the search index is a plain script that sets a global.
// "mentioned in" (backlinks), the page properties report of each kind, the
// page states, the decision log, and the include of a page or a section at
// build time (`![[target#Heading]]`).
//
// It parses nothing itself. The library (lib/*.mjs) reads the corpus, the
// wikilinks, the decisions and the states, as the checker does. Markdown
// becomes HTML through `marked`: the copy in ./vendor/ in a bundle, else the
// package from node_modules.

import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { join, posix } from 'node:path';
import { pathToFileURL } from 'node:url';
import { loadRules, RulesError } from './lib/rules.mjs';
import { readCorpus } from './lib/corpus.mjs';
import { checkEntries, RULES } from './lib/check.mjs';
import { replaceWikilinks } from './lib/wikilinks.mjs';
import { parseDecisions } from './lib/decisions.mjs';
import { pageState } from './lib/states.mjs';
import { fencedLines } from './lib/code.mjs';

const USAGE = 'usage: node site.mjs --rules <gaks.json> --root <dir> --out <site dir> [--name "<project name>"]';
const MARKER = 'gaks-site.json';
const MAX_EMBED_DEPTH = 3;
const INDEX_TEXT_CAP = 3000;
const IMAGE = /\.(png|jpe?g|gif|svg|webp|avif)$/i;

/** marked: the vendored copy beside this file, else the package. */
export async function loadMarked() {
  const vendored = new URL('./vendor/marked.esm.js', import.meta.url);
  if (existsSync(vendored)) return import(vendored.href);
  return import('marked');
}

// ---------------------------------------------------------------- helpers

/** Escape text for HTML content and for an attribute value. */
export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

/** The anchor of a heading text: lower case, letters, digits and hyphens. */
export function slug(text) {
  return String(text).toLowerCase()
    .replace(/[*_`~\[\]()]/g, '')
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .trim().replace(/\s/g, '-');
}

/** The output path of a corpus .md file, relative to the site root. */
export function pageOut(path) { return 'doc/' + path.replace(/\.md$/i, '.html'); }
/** The output path of another corpus file. */
export function fileOut(path) { return 'doc/' + path; }

/** A relative href from the page at `from` to the file at `to` (both site paths). */
export function rel(from, to) {
  let r = posix.relative(posix.dirname(from), to);
  if (r === '') r = posix.basename(to);
  return r.split('/').map((seg) => (seg === '..' || seg === '.' ? seg : encodeURIComponent(seg))).join('/');
}

/** `../` repeated to the site root from a site path. */
function toRoot(from) {
  const depth = from.split('/').length - 1;
  return depth === 0 ? '' : '../'.repeat(depth);
}

function str(v) {
  if (v === null || v === undefined) return null;
  return Array.isArray(v) ? v.join(', ') : String(v);
}

function dateOf(fm) {
  return str(fm.date) || str(fm.authored) || str(fm.created) || str(fm['last-reviewed']) || '';
}

/** A title as HTML: escaped, and a `code` span drawn as code. */
export function titleHtml(t) {
  return esc(t).replace(/`([^`]+)`/g, '<code>$1</code>');
}

/** The body without its first `# ` heading outside code: the page draws the title itself. */
export function withoutTitle(body) {
  const lines = String(body).split(/\r?\n/);
  const fenced = fencedLines(lines);
  const i = lines.findIndex((l, n) => !fenced[n] && /^#\s+\S/.test(l));
  if (i < 0) return body;
  lines.splice(i, 1);
  return lines.join('\n');
}

function stateBadge(state, raw) {
  const s = state || 'unknown';
  const t = raw ? ` title="${esc(raw)}"` : '';
  return `<span class="badge state-${esc(s)}"${t}>${esc(s)}</span>`;
}

/** The text of `body` under `heading`, up to the next heading of the same or a higher level. */
export function extractSection(body, heading, isBlock = false) {
  const lines = String(body).split(/\r?\n/);
  const fenced = fencedLines(lines);
  if (isBlock) {
    const at = lines.findIndex((l, i) => !fenced[i] && new RegExp(`\\s\\^${heading.replace(/[^\w-]/g, '')}\\s*$`).test(l));
    if (at < 0) return null;
    let a = at, b = at;
    while (a > 0 && lines[a - 1].trim() !== '') a--;
    while (b < lines.length - 1 && lines[b + 1].trim() !== '') b++;
    return lines.slice(a, b + 1).join('\n').replace(/\s\^[\w-]+\s*$/m, '');
  }
  const want = slug(heading);
  let start = -1, level = 0;
  for (let i = 0; i < lines.length; i++) {
    if (fenced[i]) continue;
    const m = /^(#{1,6})\s+(.*?)\s*#*\s*$/.exec(lines[i]);
    if (!m) continue;
    if (start < 0) {
      if (slug(m[2]) === want) { start = i; level = m[1].length; }
    } else if (m[1].length <= level) {
      return lines.slice(start, i).join('\n');
    }
  }
  return start < 0 ? null : lines.slice(start).join('\n');
}

/** Plain text of a Markdown body, for the search index. */
export function plainText(body) {
  return replaceWikilinks(body, (l) => l.alias || l.target + (l.heading ? ' ' + l.heading : ''))
    .replace(/\[!([a-z-]+)\][+-]?/gi, '$1')
    .replace(/!?\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[*_`~]+/g, '')
    .replace(/[#>|\\]+|(^|\s)-+(?=\s|$)/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

// ---------------------------------------------------------------- the site

/**
 * Build the site. Returns {files, bytes, documents, pages, indexBytes,
 * decisions, check}. `marked` is the module that loadMarked returns.
 */
export function buildSite({ rules, root, out, name, marked }) {
  const corpus = readCorpus(rules, root);
  const check = checkEntries(rules, corpus);
  const name_ = name || 'GAKS corpus';
  const entries = corpus.entries;
  const byPath = new Map(entries.map((e) => [e.path, e]));
  const fileSet = new Set(corpus.files);
  const kinds = new Map(rules.kinds.map((k) => [k.prefix, k]));
  const meaning = (rules['page-states'] || {}).meaning || {};
  const stateOrder = (rules['page-states'] || {}).order || [];
  const written = new Map(); // site path -> content (string or {copy})
  const toCopy = new Set();
  const write = (p, content) => written.set(p, content);

  // Backlinks: every resolved wikilink, by its target page.
  const backlinks = new Map();
  for (const e of entries) {
    for (const w of e.wikilinks) {
      const r = corpus.lookup(w.target);
      if (!r || !r.entry || r.entry === e) continue;
      if (!backlinks.has(r.entry.path)) backlinks.set(r.entry.path, new Set());
      backlinks.get(r.entry.path).add(e.path);
    }
  }

  // ----- Markdown rendering. `current` is the context of the parse that runs.
  let current = null;
  const md = new marked.Marked({ gfm: true });
  md.use({
    renderer: {
      heading({ tokens, depth, text }) {
        const inner = this.parser.parseInline(tokens);
        if (!current || !current.ids) return `<h${depth}>${inner}</h${depth}>\n`;
        const base = slug(labelOf(text)) || 'section';
        const n = current.slugs.get(base) || 0;
        current.slugs.set(base, n + 1);
        const id = n === 0 ? base : `${base}-${n}`;
        return `<h${depth} id="${esc(id)}">${inner}<a class="anchor" href="#${esc(id)}" aria-label="Link to this section">#</a></h${depth}>\n`;
      },
      blockquote({ tokens }) {
        const body = this.parser.parse(tokens);
        const m = /^<p>\[!([A-Za-z0-9_-]+)\][+-]?[ \t]*/.exec(body);
        if (!m) return `<blockquote>\n${body}</blockquote>\n`;
        const type = m[1].toLowerCase();
        const rest = '<p>' + body.slice(m[0].length);
        let restClean = rest.startsWith('<p></p>') ? rest.slice(7) : rest;
        const t = /^<p>([^\n<]+)(\n|<\/p>\n?)/.exec(restClean);
        if (t) restClean = `<div class="callout-title">${t[1]}</div>` + (t[2] === '\n' ? '<p>' : '') + restClean.slice(t[0].length);
        const bad = type === rules.decision.callout ? ' callout-malformed' : '';
        const note = bad ? ' <span class="muted">(the head of this decision does not parse)</span>' : '';
        return `<div class="callout callout-${esc(type)}${bad}"><div class="callout-type">${esc(type)}${note}</div>${restClean}</div>\n`;
      },
      // Raw HTML of the Markdown passes, but never a script, a frame or a
      // style: a site that opens from disk runs no code and takes no style
      // that a page brought (a pasted transcript holds <link> and <style>).
      html({ text }) {
        return String(text).replace(/<(\/?)(script|iframe|object|embed|style|link|meta|base)\b/gi, '&lt;$1$2');
      },
      link({ href, title, tokens }) {
        const text = this.parser.parseInline(tokens);
        const r = resolveHref(href);
        if (r.dead) return `<span class="dead-link" title="${esc(r.dead)}">${text}</span>`;
        const t = title ? ` title="${esc(title)}"` : '';
        const ext = /^[a-z][a-z0-9+.-]*:/i.test(r.href) ? ' rel="noopener"' : '';
        return `<a href="${esc(r.href)}"${t}${ext}>${text}</a>`;
      },
      image({ href, title, text }) {
        const r = resolveHref(href);
        if (r.dead) return `<span class="dead-link" title="${esc(r.dead)}">[image: ${esc(text)}]</span>`;
        const t = title ? ` title="${esc(title)}"` : '';
        return `<img src="${esc(r.href)}" alt="${esc(text)}"${t} loading="lazy">`;
      },
    },
  });

  function labelOf(text) {
    return String(text).replace(/GAKSTOKEN(\d+)X/g, (_, n) => (current && current.tokens[n] ? current.tokens[n].label : ''));
  }

  /** A Markdown href, as the page in `current` sees it. */
  function resolveHref(href) {
    const h = String(href || '');
    if (h === '' || h.startsWith('#') || /^[a-z][a-z0-9+.-]*:/i.test(h) || h.startsWith('//')) return { href: h };
    const [pathPart, ...hashParts] = h.split('#');
    const hash = hashParts.length ? '#' + hashParts.join('#') : '';
    let p;
    try { p = decodeURI(pathPart); } catch { p = pathPart; }
    if (p.startsWith('/')) return { dead: `Not in the corpus: ${p}` };
    const target = posix.normalize(posix.join(posix.dirname(current.srcPath), p));
    if (target.startsWith('..')) return { dead: `Outside the corpus: ${p}` };
    if (byPath.has(target)) return { href: rel(current.from, pageOut(target)) + hash };
    if (fileSet.has(target)) { toCopy.add(target); return { href: rel(current.from, fileOut(target)) + hash }; }
    return { dead: `No file at ${target}` };
  }

  function linkHtml(l, ctx) {
    const label = l.alias || (l.target === '' ? l.heading : l.target + (l.heading ? ' › ' + l.heading : ''));
    const isBlock = l.raw.includes('^');
    const anchor = l.heading ? '#' + (isBlock ? '^' + l.heading : slug(l.heading)) : '';
    if (l.target === '') return { html: `<a class="wikilink" href="${esc(anchor)}">${esc(label)}</a>`, label };
    const r = corpus.lookup(l.target);
    if (!r) return { html: `<span class="dead-link" title="${esc(`No page named ${l.target}`)}">${esc(label)}</span>`, label };
    if (r.file) {
      toCopy.add(r.file);
      const href = rel(ctx.from, fileOut(r.file));
      if (l.embed && IMAGE.test(r.file)) return { html: `<img src="${esc(href)}" alt="${esc(label)}" loading="lazy">`, label };
      return { html: `<a class="wikilink" href="${esc(href)}">${esc(label)}</a>`, label };
    }
    const href = rel(ctx.from, pageOut(r.entry.path)) + anchor;
    return { html: `<a class="wikilink" href="${esc(href)}" title="${esc(r.entry.title)}">${esc(label)}</a>`, label, entry: r.entry };
  }

  function embedHtml(l, ctx) {
    const r = corpus.lookup(l.target);
    if (!r || r.file) return linkHtml(l, ctx);
    const e = r.entry;
    const href = rel(ctx.from, pageOut(e.path)) + (l.heading ? '#' + slug(l.heading) : '');
    const label = e.title + (l.heading ? ' › ' + l.heading : '');
    const head = `<div class="embed-head">Included from <a href="${esc(href)}">${esc(label)}</a></div>`;
    const refuse = (why) => ({ html: `<div class="embed embed-refused">${head}<p class="muted">${esc(why)}</p></div>`, label });
    if (ctx.stack.includes(e.path)) return refuse('Not included: this page is already included above it (a cycle).');
    if (ctx.depth + 1 > MAX_EMBED_DEPTH) return refuse(`Not included: more than ${MAX_EMBED_DEPTH} levels of includes.`);
    const section = l.heading ? extractSection(e.body, l.heading, l.raw.includes('^')) : e.body;
    if (section === null) return refuse(`Not included: no section "${l.heading}" in this page.`);
    const inner = render(section, { from: ctx.from, srcPath: e.path, depth: ctx.depth + 1, stack: [...ctx.stack, e.path], ids: false });
    return { html: `<div class="embed">${head}<div class="embed-body">${inner}</div></div>`, label };
  }

  /** Replace the wikilinks of `text` by tokens of `ctx`. */
  function linkify(text, ctx) {
    return replaceWikilinks(text, (l) => {
      const r = l.embed ? embedHtml(l, ctx) : linkHtml(l, ctx);
      ctx.tokens.push(r);
      return `GAKSTOKEN${ctx.tokens.length - 1}X`;
    });
  }

  function untoken(html, ctx) {
    return html
      .replace(/<p>\s*GAKSTOKEN(\d+)X\s*<\/p>/g, (_, n) => ctx.tokens[n].html)
      .replace(/GAKSTOKEN(\d+)X/g, (_, n) => ctx.tokens[n].html);
  }

  /** Inline Markdown with wikilinks, for a decision's text. */
  function inline(text, ctx) {
    const c = { ...ctx, tokens: [] };
    const src = linkify(text, c);
    const prev = current; current = c;
    try { return untoken(md.parseInline(src), c); } finally { current = prev; }
  }

  function decisionBox(d, ctx) {
    const id = ctx.ids ? ` id="decision-${esc(d.key)}"` : '';
    const meta = d.state === 'open' ? '' : ` <span class="decision-meta">${esc(d.date)} · ${esc(d.who)}</span>`;
    const fields = Object.entries(d.fields).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${inline(v, ctx)}</dd>`).join('');
    return `<div class="decision decision-${esc(d.state)}"${id}>`
      + `<div class="decision-head"><span class="decision-label">Decision</span> `
      + `<a class="decision-key" href="#decision-${esc(d.key)}">${esc(d.key)}</a> `
      + `<span class="badge dstate-${esc(d.state)}">${esc(d.state)}</span>${meta}</div>`
      + (d.question ? `<div class="decision-question">${inline(d.question, ctx)}</div>` : '')
      + (fields ? `<dl class="decision-fields">${fields}</dl>` : '')
      + '</div>';
  }

  /** Decision blocks become tokens; a head that does not parse stays a callout. */
  function decisionBlocks(text, ctx) {
    const lines = String(text).split(/\r?\n/);
    const fenced = fencedLines(lines);
    const cal = rules.decision.callout.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const headRe = new RegExp(`^\\s{0,3}>\\s*\\[!${cal}\\][+-]?`, 'i');
    const out = [];
    for (let i = 0; i < lines.length; i++) {
      if (fenced[i] || !headRe.test(lines[i])) { out.push(lines[i]); continue; }
      let j = i + 1;
      while (j < lines.length && /^\s{0,3}>/.test(lines[j]) && !headRe.test(lines[j])) j++;
      const block = lines.slice(i, j).join('\n');
      const { decisions } = parseDecisions(rules, block, {});
      if (decisions.length === 1) {
        ctx.tokens.push({ html: decisionBox(decisions[0], ctx), label: decisions[0].key });
        out.push('', `GAKSTOKEN${ctx.tokens.length - 1}X`, '');
      } else {
        out.push(...lines.slice(i, j));
      }
      i = j - 1;
    }
    return out.join('\n');
  }

  /**
   * Markdown → HTML. ctx: {from: the site path of the page that shows it,
   * srcPath: the corpus path of the text, depth, stack, ids}.
   */
  function render(text, ctx0) {
    const ctx = { ...ctx0, tokens: [], slugs: new Map() };
    const src = linkify(decisionBlocks(text, ctx), ctx);
    const prev = current; current = ctx;
    try { return untoken(md.parse(src), ctx); } finally { current = prev; }
  }

  // ----- The frame of every page.
  const reportKinds = [...new Set(entries.filter((e) => e.isDocument).map((e) => e.prefix))]
    .sort((a, b) => {
      const ia = rules.kinds.findIndex((k) => k.prefix === a), ib = rules.kinds.findIndex((k) => k.prefix === b);
      return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib) || (a < b ? -1 : 1);
    });
  const others = entries.filter((e) => !e.isDocument);
  const kindName = (p) => (kinds.get(p) ? kinds.get(p).name : `${p} (not a declared kind)`);
  const countOf = (p) => entries.filter((e) => e.isDocument && e.prefix === p).length;

  function layout(at, title, body, { search = false, active = '' } = {}) {
    const r = toRoot(at);
    const nav = [['index.html', 'Home'], ['tree.html', 'Tree'], ['decisions.html', 'Decisions'], ['checks.html', 'Checks']]
      .map(([h, t]) => `<a href="${r}${h}"${active === h ? ' aria-current="page"' : ''}>${t}</a>`).join('');
    const side = reportKinds.map((p) => `<li><a href="${r}reports/${esc(p)}.html"${active === `reports/${p}.html` ? ' aria-current="page"' : ''}>${esc(kindName(p))}</a> <span class="count">${countOf(p)}</span></li>`).join('')
      + `<li><a href="${r}reports/other.html"${active === 'reports/other.html' ? ' aria-current="page"' : ''}>Other pages</a> <span class="count">${others.length}</span></li>`;
    return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} · ${esc(name_)}</title>
<link rel="stylesheet" href="${r}assets/site.css">
${search ? `<script src="${r}assets/search-index.js"></script>\n` : ''}<script src="${r}assets/site.js" defer></script>
</head>
<body>
<header class="top">
<a class="brand" href="${r}index.html">${esc(name_)}</a>
<nav class="topnav">${nav}</nav>
<form class="topsearch" action="${r}search.html" method="get" role="search"><input type="search" name="q" placeholder="Search" aria-label="Search the corpus"></form>
</header>
<div class="shell">
<main class="main">
${body}
</main>
<nav class="side" aria-label="Kinds"><h2>Kinds</h2><ul>${side}</ul></nav>
</div>
<footer class="foot">Built ${esc(new Date().toISOString().slice(0, 16).replace('T', ' '))} UTC from gaks.json ${esc(rules['gaks-version'] || '')}. A projection of the Markdown: do not edit it by hand.</footer>
</body>
</html>
`;
  }

  // ----- One page per Markdown file.
  for (const e of entries) {
    const at = pageOut(e.path);
    const fm = e.frontmatter;
    const state = e.isDocument || e.status ? pageState(rules, e.status) : null;
    const rows = [];
    if (e.id || e.docId) rows.push(['id', esc(e.id || e.docId)]);
    if (e.status) rows.push(['status', `${esc(e.status)} ${stateBadge(state, e.status)}`]);
    if (e.subproject) rows.push(['subproject', esc(e.subproject)]);
    if (dateOf(fm)) rows.push(['date', esc(dateOf(fm))]);
    if (fm.authors) rows.push(['authors', esc(str(fm.authors))]);
    if (e.isDocument) rows.push(['kind', `<a href="${rel(at, `reports/${e.prefix}.html`)}">${esc(kindName(e.prefix))}</a>`]);
    rows.push(['source', `<code>${esc(e.path)}</code>`]);
    const shown = new Set(['id', 'status', 'subproject', 'date', 'authors']);
    const rest = Object.entries(fm).filter(([k, v]) => !shown.has(k) && v !== null);
    const props = `<table class="props">${rows.map(([k, v]) => `<tr><th>${k}</th><td>${v}</td></tr>`).join('')}</table>`
      + (rest.length ? `<details class="props-more"><summary>All properties (${rest.length} more)</summary><table class="props">${rest.map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(str(v))}</td></tr>`).join('')}</table></details>` : '');
    const html = render(withoutTitle(e.body), { from: at, srcPath: e.path, depth: 0, stack: [e.path], ids: true });
    const back = [...(backlinks.get(e.path) || [])].map((p) => byPath.get(p)).sort((a, b) => a.title.localeCompare(b.title));
    const backHtml = `<section class="backlinks"><h2>Mentioned in <span class="count">${back.length}</span></h2>`
      + (back.length
        ? `<ul>${back.map((b) => `<li><a href="${rel(at, pageOut(b.path))}">${titleHtml(b.title)}</a> <span class="muted">${esc(b.id || b.docId || b.path)}</span></li>`).join('')}</ul>`
        : '<p class="muted">No page links here.</p>')
      + '</section>';
    const crumbs = e.path.split('/').slice(0, -1);
    const crumbHtml = `<div class="crumbs"><a href="${rel(at, 'tree.html')}">Tree</a>${crumbs.map((c) => ` / ${esc(c)}`).join('')}</div>`;
    const badge = state || e.status ? ' ' + stateBadge(state, e.status) : '';
    const h1 = `<h1 class="page-title" id="${esc(slug(e.title))}">${titleHtml(e.title)}${badge}</h1>`;
    write(at, layout(at, e.title, `${crumbHtml}${h1}${props}<article class="doc">${html}</article>${backHtml}`));
  }

  // ----- The report of each kind: the page properties report.
  function reportTable(at, list, withState) {
    const head = withState
      ? '<tr><th>id</th><th>title</th><th>state</th><th>status</th><th>subproject</th><th>date</th></tr>'
      : '<tr><th>path</th><th>title</th><th>status</th><th>date</th></tr>';
    const body = list.map((e) => {
      const st = pageState(rules, e.status);
      const link = (t) => `<a href="${rel(at, pageOut(e.path))}">${esc(t)}</a>`;
      return withState
        ? `<tr data-state="${esc(st || 'unknown')}"><td class="nowrap">${link(e.docId)}</td><td>${titleHtml(e.title)}</td><td data-sort="${stateOrder.indexOf(st)}">${stateBadge(st, e.status)}</td><td>${esc(e.status || '')}</td><td>${esc(e.subproject || '')}</td><td class="nowrap">${esc(dateOf(e.frontmatter))}</td></tr>`
        : `<tr><td>${link(e.path)}</td><td>${titleHtml(e.title)}</td><td>${esc(e.status || '')}</td><td class="nowrap">${esc(dateOf(e.frontmatter))}</td></tr>`;
    }).join('');
    const states = withState
      ? `<select data-filter-state aria-label="Filter by page state"><option value="">every state</option>${[...stateOrder, 'unknown'].map((s) => `<option>${esc(s)}</option>`).join('')}</select>`
      : '';
    return `<div class="filters"><input type="search" data-filter placeholder="Filter rows" aria-label="Filter rows">${states}<span class="muted" data-filter-count>${list.length} rows</span></div>`
      + `<div class="table-wrap"><table class="report sortable kind-report"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
  }
  for (const p of reportKinds) {
    const at = `reports/${p}.html`;
    const list = entries.filter((e) => e.isDocument && e.prefix === p);
    const k = kinds.get(p);
    const tmpl = k && k.template ? `<p class="muted">Sections of a new ${esc(k.name.toLowerCase())}: ${k.template.map(esc).join(' · ')}</p>` : '';
    write(at, layout(at, kindName(p), `<h1>${esc(kindName(p))} <span class="count">${list.length}</span></h1><p class="muted">Prefix <code>${esc(p)}</code>${k ? `, folder <code>${esc(k.folder || '')}</code>` : ''}. Click a column head to sort.</p>${tmpl}${reportTable(at, list, true)}`, { active: at }));
  }
  {
    const at = 'reports/other.html';
    write(at, layout(at, 'Other pages', `<h1>Other pages <span class="count">${others.length}</span></h1><p class="muted">Markdown files whose name is not a document id. They are read for links and decisions and are not checked as documents.</p>${reportTable(at, others, false)}`, { active: at }));
  }

  // ----- The tree.
  {
    const at = 'tree.html';
    const rootNode = { dirs: new Map(), files: [] };
    for (const e of entries) {
      const segs = e.path.split('/');
      let n = rootNode;
      for (const s of segs.slice(0, -1)) {
        if (!n.dirs.has(s)) n.dirs.set(s, { dirs: new Map(), files: [] });
        n = n.dirs.get(s);
      }
      n.files.push(e);
    }
    const count = (n) => n.files.length + [...n.dirs.values()].reduce((a, d) => a + count(d), 0);
    const draw = (n, level) => {
      const dirs = [...n.dirs.entries()].sort(([a], [b]) => a.localeCompare(b))
        .map(([d, c]) => `<li><details${level === 0 ? ' open' : ''}><summary>${esc(d)} <span class="count">${count(c)}</span></summary>${draw(c, level + 1)}</details></li>`).join('');
      const files = n.files.sort((a, b) => a.path.localeCompare(b.path)).map((e) => {
        const st = pageState(rules, e.status);
        return `<li class="leaf"><a href="${rel(at, pageOut(e.path))}">${titleHtml(e.title)}</a> ${e.status ? stateBadge(st, e.status) : ''} <span class="muted">${esc(e.stem)}</span></li>`;
      }).join('');
      return `<ul class="tree">${dirs}${files}</ul>`;
    };
    write(at, layout(at, 'Tree', `<h1>Tree <span class="count">${entries.length}</span></h1><p class="muted">Every Markdown file, by folder.</p>${draw(rootNode, 0)}`, { active: at }));
  }

  // ----- The decision log.
  const decisions = check.decisions;
  const open = decisions.filter((d) => d.state === 'open');
  const decided = decisions.filter((d) => d.state === 'decided');
  const withdrawn = decisions.filter((d) => d.state === 'withdrawn');
  const problems = check.findings.filter((f) => f.rule === 'decision-malformed');
  {
    const at = 'decisions.html';
    const ctxFor = (d) => ({ from: at, srcPath: d.path, depth: 0, stack: [d.path], ids: false });
    const docLink = (d) => {
      const e = byPath.get(d.path);
      return `<a href="${rel(at, pageOut(d.path))}">${esc(e ? e.title : d.path)}</a>`;
    };
    const keyLink = (d) => `<a class="decision-key" href="${rel(at, pageOut(d.path))}#decision-${encodeURIComponent(d.key)}">${esc(d.key)}</a>`;
    const groups = new Map();
    for (const d of open) {
      if (!groups.has(d.path)) groups.set(d.path, []);
      groups.get(d.path).push(d);
    }
    const openHtml = [...groups.entries()].map(([p, ds]) => `<section class="dgroup"><h3>${docLink(ds[0])} <span class="muted">${esc(ds[0].doc)}</span></h3>`
      + ds.map((d) => `<div class="decision decision-open"><div class="decision-head">${keyLink(d)} <span class="badge dstate-open">open</span></div>`
        + (d.question ? `<div class="decision-question">${inline(d.question, ctxFor(d))}</div>` : '')
        + `<dl class="decision-fields">${['Recommendation', 'Opens'].filter((f) => d.fields[f]).map((f) => `<dt>${f}</dt><dd>${inline(d.fields[f], ctxFor(d))}</dd>`).join('')}</dl></div>`).join('')
      + '</section>').join('');
    const closedTable = (list, field) => (list.length
      ? `<div class="table-wrap"><table class="report sortable"><thead><tr><th>document</th><th>key</th><th>date</th><th>who</th><th>question</th><th>${field}</th></tr></thead><tbody>`
        + list.map((d) => `<tr><td>${docLink(d)}</td><td>${keyLink(d)}</td><td>${esc(d.date)}</td><td>${esc(d.who)}</td><td>${inline(d.question, ctxFor(d))}</td><td>${d.fields[field] ? inline(d.fields[field], ctxFor(d)) : ''}</td></tr>`).join('')
        + '</tbody></table></div>'
      : '<p class="muted">None.</p>');
    const probHtml = problems.length
      ? `<section><h2 id="problems">Blocks that do not parse <span class="count">${problems.length}</span></h2><div class="table-wrap"><table class="report"><thead><tr><th>page</th><th>detail</th></tr></thead><tbody>${problems.map((f) => `<tr><td><a href="${rel(at, pageOut(f.path))}">${esc(f.path)}</a></td><td>${esc(f.detail)}</td></tr>`).join('')}</tbody></table></div></section>`
      : '';
    write(at, layout(at, 'Decision log', `<h1>Decision log</h1><p class="muted">Every <code>&gt; [!${esc(rules.decision.callout)}]</code> block of the corpus. ${open.length} open, ${decided.length} decided, ${withdrawn.length} withdrawn.</p>`
      + `<section><h2 id="open">Open <span class="count">${open.length}</span></h2>${openHtml || '<p class="muted">None.</p>'}</section>`
      + `<section><h2 id="decided">Decided <span class="count">${decided.length}</span></h2>${closedTable(decided, 'Answer')}</section>`
      + `<section><h2 id="withdrawn">Withdrawn <span class="count">${withdrawn.length}</span></h2>${closedTable(withdrawn, 'Why')}</section>`
      + probHtml, { active: at }));
  }

  // ----- The check result.
  {
    const at = 'checks.html';
    const rows = check.findings.map((f) => `<tr><td>${esc(f.rule)}</td><td><a href="${rel(at, pageOut(f.path))}">${esc(f.path)}</a></td><td>${esc(f.detail)}</td></tr>`).join('');
    write(at, layout(at, 'Checks', `<h1>Checks</h1>${checkSummary(check)}<h2>Findings <span class="count">${check.findings.length}</span></h2>`
      + `<div class="filters"><input type="search" data-filter placeholder="Filter rows" aria-label="Filter rows"><span class="muted" data-filter-count>${check.findings.length} rows</span></div>`
      + `<div class="table-wrap"><table class="report sortable"><thead><tr><th>rule</th><th>page</th><th>detail</th></tr></thead><tbody>${rows}</tbody></table></div>`, { active: at }));
  }

  // ----- The home page, and the search page.
  const searchBox = '<div class="search"><input type="search" id="search-q" placeholder="Search titles, ids and text" aria-label="Search" autocomplete="off"><div id="search-results" class="search-results" aria-live="polite"></div></div>';
  {
    const at = 'index.html';
    const docs = entries.filter((e) => e.isDocument);
    const kindRows = reportKinds.map((p) => `<tr><td><a href="reports/${esc(p)}.html">${esc(kindName(p))}</a></td><td><code>${esc(p)}</code></td><td class="num">${countOf(p)}</td></tr>`).join('')
      + `<tr><td><a href="reports/other.html">Other pages</a></td><td></td><td class="num">${others.length}</td></tr>`;
    const byState = new Map();
    for (const e of docs) {
      const s = pageState(rules, e.status) || 'unknown';
      byState.set(s, (byState.get(s) || 0) + 1);
    }
    const stateRows = [...stateOrder, 'unknown'].filter((s) => s !== 'unknown' || byState.get(s))
      .map((s) => `<tr><td>${stateBadge(s)}</td><td>${esc(meaning[s] || 'No status, or a status that is not a declared word.')}</td><td class="num">${byState.get(s) || 0}</td></tr>`).join('');
    const body = `<h1>${esc(name_)}</h1>
<p class="lead">${docs.length} documents and ${others.length} other pages.</p>
${searchBox}
<div class="cards">
<a class="card card-open" href="decisions.html#open"><span class="big">${open.length}</span> open decisions</a>
<a class="card" href="decisions.html#decided"><span class="big">${decided.length}</span> decided</a>
<a class="card ${check.exitCode === 0 ? 'card-ok' : 'card-bad'}" href="checks.html"><span class="big">${check.findings.length}</span> check findings · ${check.exitCode === 0 ? 'clean' : 'not clean'}</a>
</div>
<h2>Kinds</h2><div class="table-wrap"><table class="report"><thead><tr><th>kind</th><th>prefix</th><th class="num">pages</th></tr></thead><tbody>${kindRows}</tbody></table></div>
<h2>Page states</h2><div class="table-wrap"><table class="report"><thead><tr><th>state</th><th>meaning</th><th class="num">documents</th></tr></thead><tbody>${stateRows}</tbody></table></div>
<h2>Check</h2>${checkSummary(check)}`;
    write(at, layout(at, 'Home', body, { search: true, active: at }));
    write('search.html', layout('search.html', 'Search', `<h1>Search</h1>${searchBox}`, { search: true }));
  }

  // ----- The search index: a script that sets a global, so file:// works.
  const index = entries.map((e) => ({
    t: e.title, i: e.id || e.docId || e.stem, h: pageOut(e.path),
    s: pageState(rules, e.status) || '', x: plainText(e.body).slice(0, INDEX_TEXT_CAP),
  }));
  const indexJs = `window.GAKS_SEARCH = ${JSON.stringify(index)};\n`;
  write('assets/search-index.js', indexJs);
  write(MARKER, JSON.stringify({ name: name_, 'gaks-version': rules['gaks-version'] || null, documents: entries.filter((e) => e.isDocument).length, pages: others.length, decisions: { open: open.length, decided: decided.length, withdrawn: withdrawn.length } }, null, 2) + '\n');

  // ----- Write.
  prepareOut(out);
  let bytes = 0, files = 0;
  for (const [p, content] of written) {
    const full = join(out, ...p.split('/'));
    mkdirSync(join(full, '..'), { recursive: true });
    writeFileSync(full, content);
    bytes += Buffer.byteLength(content); files++;
  }
  for (const p of toCopy) {
    const full = join(out, ...fileOut(p).split('/'));
    mkdirSync(join(full, '..'), { recursive: true });
    cpSync(join(root, ...p.split('/')), full);
    bytes += statSync(full).size; files++;
  }
  const assets = new URL('./assets/', import.meta.url);
  for (const a of readdirSync(assets)) {
    const full = join(out, 'assets', a);
    cpSync(new URL(a, assets), full);
    bytes += statSync(full).size; files++;
  }
  return {
    files, bytes, documents: entries.filter((e) => e.isDocument).length, pages: others.length,
    indexBytes: Buffer.byteLength(indexJs), decisions: { open: open.length, decided: decided.length, withdrawn: withdrawn.length },
    check,
  };

  function checkSummary(c) {
    const rows = RULES.map((r) => {
      const rt = c.ratchets[r];
      const verdict = rt ? (rt.over ? '<span class="badge bad">over the ceiling</span>' : '<span class="badge ok">at or under</span>')
        : (c.counts[r] ? '<span class="badge bad">finding</span>' : '<span class="badge ok">none</span>');
      return `<tr><td><code>${esc(r)}</code></td><td class="num">${c.counts[r] || 0}</td><td class="num">${rt ? rt.ceiling : ''}</td><td>${verdict}</td></tr>`;
    }).join('');
    return `<p>The check is <strong>${c.exitCode === 0 ? 'clean' : 'not clean'}</strong>. A ratchet is a count that may only go down: it fails only over its ceiling.</p>`
      + `<div class="table-wrap"><table class="report"><thead><tr><th>rule</th><th class="num">count</th><th class="num">ratchet ceiling</th><th>result</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }
}

/** An empty or missing folder, or a site this tool built: else refuse. */
function prepareOut(out) {
  if (existsSync(out)) {
    if (!statSync(out).isDirectory()) throw new Error(`--out ${out} is a file`);
    const items = readdirSync(out);
    if (items.length && !items.includes(MARKER)) {
      throw new Error(`--out ${out} is not empty and holds no ${MARKER}. A site is written into an empty folder or over a site`);
    }
    for (const i of items) rmSync(join(out, i), { recursive: true, force: true });
  }
  mkdirSync(out, { recursive: true });
}

// ---------------------------------------------------------------- the CLI

export function parseArgs(argv) {
  const opts = { rules: null, root: null, out: null, name: null, help: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') opts.help = true;
    else if (['--rules', '--root', '--out', '--name'].includes(a)) {
      const v = argv[i + 1];
      if (v === undefined || (v.startsWith('--') && a !== '--name')) throw new RulesError(`${a} needs a value`);
      opts[a.slice(2)] = v;
      i++;
    } else throw new RulesError(`unknown argument: ${a}`);
  }
  return opts;
}

export async function main(argv, out = process.stdout, err = process.stderr) {
  let opts, rules;
  try {
    opts = parseArgs(argv);
    if (opts.help) { out.write(USAGE + '\n'); return 0; }
    if (!opts.rules || !opts.root || !opts.out) throw new RulesError('--rules, --root and --out are all needed');
    let st;
    try { st = statSync(opts.root); } catch { st = null; }
    if (!st || !st.isDirectory()) throw new RulesError(`--root ${opts.root} is not a directory`);
    rules = loadRules(opts.rules);
  } catch (e) {
    if (!(e instanceof RulesError)) throw e;
    err.write(`site: ${e.message}\n${USAGE}\n`);
    return 2;
  }
  try {
    const t0 = Date.now();
    const marked = await loadMarked();
    const r = buildSite({ rules, root: opts.root, out: opts.out, name: opts.name, marked });
    const secs = ((Date.now() - t0) / 1000).toFixed(1);
    out.write(`site: ${r.documents} documents, ${r.pages} other pages, ${r.files} files, ${(r.bytes / 1048576).toFixed(1)} MB, `
      + `search index ${(r.indexBytes / 1024).toFixed(0)} KB, decisions ${r.decisions.open} open / ${r.decisions.decided} decided / ${r.decisions.withdrawn} withdrawn, ${secs} s\n`);
    return 0;
  } catch (e) {
    err.write(`site: FAILED: ${e.stack || e.message}\n`);
    return 1;
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) {
  process.exitCode = await main(process.argv.slice(2));
}
