// src/telemetry_client/bridge.ts
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

export type TelemetryEvent = {
  name: string;
  level: "debug" | "info" | "warn" | "error";
  fields: Record<string, unknown>;
};

export type TelemetryEnvelope = {
  schema_id: "core.telemetry_envelope";
  ts: string;
  run_id: string;
  app: string;
  version: string;
};

export type TelemetryClient = {
  emit: (evt: TelemetryEvent) => void;
  flush: () => Promise<void>;
  getEnvelope: () => TelemetryEnvelope;
};

export type TelemetryRunOptions = {
  runDir?: string; // default: <cwd>/runs
  runId?: string;  // default: uuid
};

function isoNow() {
  return new Date().toISOString();
}

function mkdirp(p: string) {
  try {
    fs.mkdirSync(p, { recursive: true });
  } catch {
    // keep going (tests include "continue on write fail")
  }
}

function safeWrite(p: string, content: string) {
  try {
    mkdirp(path.dirname(p));
    fs.writeFileSync(p, content, "utf-8");
  } catch {
    // keep going (must not throw)
  }
}

export function createTelemetryRun(opts: TelemetryRunOptions = {}): TelemetryClient {
  const run_id = opts.runId ?? crypto.randomUUID();
  const runRoot = opts.runDir ?? path.join(process.cwd(), "runs");
  const outDir = path.join(runRoot, run_id, "telemetry");

  const envelope: TelemetryEnvelope = {
    schema_id: "core.telemetry_envelope",
    ts: isoNow(),
    run_id,
    app: "epos_mcp",
    version: "0.1.0"
  };

  const events: Array<TelemetryEvent & { ts: string; run_id: string }> = [];

  const emit = (evt: TelemetryEvent) => {
    events.push({ ...evt, ts: isoNow(), run_id });
  };

  const flush = async () => {
    // Must never throw, even if mkdir/write fails.
    safeWrite(path.join(outDir, "envelope.json"), JSON.stringify(envelope, null, 2));

    const lines = events.map((e) => JSON.stringify(e)).join("\n") + (events.length ? "\n" : "");
    safeWrite(path.join(outDir, "events.jsonl"), lines);
  };

  const getEnvelope = () => envelope;

  return { emit, flush, getEnvelope };
}

