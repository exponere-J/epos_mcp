"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.auditAdditionalProperties = auditAdditionalProperties;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const loader_1 = require("./loader");
function isObjectSchema(node) {
    if (!node || typeof node !== "object")
        return false;
    if (node.type === "object")
        return true;
    // some schemas omit explicit type but have properties; treat as object-ish for audit
    if (node.properties && typeof node.properties === "object")
        return true;
    return false;
}
function walk(node, schemaPath, jsonPointer, out) {
    if (!node || typeof node !== "object")
        return;
    // Audit rule: any object schema must have additionalProperties:false
    if (isObjectSchema(node)) {
        if (node.additionalProperties !== false) {
            out.push({
                schemaPath,
                jsonPointer,
                message: "object schema missing additionalProperties:false"
            });
        }
    }
    // Traverse children
    const keys = Object.keys(node);
    for (const k of keys) {
        const v = node[k];
        if (v && typeof v === "object") {
            if (Array.isArray(v)) {
                v.forEach((item, idx) => walk(item, schemaPath, `${jsonPointer}/${k}/${idx}`, out));
            }
            else {
                walk(v, schemaPath, `${jsonPointer}/${k}`, out);
            }
        }
    }
}
function auditAdditionalProperties() {
    const schemaRoot = path_1.default.join(process.cwd(), "schemas");
    const files = (0, loader_1.listSchemaFiles)(schemaRoot);
    const violations = [];
    for (const abs of files) {
        const base = path_1.default.basename(abs);
        if (base === "_defs.schema.json")
            continue; // defs can contain $defs objects without AP false in each node; we keep it permissive
        const rel = path_1.default.relative(process.cwd(), abs);
        const json = JSON.parse(fs_1.default.readFileSync(abs, "utf-8"));
        walk(json, rel, "", violations);
    }
    return violations;
}
//# sourceMappingURL=additional_properties_audit.js.map