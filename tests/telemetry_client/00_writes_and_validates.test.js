"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const telemetry_client_1 = require("../../src/telemetry_client");
describe("Module 2: telemetry_client local sink", () => {
    test("writes validated envelopes to telemetry.json (NDJSON)", async () => {
        const runDir = path_1.default.join(process.cwd(), "tests", "fixtures", "telemetry_run_1");
        fs_1.default.rmSync(runDir, { recursive: true, force: true });
        const t = (0, telemetry_client_1.createTelemetryRun)({ runDir, runId: "run_test_1" });
        t.emit({ name: "mission.received", level: "info", fields: { mission_id: "m1" } });
        await t.flush();
        const filePath = path_1.default.join(runDir, "telemetry.json");
        expect(fs_1.default.existsSync(filePath)).toBe(true);
        const lines = fs_1.default.readFileSync(filePath, "utf-8").trim().split("\n").filter(Boolean);
        expect(lines.length).toBeGreaterThanOrEqual(2);
        const env0 = JSON.parse(lines[0]);
        expect(env0.schema_id).toBe("core.telemetry_envelope");
        expect(env0.run_id).toBe("run_test_1");
        expect(env0.event.name).toBe("mission.received");
    });
});
//# sourceMappingURL=00_writes_and_validates.test.js.map