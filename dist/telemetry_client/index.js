"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createTelemetryRun = createTelemetryRun;
const node_path_1 = __importDefault(require("node:path"));
const fs_sink_1 = require("./fs_sink");
const validate_1 = require("./validate");
function isoNow() {
    return new Date().toISOString();
}
function defaultRunId() {
    // deterministic enough for tests; real system can swap later
    return `run_${Date.now()}`;
}
function defaultRunDir(runId) {
    return node_path_1.default.join(process.cwd(), "runs", runId);
}
function createTelemetryRun(opts) {
    const runId = opts?.runId ?? defaultRunId();
    const runDir = opts?.runDir ?? defaultRunDir(runId);
    const telemetryFile = node_path_1.default.join(runDir, "telemetry.json");
    // Track whether a completion has already been emitted (manual or automatic)
    let completionSeen = false;
    // Ensure runDir exists (binding)
    try {
        (0, fs_sink_1.mkdirp)(runDir);
    }
    catch (e) {
        // best-effort; continue
        // eslint-disable-next-line no-console
        console.error("TELEMETRY_WRITE_FAILED", String(e?.message ?? e));
    }
    const emit = (event) => {
        if (event?.name === "system.run_completed") {
            completionSeen = true;
        }
        const envelope = {
            schema_id: "core.telemetry_envelope",
            ts: isoNow(),
            run_id: runId,
            event,
        };
        // Validate by schemaId constant (binding)
        (0, validate_1.validateEnvelopeOrThrow)(envelope);
        // Write NDJSON line (binding). If write fails, log + continue.
        try {
            (0, fs_sink_1.appendNdjsonLine)(telemetryFile, envelope);
        }
        catch (e) {
            // eslint-disable-next-line no-console
            console.error("TELEMETRY_WRITE_FAILED", String(e?.message ?? e));
        }
    };
    const flush = async () => {
        // Binding: flush emits system.run_completed only if not already present
        if (!completionSeen) {
            emit({
                name: "system.run_completed",
                level: "info",
                fields: {},
            });
            completionSeen = true;
        }
    };
    return {
        getEnvelope() {
            return { run_id: runId, run_dir: runDir };
        },
        emit,
        flush,
    };
}
//# sourceMappingURL=index.js.map