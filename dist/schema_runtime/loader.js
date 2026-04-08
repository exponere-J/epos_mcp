"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.listSchemaFiles = listSchemaFiles;
exports.loadSchemaFiles = loadSchemaFiles;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
function isSchemaFile(filename) {
    return filename.endsWith(".schema.json");
}
function listSchemaFiles(rootDir) {
    // recursive crawl; allow only *.schema.json, but include _defs.schema.json explicitly if present.
    const out = [];
    const walk = (dir) => {
        const entries = fs_1.default.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name));
        for (const ent of entries) {
            const abs = path_1.default.join(dir, ent.name);
            if (ent.isDirectory())
                walk(abs);
            else if (ent.isFile() && isSchemaFile(ent.name))
                out.push(abs);
        }
    };
    walk(rootDir);
    // enforce allowlist + deterministic ordering: _defs first, then the rest
    const defs = out.filter((p) => path_1.default.basename(p) === "_defs.schema.json");
    const rest = out.filter((p) => path_1.default.basename(p) !== "_defs.schema.json");
    return [...defs, ...rest].sort((a, b) => {
        // keep _defs first even after sort
        const aIsDefs = path_1.default.basename(a) === "_defs.schema.json";
        const bIsDefs = path_1.default.basename(b) === "_defs.schema.json";
        if (aIsDefs && !bIsDefs)
            return -1;
        if (!aIsDefs && bIsDefs)
            return 1;
        return a.localeCompare(b);
    });
}
function loadSchemaFiles() {
    const schemaRoot = path_1.default.join(process.cwd(), "schemas");
    const files = listSchemaFiles(schemaRoot);
    return files.map((absPath) => {
        const relPath = path_1.default.relative(process.cwd(), absPath);
        const raw = fs_1.default.readFileSync(absPath, "utf-8");
        const json = JSON.parse(raw);
        return { absPath, relPath, json };
    });
}
//# sourceMappingURL=loader.js.map