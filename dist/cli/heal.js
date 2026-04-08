"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
const node_child_process_1 = require("node:child_process");
const telemetry_client_1 = require("../telemetry_client");
const schema_runtime_1 = require("../schema_runtime");
function isoNow() {
    return new Date().toISOString();
}
function writeFileSafe(p, content) {
    node_fs_1.default.mkdirSync(node_path_1.default.dirname(p), { recursive: true });
    node_fs_1.default.writeFileSync(p, content, "utf-8");
}
function hasDependencyGrant() {
    const p = node_path_1.default.join(process.cwd(), "grants.local.json");
    if (!node_fs_1.default.existsSync(p))
        return false;
    try {
        const j = JSON.parse(node_fs_1.default.readFileSync(p, "utf-8"));
        return j?.change_dependencies === true;
    }
    catch {
        return false;
    }
}
function exec(cmd) {
    try {
        const stdout = (0, node_child_process_1.execSync)(cmd, { stdio: ["ignore", "pipe", "pipe"], encoding: "utf-8" });
        return { ok: true, code: 0, stdout, stderr: "" };
    }
    catch (e) {
        const stdout = e?.stdout?.toString?.() ?? "";
        const stderr = e?.stderr?.toString?.() ?? e?.message ?? "";
        return { ok: false, code: typeof e?.status === "number" ? e.status : 1, stdout, stderr };
    }
}
async function main() {
    const telemetry = (0, telemetry_client_1.createTelemetryRun)();
    const runId = telemetry.runId;
    const outDir = node_path_1.default.join(process.cwd(), "runs", runId, "health");
    if (!hasDependencyGrant()) {
        telemetry.emit({
            name: "heal.permission_denied",
            level: "warn",
            fields: { run_id: runId, code: "HEAL_PERMISSION_DENIED" }
        });
        await telemetry.flush();
        process.exit(2);
    }
    const plan = {
        schema_id: "core.remediation_plan",
        ts: isoNow(),
        run_id: runId,
        level: 1,
        actions: [
            { kind: "npm_update", cmd: "npm update", reason: "Apply non-breaking updates within declared semver ranges." },
            { kind: "npm_install", cmd: "npm install", reason: "Regenerate lockfile after updates." },
            { kind: "npm_test", cmd: "npm test", reason: "Prove integrity after dependency changes." }
        ],
        expected_outcome: ["Reduced deprecated/outdated packages (where possible)", "No new test failures introduced"]
    };
    (0, schema_runtime_1.validateOrThrow)("core.remediation_plan", plan);
    writeFileSafe(node_path_1.default.join(outDir, "remediation_plan.json"), JSON.stringify(plan, null, 2));
    telemetry.emit({
        name: "heal.started",
        level: "info",
        fields: { run_id: runId, level: plan.level }
    });
    for (const a of plan.actions) {
        telemetry.emit({
            name: "heal.step_started",
            level: "info",
            fields: { run_id: runId, kind: a.kind, cmd: a.cmd }
        });
        const r = exec(a.cmd);
        writeFileSafe(node_path_1.default.join(outDir, `receipt_${a.kind}.txt`), `CMD: ${a.cmd}\nCODE: ${r.code}\n\nSTDOUT:\n${r.stdout}\n\nSTDERR:\n${r.stderr}\n`);
        if (!r.ok) {
            telemetry.emit({
                name: "heal.step_failed",
                level: "error",
                fields: { run_id: runId, kind: a.kind, code: r.code }
            });
            if (a.kind === "npm_test") {
                telemetry.emit({
                    name: "heal.failed_tests",
                    level: "error",
                    fields: { run_id: runId, code: "HEAL_FAILED_TESTS" }
                });
            }
            await telemetry.flush();
            process.exit(1);
        }
        telemetry.emit({
            name: "heal.step_ok",
            level: "info",
            fields: { run_id: runId, kind: a.kind }
        });
    }
    telemetry.emit({
        name: "heal.applied_success",
        level: "info",
        fields: { run_id: runId, code: "HEAL_APPLIED_SUCCESS" }
    });
    await telemetry.flush();
}
main().catch(async (err) => {
    // eslint-disable-next-line no-console
    console.error(err);
    try {
        const telemetry = (0, telemetry_client_1.createTelemetryRun)();
        telemetry.emit({
            name: "heal.failed",
            level: "error",
            fields: { message: String(err?.message ?? err) }
        });
        await telemetry.flush();
    }
    catch { }
    process.exit(1);
});
//# sourceMappingURL=heal.js.map