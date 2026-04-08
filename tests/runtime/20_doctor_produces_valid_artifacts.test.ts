import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";

describe("Self-heal: doctor", () => {
  test("epos:doctor produces health_report artifacts under runs/<runId>/health", () => {
    execSync("npm run epos:doctor", { stdio: "pipe" });

    const runsDir = path.join(process.cwd(), "runs");
    expect(fs.existsSync(runsDir)).toBe(true);

    const entries = fs.readdirSync(runsDir).map((d) => path.join(runsDir, d));
    expect(entries.length).toBeGreaterThan(0);

    // newest by mtime (good enough for local runs)
    entries.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
    const latest = entries[0];

    const healthDir = path.join(latest, "health");
    const reportJson = path.join(healthDir, "health_report.json");
    const reportMd = path.join(healthDir, "health_report.md");

    expect(fs.existsSync(reportJson)).toBe(true);
    expect(fs.existsSync(reportMd)).toBe(true);

    const parsed = JSON.parse(fs.readFileSync(reportJson, "utf-8"));
    expect(parsed.schema_id).toBe("core.health_report");
  });
});
