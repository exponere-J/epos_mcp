"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const path_1 = __importDefault(require("path"));
const telemetry_client_1 = require("../../src/telemetry_client");
describe("Module 2: mkdirp and continue on IO failure", () => {
    test("does not throw when runDir is unwritable (best-effort)", async () => {
        // Intentionally pick an invalid-ish directory name on most systems.
        // If it happens to be writable on your system, this test may be inconclusive.
        const runDir = path_1.default.join(process.cwd(), "tests", "fixtures", "telemetry_run_bad", "\u0000");
        const t = (0, telemetry_client_1.createTelemetryRun)({ runDir, runId: "run_bad" });
        // Emit should not throw on IO; schema validation is still enforced
        expect(() => t.emit({ name: "x", level: "info", fields: {} })).not.toThrow();
        // Flush should not throw either
        await expect(t.flush()).resolves.toBeUndefined();
    });
});
//# sourceMappingURL=20_mkdirp_and_continue_on_write_fail.test.js.map