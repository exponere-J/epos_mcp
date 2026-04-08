"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_fs_1 = __importDefault(require("node:fs"));
const node_child_process_1 = require("node:child_process");
describe("Self-heal: heal", () => {
    test("epos:heal refuses without grants.local.json change_dependencies", () => {
        if (node_fs_1.default.existsSync("grants.local.json"))
            node_fs_1.default.unlinkSync("grants.local.json");
        let code = 0;
        try {
            (0, node_child_process_1.execSync)("npm run epos:heal", { stdio: "pipe" });
        }
        catch (e) {
            code = e?.status ?? 1;
        }
        expect(code).toBe(2);
    });
});
//# sourceMappingURL=21_heal_denies_without_grant.test.js.map