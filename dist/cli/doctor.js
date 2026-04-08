"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
const node_child_process_1 = require("node:child_process");
const index_1 = require("../telemetry_client/index");
const index_2 = require("../schema_runtime/index");
function isoNow() {
    return new Date().toISOString();
}
function writeFileSafe(p, content) {
    node_fs_1.default.mkdirSync(node_path_1.default.dirname(p), { recursive: true });
    node_fs_1.default.writeFileSync(p, content, "utf-8");
}
function execJson(cmd) {
    try {
        const stdout = (0, node_child_process_1.execSync)(cmd, { stdio: ["ignore", "pipe", "pipe"], encoding: "utf-8" });
        const json = stdout ? JSON.parse(stdout) : null;
        return { ok: true, stdout, stderr: "", code: 0, json };
    }
    catch (e) {
        const stdout = e?.stdout?.toString?.() ?? "";
        const stderr = e?.stderr?.toString?.() ?? e?.message ?? "";
        let json = null;
        try {
            if (stdout)
                json = JSON.parse(stdout);
        }
        catch {
            // best-effort
        }
        return { ok: false, stdout, stderr, code: typeof e?.status === "number" ? e.status : 1, json };
    }
}
function countDeprecatedFromNpmLs(npmLs) {
    let count = 0;
    const walk = (node) => {
        if (!node || typeof node !== "object")
            return;
        if (typeof node.deprecated === "string" && node.deprecated.length > 0)
            count += 1;
        const deps = node.dependencies;
        if (deps && typeof deps === "object") {
            for (const k of Object.keys(deps))
                walk(deps[k]);
        }
    };
    walk(npmLs);
    return count;
}
function countOutdated(npmOutdated) {
    if (!npmOutdated || typeof npmOutdated !== "object")
        return 0;
    return Object.keys(npmOutdated).length;
}
function vulnSummary(npmAudit) {
    const v = npmAudit?.metadata?.vulnerabilities;
    return {
        critical: Number(v?.critical ?? 0),
        high: Number(v?.high ?? 0),
        moderate: Number(v?.moderate ?? 0),
        low: Number(v?.low ?? 0),
    };
}
function mdReport(report) {
    const v = report.findings.vuln_summary;
    return [
        `# EPOS Dependency Health Report`,
        ``,
        `- ts: ${report.ts}`,
        `- run_id: ${report.run_id}`,
        `- node: ${report.node}`,
        `- npm: ${report.npm}`,
        ``,
        `## Findings`,
        `- Deprecated packages: ${report.findings.deprecated_count}`,
        `- Outdated direct packages: ${report.findings.outdated_count}`,
        `- Vulnerabilities: critical=${v.critical}, high=${v.high}, moderate=${v.moderate}, low=${v.low}`,
        ``,
        `## Violations`,
        ...(report.violations.length ? report.violations.map((x) => `- ${x.code}: ${x.message}`) : [`- None`]),
        ``,
        `## Notes`,
        ...(report.findings.notes.length ? report.findings.notes.map((n) => `- ${n}`) : [`- None`]),
        ``,
    ].join("\n");
}
async function main() {
    const telemetry = (0, index_1.createTelemetryRun)();
    const runId = telemetry.getEnvelope().run_id;
    const outDir = node_path_1.default.join(process.cwd(), "runs", runId, "health");
    telemetry.emit({ name: "health.scan_started", level: "info", fields: { run_id: runId } });
    const nodeVer = process.versions.node;
    const npmVer = (() => {
        try {
            return (0, node_child_process_1.execSync)("npm -v", { stdio: ["ignore", "pipe", "pipe"], encoding: "utf-8" }).trim();
        }
        catch {
            return "unknown";
        }
    })();
    const npmLs = execJson("npm ls --json");
    const npmOutdated = execJson("npm outdated --json");
    const npmAudit = execJson("npm audit --json");
    const deprecatedCount = npmLs.json ? countDeprecatedFromNpmLs(npmLs.json) : 0;
    const outdatedCount = countOutdated(npmOutdated.json);
    const vs = vulnSummary(npmAudit.json);
    const violations = [];
    if (deprecatedCount > 0)
        violations.push({ code: "HEALTH_DEPRECATIONS_FOUND", message: `${deprecatedCount} deprecated packages detected` });
    if (outdatedCount > 0)
        violations.push({ code: "HEALTH_OUTDATED_FOUND", message: `${outdatedCount} outdated direct dependencies detected` });
    if (vs.critical + vs.high + vs.moderate + vs.low > 0) {
        violations.push({ code: "HEALTH_VULNERABILITIES_FOUND", message: `vulnerabilities present (critical=${vs.critical}, high=${vs.high})` });
    }
    const report = {
        schema_id: "core.health_report",
        ts: isoNow(),
        run_id: runId,
        node: nodeVer,
        npm: npmVer,
        findings: {
            deprecated_count: deprecatedCount,
            outdated_count: outdatedCount,
            vuln_summary: vs,
            notes: ["Phase 1: report-only by default; remediation requires explicit grant change_dependencies."],
        },
        raw: {
            npm_ls: npmLs.json ?? {},
            npm_outdated: npmOutdated.json ?? null,
            npm_audit: npmAudit.json ?? null,
        },
        violations,
    };
    (0, index_2.validateOrThrow)("core.health_report", report);
    writeFileSafe(node_path_1.default.join(outDir, "health_report.json"), JSON.stringify(report, null, 2));
    writeFileSafe(node_path_1.default.join(outDir, "health_report.md"), mdReport(report));
    telemetry.emit({
        name: "health.report_written",
        level: "info",
        fields: { run_id: runId, out_dir: node_path_1.default.relative(process.cwd(), outDir) },
    });
    if (violations.length) {
        telemetry.emit({
            name: "health.violations_found",
            level: "warn",
            fields: { run_id: runId, violations: violations.map((v) => v.code) },
        });
    }
    await telemetry.flush();
}
main().catch(async (err) => {
    // eslint-disable-next-line no-console
    console.error(err);
    try {
        const telemetry = (0, index_1.createTelemetryRun)();
        telemetry.emit({ name: "health.scan_failed", level: "error", fields: { message: String(err?.message ?? err) } });
        await telemetry.flush();
    }
    catch { }
    process.exit(1);
});
//# sourceMappingURL=doctor.js.map