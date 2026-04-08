import path from "path";
import { createTelemetryRun } from "../../src/telemetry_client";

describe("Module 2: mkdirp and continue on IO failure", () => {
  test("does not throw when runDir is unwritable (best-effort)", async () => {
    // Intentionally pick an invalid-ish directory name on most systems.
    // If it happens to be writable on your system, this test may be inconclusive.
    const runDir = path.join(process.cwd(), "tests", "fixtures", "telemetry_run_bad", "\u0000");

    const t = createTelemetryRun({ runDir, runId: "run_bad" });

    // Emit should not throw on IO; schema validation is still enforced
    expect(() => t.emit({ name: "x", level: "info", fields: {} })).not.toThrow();

    // Flush should not throw either
    await expect(t.flush()).resolves.toBeUndefined();
  });
});
