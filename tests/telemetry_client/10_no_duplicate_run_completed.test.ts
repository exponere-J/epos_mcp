import fs from "fs";
import path from "path";
import { createTelemetryRun } from "../../src/telemetry_client";

describe("Module 2: no duplicate system.run_completed", () => {
  test("flush emits system.run_completed once even if user emits it", async () => {
    const runDir = path.join(process.cwd(), "tests", "fixtures", "telemetry_run_2");
    fs.rmSync(runDir, { recursive: true, force: true });

    const t = createTelemetryRun({ runDir, runId: "run_test_2" });

    // user emits completion early
    t.emit({ name: "system.run_completed", level: "info", fields: { note: "manual" } });

    // flush should not emit another completion
    await t.flush();

    const lines = fs.readFileSync(path.join(runDir, "telemetry.json"), "utf-8").trim().split("\n").filter(Boolean);
    const completions = lines.map((l) => JSON.parse(l)).filter((e) => e.event?.name === "system.run_completed");
    expect(completions).toHaveLength(1);
  });
});
