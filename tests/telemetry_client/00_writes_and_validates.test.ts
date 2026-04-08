import fs from "fs";
import path from "path";
import { createTelemetryRun } from "../../src/telemetry_client";

describe("Module 2: telemetry_client local sink", () => {
  test("writes validated envelopes to telemetry.json (NDJSON)", async () => {
    const runDir = path.join(process.cwd(), "tests", "fixtures", "telemetry_run_1");
    fs.rmSync(runDir, { recursive: true, force: true });

    const t = createTelemetryRun({ runDir, runId: "run_test_1" });

    t.emit({ name: "mission.received", level: "info", fields: { mission_id: "m1" } });
    await t.flush();

    const filePath = path.join(runDir, "telemetry.json");
    expect(fs.existsSync(filePath)).toBe(true);

    const lines = fs.readFileSync(filePath, "utf-8").trim().split("\n").filter(Boolean);
    expect(lines.length).toBeGreaterThanOrEqual(2);

    const env0 = JSON.parse(lines[0]);
    expect(env0.schema_id).toBe("core.telemetry_envelope");
    expect(env0.run_id).toBe("run_test_1");
    expect(env0.event.name).toBe("mission.received");
  });
});
