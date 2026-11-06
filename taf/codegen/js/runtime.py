"""Runtime support sources for JavaScript ESM Playwright — journal and sink."""

from .common import _HEADER


def _journal_source():
    return _HEADER + """
// @concept CONCEPT-taf-v1-004-01-the-artifacts
// @concept CONCEPT-js-v1-001-01-object-freeze-and-destructuring

import * as fs from "node:fs";
import * as path from "node:path";

class TafJournal {
  constructor() {
    /** @type {{write: (s: string) => void, end: () => void} | null} */
    this.currentStream = null;
    /** @type {string | null} */
    this.currentPath = null;
    this.startTime = 0;
    /** @type {string | null} */
    this.dir = null;
    /** @type {number[]} */
    this.noteT = [];
    /** @type {string[]} */
    this.noteL = [];
    this.lastOutcome = "passed";
    /** @type {Map<string, string[]>} */
    this.pools = new Map();
  }

  /**
   * @param {string} runDir
   * @param {string} testId
   */
  begin(runDir, testId) {
    const d = path.join(runDir, testId.replace(/[^a-zA-Z0-9_-]/g, "_"));
    this.dir = d;
    fs.mkdirSync(d, { recursive: true });
    this.startTime = Date.now();
    this.noteT = [];
    this.noteL = [];
    this.lastOutcome = "passed";
    this.currentPath = path.join(d, "@@journal@@");
    this.currentStream = fs.createWriteStream(this.currentPath, { flags: "a", encoding: "utf-8" });
  }

  testDir() {
    if (!this.dir) throw new Error("journal not begun");
    return this.dir;
  }

  failed() {
    return this.lastOutcome === "failed";
  }

  /** @param {string} outcome */
  mark(outcome) {
    this.lastOutcome = outcome;
  }

  /** @param {string} name */
  envPool(name) {
    const v = process.env[name];
    if (!v || v.trim().length === 0) {
      throw new Error(`env-pool:${name} — the variable is unset or blank`);
    }
    if (!this.pools.has(name)) {
      this.pools.set(name, v.trim().split(/\\s+/));
    }
    const pool = this.pools.get(name);
    if (!pool || pool.length === 0) {
      throw new Error(`env-pool:${name} ran dry — every value is spent`);
    }
    return pool.shift();
  }

  /** @param {string} label */
  note(label) {
    this.event("note", { label });
    const elapsed = Date.now() - this.startTime;
    this.noteT.push(elapsed);
    this.noteL.push(label);
    console.log(label);
  }

  /**
   * @param {string} kind
   * @param {Record<string, any>} [fields]
   */
  event(kind, fields = {}) {
    const t = Date.now() - this.startTime;
    const line = JSON.stringify({ t, event: kind, ...fields }) + "\\n";
    if (this.currentStream) {
      this.currentStream.write(line);
    } else if (this.currentPath) {
      fs.appendFileSync(this.currentPath, line, "utf-8");
    }
  }

  /**
   * @private
   * @param {number} ms
   */
  srtTs(ms) {
    const h = Math.floor(ms / 3600000);
    const m = Math.floor((ms % 3600000) / 60000);
    const s = Math.floor((ms % 60000) / 1000);
    const rem = ms % 1000;
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(rem).padStart(3, "0")}`;
  }

  /** @param {string} [outcome] */
  end(outcome = "passed") {
    if (outcome === "failed") {
      this.lastOutcome = "failed";
    }
    this.event("end", { outcome: this.lastOutcome });
    if (this.currentStream) {
      this.currentStream.end();
      this.currentStream = null;
    }
    if (this.dir && this.noteL.length > 0) {
      const parts = [];
      for (let i = 0; i < this.noteL.length; i++) {
        const start = this.noteT[i];
        const end = i + 1 < this.noteL.length ? this.noteT[i + 1] : start + 2000;
        parts.push(`${i + 1}\\n${this.srtTs(start)} --> ${this.srtTs(end)}\\n${this.noteL[i]}\\n`);
      }
      const srtPath = path.join(this.dir, "@@subtitles@@");
      fs.writeFileSync(srtPath, parts.join("\\n"), "utf-8");
      try {
        const files = fs.readdirSync(this.dir);
        for (const file of files) {
          if (file.endsWith(".webm")) {
            const dest = path.join(this.dir, file.slice(0, -5) + ".srt");
            fs.copyFileSync(srtPath, dest);
          }
        }
      } catch (_ignored) {}
    }
  }
}

export const tafJournal = new TafJournal();
"""


def _sink_source():
    return _HEADER + """
// @concept CONCEPT-taf-v1-002-01-the-result-sink

import * as crypto from "node:crypto";
import * as fs from "node:fs";
import * as path from "node:path";

/**
 * @param {string} name
 * @param {any} err
 */
export function fingerprint(name, err) {
  const tail = String(err).replace(/(\\/\\S*\\/taf-run-\\S+|0x[0-9a-fA-F]+)/g, "~");
  return crypto.createHash("sha1").update(name + "\\n" + tail).digest("hex").slice(0, 12);
}

function ledgerPath() {
  return path.join(process.env["TAF_RESULTS"] || "results", "filed.json");
}

/** @param {string} fp */
export function filed(fp) {
  try {
    const p = ledgerPath();
    const data = JSON.parse(fs.readFileSync(p, "utf-8"));
    return data[fp]?.id ?? null;
  } catch {
    return null;
  }
}

/**
 * @param {string} fp
 * @param {string} reportId
 */
export function record(fp, reportId) {
  const p = ledgerPath();
  let led = {};
  try {
    led = JSON.parse(fs.readFileSync(p, "utf-8"));
  } catch {}
  led[fp] = { id: reportId, at: new Date().toISOString().slice(0, 19) };
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(led, null, 1), "utf-8");
}

/** @param {string} s */
function ednStr(s) {
  return '"' + s.replace(/\\\\/g, "\\\\\\\\").replace(/"/g, '\\\\"') + '"';
}

/** @param {any} v */
function edn(v) {
  if (typeof v === "object" && v !== null) {
    const items = Object.entries(v)
      .filter(([_, x]) => x !== null && x !== undefined)
      .map(([k, x]) => `:${k} ${edn(x)}`)
      .join(" ");
    return "{" + items + "}";
  }
  if (typeof v === "string" && v.startsWith(":")) {
    return v;
  }
  return ednStr(String(v));
}

/**
 * @param {string} wsUrl
 * @param {string} what
 * @param {{ url?: string; dom?: string; island?: string; timeoutMs?: number }} [opts]
 * @returns {Promise<string>}
 */
export async function fileReport(wsUrl, what, opts) {
  const rid = crypto.randomUUID();
  const cmd = {
    type: ":support/file-report",
    what,
    url: opts?.url || "",
    dom: opts?.dom || "",
    island: opts?.island || "",
  };
  const envelope = `{:t :dispatch :id ${ednStr(rid)} :command ${edn(cmd)}}`;
  return new Promise((resolve, reject) => {
    // @ts-ignore
    const WsClass = typeof WebSocket !== "undefined" ? WebSocket : globalThis.WebSocket;
    if (!WsClass) {
      return reject(new Error("WebSocket is not supported in this runtime"));
    }
    const ws = new WsClass(wsUrl, ["ikc3-bus"]);
    const timer = setTimeout(() => {
      try { ws.close(); } catch {}
      reject(new Error("Timeout waiting for fault report reply"));
    }, opts?.timeoutMs || 30000);

    ws.onopen = () => {
      ws.send(envelope);
    };
    ws.onmessage = (event) => {
      const msg = String(event.data);
      if (!msg.includes(`:id "${rid}"`) || !msg.includes(":reply")) {
        return;
      }
      clearTimeout(timer);
      try { ws.close(); } catch {}
      if (!msg.includes(":support/report-filed")) {
        return reject(new Error(`the bus refused the report: ${msg.slice(0, 300)}`));
      }
      const marker = ':report-id #uuid "';
      const idx = msg.indexOf(marker);
      if (idx === -1) {
        return reject(new Error("report-id marker not found"));
      }
      const start = idx + marker.length;
      const end = msg.indexOf('"', start);
      resolve(msg.slice(start, end));
    };
    ws.onerror = (err) => {
      clearTimeout(timer);
      reject(err);
    };
  });
}
"""
