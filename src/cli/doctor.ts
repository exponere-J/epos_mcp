import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";

import { createTelemetryRun } from "../telemetry_client/index";
import { validateOrThrow } from "../schema_runtime/index";

type CmdResult = { ok: boolean; stdout: string; stderr: string; code: number; json: any | null };

function isoNow() {
  return new Date().toISOString();
}

function writeFileSafe(p: string, content: string) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content, "utf-8");
}

function execJson(cmd: string): CmdResult {
  try {
    const stdout = execSync(cmd, { stdio: ["ignore", "pipe", "pipe"], encoding: "utf-8" }) as string;
    const json = stdout ? JSON.parse(stdout) : null;
    return { ok: true, stdout, stderr: "", code: 0, json };
  } catch (e: any) {
    const stdout = e?.stdout?.toString?.() ?? "";
    const stderr = e?.stderr?.toString?.() ?? e?.message ?? "";
    let json: any | null = null;
    try {
      if (stdout) json = JSON.parse(stdout);
    } catch {
      // best-effort
    }
    return { ok: false, stdout, stderr, code: typeof e?.status === "number" ? e.status : 1, json };
  }
}

function countDeprecatedFromNpmLs(npmLs: any): number {
  let count = 0;
  const walk = (node: any) => {
    if (!node || typeof node !== "object") return;
    if (typeof node.deprecated === "string" && node.deprecated.length > 0) count += 1;
    const deps = node.dependencies;
    if (deps && typeof deps === "object") {
      for (const k of Object.keys(deps)) walk(deps[k]);
    }
  };
  walk(npmLs);
  return count;
}

function countOutdated(npmOutdated: any | null): number {
  if (!npmOutdated || typeof npmOutdated !== "object") return 0;
  return Object.keys(npmOutdated).length;
}

function vulnSummary(npmAudit: any | null) {
  const v = npmAudit?.metadata?.vulnerabilities;
  return {
    critical: Number(v?.critical ?? 0),
    high: Number(v?.high ?? 0),
    moderate: Number(v?.moderate ?? 0),
    low: Number(v?.low ?? 0),
  };
}

function mdReport(report: any): string {
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
    ...(report.violations.length ? report.violations.map((x: any) => `- ${x.code}: ${x.message}`) : [`- None`]),
    ``,
    `## Notes`,
    ...(report.findings.notes.length ? report.findings.notes.map((n: string) => `- ${n}`) : [`- None`]),
    ``,
  ].join("\n");
}

async function main() {
  const telemetry = createTelemetryRun();
  const runId = telemetry.getEnvelope().run_id;

  const outDir = path.join(process.cwd(), "runs", runId, "health");

  telemetry.emit({ name: "health.scan_started", level: "info", fields: { run_id: runId } });

  const nodeVer = process.versions.node;
  const npmVer = (() => {
    try {
      return execSync("npm -v", { stdio: ["ignore", "pipe", "pipe"], encoding: "utf-8" }).trim();
    } catch {
      return "unknown";
    }
  })();

  const npmLs = execJson("npm ls --json");
  const npmOutdated = execJson("npm outdated --json");
  const npmAudit = execJson("npm audit --json");

  const deprecatedCount = npmLs.json ? countDeprecatedFromNpmLs(npmLs.json) : 0;
  const outdatedCount = countOutdated(npmOutdated.json);
  const vs = vulnSummary(npmAudit.json);

  const violations: Array<{ code: string; message: string }> = [];
  if (deprecatedCount > 0) violations.push({ code: "HEALTH_DEPRECATIONS_FOUND", message: `${deprecatedCount} deprecated packages detected` });
  if (outdatedCount > 0) violations.push({ code: "HEALTH_OUTDATED_FOUND", message: `${outdatedCount} outdated direct dependencies detected` });
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

  validateOrThrow("core.health_report", report);

  writeFileSafe(path.join(outDir, "health_report.json"), JSON.stringify(report, null, 2));
  writeFileSafe(path.join(outDir, "health_report.md"), mdReport(report));

  telemetry.emit({
    name: "health.report_written",
    level: "info",
    fields: { run_id: runId, out_dir: path.relative(process.cwd(), outDir) },
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
    const telemetry = createTelemetryRun();
    telemetry.emit({ name: "health.scan_failed", level: "error", fields: { message: String((err as any)?.message ?? err) } });
    await telemetry.flush();
  } catch {}
  process.exit(1);
});
