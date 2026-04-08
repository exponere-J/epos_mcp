"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createTelemetryRun = createTelemetryRun;
// src/telemetry_client/bridge.ts
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
const node_crypto_1 = __importDefault(require("node:crypto"));
function isoNow() {
    return new Date().toISOString();
}
function mkdirp(p) {
    try {
        node_fs_1.default.mkdirSync(p, { recursive: true });
    }
    catch {
        // keep going (tests include "continue on write fail")
    }
}
function safeWrite(p, content) {
    try {
        mkdirp(node_path_1.default.dirname(p));
        node_fs_1.default.writeFileSync(p, content, "utf-8");
    }
    catch {
        // keep going (must not throw)
    }
}
function createTelemetryRun(opts = {}) {
    const run_id = opts.runId ?? node_crypto_1.default.randomUUID();
    const runRoot = opts.runDir ?? node_path_1.default.join(process.cwd(), "runs");
    const outDir = node_path_1.default.join(runRoot, run_id, "telemetry");
    const envelope = {
        schema_id: "core.telemetry_envelope",
        ts: isoNow(),
        run_id,
        app: "epos_mcp",
        version: "0.1.0"
    };
    const events = [];
    const emit = (evt) => {
        events.push({ ...evt, ts: isoNow(), run_id });
    };
    const flush = async () => {
        // Must never throw, even if mkdir/write fails.
        safeWrite(node_path_1.default.join(outDir, "envelope.json"), JSON.stringify(envelope, null, 2));
        const lines = events.map((e) => JSON.stringify(e)).join("\n") + (events.length ? "\n" : "");
        safeWrite(node_path_1.default.join(outDir, "events.jsonl"), lines);
    };
    const getEnvelope = () => envelope;
    return { emit, flush, getEnvelope };
}
//# sourceMappingURL=bridge.js.map