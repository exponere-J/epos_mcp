"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const node_child_process_1 = require("node:child_process");
const node_fs_1 = __importDefault(require("node:fs"));
const node_path_1 = __importDefault(require("node:path"));
function run(cmd, args) {
    const r = (0, node_child_process_1.spawnSync)(cmd, args, { stdio: "inherit", shell: true });
    return { code: typeof r.status === "number" ? r.status : 1 };
}
function runCapture(cmd) {
    const r = (0, node_child_process_1.spawnSync)(cmd, { stdio: ["ignore", "pipe", "pipe"], shell: true, encoding: "utf-8" });
    const stdout = (r.stdout ?? "").toString();
    const stderr = (r.stderr ?? "").toString();
    const code = typeof r.status === "number" ? r.status : 1;
    return { code, stdout, stderr, combined: `${stdout}\n${stderr}` };
}
function shouldDoctorFromText(text) {
    const needles = ["deprecated", "unsupported", "EBADENGINE", "npm WARN", "ERR!"];
    const t = text.toLowerCase();
    return needles.some((n) => t.includes(n.toLowerCase()));
}
function hasGrant() {
    const p = node_path_1.default.join(process.cwd(), "grants.local.json");
    if (!node_fs_1.default.existsSync(p))
        return false;
    try {
        const j = JSON.parse(node_fs_1.default.readFileSync(p, "utf-8"));
        return j?.change_dependencies === true;
    }
    catch {
        return false;
    }
}
function main() {
    const mode = process.argv[2];
    if (!mode || !["install", "update", "test"].includes(mode)) {
        // eslint-disable-next-line no-console
        console.error("Usage: node dist/cli/safe.js <install|update|test>");
        process.exit(2);
    }
    if (mode === "install") {
        const r = runCapture("npm install");
        if (r.code !== 0 || shouldDoctorFromText(r.combined)) {
            run("npm", ["run", "epos:doctor"]);
        }
        process.exit(r.code);
    }
    if (mode === "update") {
        const r = runCapture("npm update");
        // Always doctor after update (deterministic signal snapshot)
        run("npm", ["run", "epos:doctor"]);
        process.exit(r.code);
    }
    // mode === "test"
    const t = runCapture("npm test");
    if (t.code !== 0) {
        run("npm", ["run", "epos:doctor"]);
        // Optional: do NOT auto-heal here. Healing remains explicit.
        // If you want auto-heal only when granted, flip EPOS_AUTO_HEAL=1
        const autoHeal = process.env.EPOS_AUTO_HEAL === "1";
        if (autoHeal && hasGrant()) {
            run("npm", ["run", "epos:heal"]);
        }
    }
    process.exit(t.code);
}
main();
//# sourceMappingURL=safe.js.map