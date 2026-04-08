
import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";

import { createTelemetryRun } from "../telemetry_client";
import { validateOrThrow } from "../schema_runtime";

function isoNow() {
  return new Date().toISOString();
}

function writeFileSafe(p: string, content: string) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content, "utf-8");
}

function hasDependencyGrant(): boolean {
  const p = path.join(process.cwd(), "grants.local.json");
  if (!fs.existsSync(p)) return false;
  try {
    const j = JSON.parse(fs.readFileSync(p, "utf-8"));
    return j?.change_dependencies === true;
  } catch {
    return false;
  }
}

function exec(cmd: string): { ok: boolean; code: number; stdout: string; stderr: string } {
  try {
    const stdout = execSync(cmd, { stdio: ["ignore", "pipe", "pipe"], encoding: "utf-8" }) as string;
    return { ok: true, code: 0, stdout, stderr: "" };
  } catch (e: any) {
    const stdout = e?.stdout?.toString?.() ?? "";
    const stderr = e?.stderr?.toString?.() ?? e?.message ?? "";
    return { ok: false, code: typeof e?.status === "number" ? e.status : 1, stdout, stderr };
  }
}

async function main() {
  const telemetry = createTelemetryRun();
  const runId = telemetry.runId;
  const outDir = path.join(process.cwd(), "runs", runId, "health");

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

  validateOrThrow("core.remediation_plan", plan);
  writeFileSafe(path.join(outDir, "remediation_plan.json"), JSON.stringify(plan, null, 2));

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

    writeFileSafe(
      path.join(outDir, `receipt_${a.kind}.txt`),
      `CMD: ${a.cmd}\nCODE: ${r.code}\n\nSTDOUT:\n${r.stdout}\n\nSTDERR:\n${r.stderr}\n`
    );

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
    const telemetry = createTelemetryRun();
    telemetry.emit({
      name: "heal.failed",
      level: "error",
      fields: { message: String((err as any)?.message ?? err) }
    });
    await telemetry.flush();
  } catch {}
  process.exit(1);
});
