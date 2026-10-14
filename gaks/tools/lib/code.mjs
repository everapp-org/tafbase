// code.mjs — which parts of a Markdown text are code.
//
//
// A wikilink or a decision block inside code is an example, not a link or a
// decision. Both readers ask this module.

/**
 * For each line of `lines`, true when the line is inside a fenced code block
 * (the fence lines included). A fence is three or more backticks or tildes;
 * it closes with the same character, at least as many, and nothing else but
 * spaces and tabs. src/gaks/decisions.clj `fenced-lines` is the same rule.
 */
export function fencedLines(lines) {
  const out = new Array(lines.length).fill(false);
  let fence = null; // {ch, n}
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (fence === null) {
      const m = /^ {0,3}(`{3,}|~{3,})(.*)$/s.exec(l);
      if (m && !(m[1][0] === '`' && m[2].includes('`'))) {
        fence = { ch: m[1][0], n: m[1].length };
        out[i] = true;
      }
    } else {
      out[i] = true;
      const m = /^ {0,3}(`{3,}|~{3,})[ \t]*$/.exec(l);
      if (m && m[1][0] === fence.ch && m[1].length >= fence.n) fence = null;
    }
  }
  return out;
}

/**
 * The [start, end) ranges of the inline code spans of one line. A span opens
 * with a run of N backticks and closes with the next run of exactly N. A run
 * with no closing run is plain text.
 */
export function inlineCodeRanges(line) {
  const runs = [];
  const re = /`+/g;
  let m;
  while ((m = re.exec(line)) !== null) runs.push({ at: m.index, n: m[0].length });
  const ranges = [];
  let i = 0;
  while (i < runs.length) {
    let j = i + 1;
    while (j < runs.length && runs[j].n !== runs[i].n) j++;
    if (j < runs.length) {
      ranges.push([runs[i].at, runs[j].at + runs[j].n]);
      i = j + 1;
    } else {
      i++;
    }
  }
  return ranges;
}

/** Is `index` inside one of `ranges`? */
export function inRanges(ranges, index) {
  return ranges.some(([a, b]) => index >= a && index < b);
}
