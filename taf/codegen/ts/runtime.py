"""Runtime support sources for TypeScript Playwright — journal and sink."""

from .common import _HEADER


def _journal_source():
    return _HEADER + """
// @concept CONCEPT-taf-v1-004-01-the-artifacts

import * as fs from "node:fs";
import * as path from "node:path";

class TafJournal {
  private currentStream: fs.WriteStream | null = null;
  private currentPath: string | null = null;
  private startTime = 0;
  private dir: string | null = null;
  private noteT: number[] = [];
  private noteL: string[] = [];
  private lastOutcome = "passed";
  private readonly pools = new Map<string, string[]>();

  begin(runDir: string, testId: string): void {
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

  testDir(): string {
    if (!this.dir) throw new Error("journal not begun");
    return this.dir;
  }

  failed(): boolean {
    return this.lastOutcome === "failed";
  }

  mark(outcome: string): void {
    this.lastOutcome = outcome;
  }

  envPool(name: string): string {
    const v = process.env[name];
    if (!v || v.trim().length === 0) {
      throw new Error(`env-pool:${name} — the variable is unset or blank`);
    }
    if (!this.pools.has(name)) {
      this.pools.set(name, v.trim().split(/\\s+/));
    }
    const pool = this.pools.get(name)!;
    if (pool.length === 0) {
      throw new Error(`env-pool:${name} ran dry — every value is spent`);
    }
    return pool.shift()!;
  }

  note(label: string): void {
    this.event("note", { label });
    const elapsed = Date.now() - this.startTime;
    this.noteT.push(elapsed);
    this.noteL.push(label);
    console.log(label);
  }

  event(kind: string, fields: Record<string, any> = {}): void {
    const t = Date.now() - this.startTime;
    const line = JSON.stringify({ t, event: kind, ...fields }) + "\\n";
    if (this.currentStream) {
      this.currentStream.write(line);
    } else if (this.currentPath) {
      fs.appendFileSync(this.currentPath, line, "utf-8");
    }
  }

  private srtTs(ms: number): string {
    const h = Math.floor(ms / 3600000);
    const m = Math.floor((ms % 3600000) / 60000);
    const s = Math.floor((ms % 60000) / 1000);
    const rem = ms % 1000;
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(rem).padStart(3, "0")}`;
  }

  end(outcome = "passed"): void {
    if (outcome === "failed") {
      this.lastOutcome = "failed";
    }
    this.event("end", { outcome: this.lastOutcome });
    if (this.currentStream) {
      this.currentStream.end();
      this.currentStream = null;
    }
    if (this.dir && this.noteL.length > 0) {
      const parts: string[] = [];
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

export function fingerprint(name: string, err: any): string {
  const tail = String(err).replace(/(\\/\\S*\\/taf-run-\\S+|0x[0-9a-fA-F]+)/g, "~");
  return crypto.createHash("sha1").update(name + "\\n" + tail).digest("hex").slice(0, 12);
}

function ledgerPath(): string {
  return path.join(process.env["TAF_RESULTS"] || "results", "filed.json");
}

export function filed(fp: string): string | null {
  try {
    const p = ledgerPath();
    const data = JSON.parse(fs.readFileSync(p, "utf-8"));
    return data[fp]?.id ?? null;
  } catch {
    return null;
  }
}

export function record(fp: string, reportId: string): void {
  const p = ledgerPath();
  let led: Record<string, any> = {};
  try {
    led = JSON.parse(fs.readFileSync(p, "utf-8"));
  } catch {}
  led[fp] = { id: reportId, at: new Date().toISOString().slice(0, 19) };
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(led, null, 1), "utf-8");
}

function ednStr(s: string): string {
  return '"' + s.replace(/\\\\/g, "\\\\\\\\").replace(/"/g, '\\\\"') + '"';
}

function edn(v: any): string {
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

export async function fileReport(
  wsUrl: string,
  what: string,
  opts?: { url?: string; dom?: string; island?: string; timeoutMs?: number }
): Promise<string> {
  const rid = crypto.randomUUID();
  const cmd = {
    type: ":support/file-report",
    what,
    url: opts?.url || "",
    dom: opts?.dom || "",
    island: opts?.island || "",
  };
  const envelope = `{:t :dispatch :id ${ednStr(rid)} :command ${edn(cmd)}}`;
  return new Promise<string>((resolve, reject) => {
    // @ts-ignore
    const WsClass = typeof WebSocket !== "undefined" ? WebSocket : (globalThis as any).WebSocket;
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
    ws.onmessage = (event: any) => {
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
    ws.onerror = (err: any) => {
      clearTimeout(timer);
      reject(err);
    };
  });
}
"""
