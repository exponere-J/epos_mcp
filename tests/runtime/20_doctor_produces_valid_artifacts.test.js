"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
const node_child_process_1 = require("node:child_process");
describe("Self-heal: doctor", () => {
    test("epos:doctor produces health_report artifacts under runs/<runId>/health", () => {
        (0, node_child_process_1.execSync)("npm run epos:doctor", { stdio: "pipe" });
        const runsDir = node_path_1.default.join(process.cwd(), "runs");
        expect(node_fs_1.default.existsSync(runsDir)).toBe(true);
        const entries = node_fs_1.default.readdirSync(runsDir).map((d) => node_path_1.default.join(runsDir, d));
        expect(entries.length).toBeGreaterThan(0);
        // newest by mtime (good enough for local runs)
        entries.sort((a, b) => node_fs_1.default.statSync(b).mtimeMs - node_fs_1.default.statSync(a).mtimeMs);
        const latest = entries[0];
        const healthDir = node_path_1.default.join(latest, "health");
        const reportJson = node_path_1.default.join(healthDir, "health_report.json");
        const reportMd = node_path_1.default.join(healthDir, "health_report.md");
        expect(node_fs_1.default.existsSync(reportJson)).toBe(true);
        expect(node_fs_1.default.existsSync(reportMd)).toBe(true);
        const parsed = JSON.parse(node_fs_1.default.readFileSync(reportJson, "utf-8"));
        expect(parsed.schema_id).toBe("core.health_report");
    });
});
//# sourceMappingURL=20_doctor_produces_valid_artifacts.test.js.map