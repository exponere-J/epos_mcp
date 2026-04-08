import fs from "node:fs";
import path from "node:path";
import { createTelemetryRun } from "../telemetry_client";
import { validateOrThrow } from "../schema_runtime";

function isoNow() {
  return new Date().toISOString();
}

function writeFileSafe(p: string, content: string) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content, "utf-8");
}

function parseArgs(): { request: string; mode?: string } {
  const args = process.argv.slice(2);
  let request = "";
  let mode = "dry_run";

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--request" && i + 1 < args.length) {
      request = args[i + 1];
      i++;
    } else if (args[i] === "--mode" && i + 1 < args.length) {
      mode = args[i + 1];
      i++;
    }
  }

  return { request, mode };
}

async function main() {
  const telemetry = createTelemetryRun();
  const runId = telemetry.runId;
  const { request } = parseArgs();

  if (!request) {
    telemetry.emit({
      name: "deploy.missing_request",
      level: "error", 
      fields: { run_id: runId, code: "DEPLOY_MISSING_REQUEST" }
    });
    await telemetry.flush();
    process.exit(1);
  }

  if (!fs.existsSync(request)) {
    telemetry.emit({
      name: "deploy.request_not_found",
      level: "error",
      fields: { run_id: runId, request_path: request }
    });
    await telemetry.flush();
    process.exit(1);
  }

  const deployRequest = JSON.parse(fs.readFileSync(request, "utf-8"));
  validateOrThrow("core.platform_deploy_request", deployRequest);

  const outDir = path.join(process.cwd(), "runs", runId, "deploy", deployRequest.platform);
  
  // Create deployment plan (dry-run mode)
  const deploymentPlan = {
    schema_id: "core.platform_deployment",
    run_id: runId,
    product_id: deployRequest.product_id,
    platform: deployRequest.platform,
    mode: "dry_run",
    listing: {
      id: null,
      url: null,
      status: "planned"
    },
    actions: [
      {
        kind: "validate_pack",
        request_fingerprint: "mock_fingerprint",
        outcome: "success"
      },
      {
        kind: "prepare_listing", 
        request_fingerprint: "mock_fingerprint",
        outcome: "success"
      }
    ],
    asset_uploads: [],
    receipts: [],
    timestamps: {
      started: isoNow(),
      completed: isoNow()
    }
  };

  validateOrThrow("core.platform_deployment", deploymentPlan);
  writeFileSafe(path.join(outDir, "deployment_plan.json"), JSON.stringify(deploymentPlan, null, 2));

  telemetry.emit({
    name: "deploy.plan_created",
    level: "info",
    fields: { 
      run_id: runId,
      product_id: deployRequest.product_id,
      platform: deployRequest.platform,
      mode: "dry_run"
    }
  });

  await telemetry.flush();
}

main().catch(async (err) => {
  console.error(err);
  try {
    const telemetry = createTelemetryRun();
    telemetry.emit({
      name: "deploy.failed",
      level: "error", 
      fields: { message: String((err as any)?.message ?? err) }
    });
    await telemetry.flush();
  } catch {}
  process.exit(1);
});