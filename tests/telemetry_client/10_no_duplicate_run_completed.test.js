"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const telemetry_client_1 = require("../../src/telemetry_client");
describe("Module 2: no duplicate system.run_completed", () => {
    test("flush emits system.run_completed once even if user emits it", async () => {
        const runDir = path_1.default.join(process.cwd(), "tests", "fixtures", "telemetry_run_2");
        fs_1.default.rmSync(runDir, { recursive: true, force: true });
        const t = (0, telemetry_client_1.createTelemetryRun)({ runDir, runId: "run_test_2" });
        // user emits completion early
        t.emit({ name: "system.run_completed", level: "info", fields: { note: "manual" } });
        // flush should not emit another completion
        await t.flush();
        const lines = fs_1.default.readFileSync(path_1.default.join(runDir, "telemetry.json"), "utf-8").trim().split("\n").filter(Boolean);
        const completions = lines.map((l) => JSON.parse(l)).filter((e) => e.event?.name === "system.run_completed");
        expect(completions).toHaveLength(1);
    });
});
//# sourceMappingURL=10_no_duplicate_run_completed.test.js.map