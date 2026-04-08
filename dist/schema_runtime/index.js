"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SchemaRuntimeError = void 0;
exports.buildSchemaRuntime = buildSchemaRuntime;
exports.getSchemaRuntime = getSchemaRuntime;
exports.validateOrThrow = validateOrThrow;
const ajv_factory_1 = require("./ajv_factory");
const loader_1 = require("./loader");
const errors_1 = require("./errors");
var errors_2 = require("./errors");
Object.defineProperty(exports, "SchemaRuntimeError", { enumerable: true, get: function () { return errors_2.SchemaRuntimeError; } });
let _runtime = null;
function mapAjvErrors(errors) {
    if (!errors || errors.length === 0)
        return [{ path: "", message: "validation error" }];
    return errors.map((e) => ({
        path: e.instancePath || e.schemaPath || "",
        message: e.message || "validation error"
    }));
}
function aliasKeysFor(id) {
    // Deterministic aliasing: only where the test contract expects short keys.
    // Extend later if you add more “short key” expectations.
    if (id === "core.telemetry_envelope")
        return ["telemetry_envelope"];
    return [];
}
function buildSchemaRuntime() {
    const ajv = (0, ajv_factory_1.createAjvStrict)();
    const loaded = (0, loader_1.loadSchemaFiles)();
    // Gate: must have $id, must be unique
    const ids = new Map(); // id -> relPath
    for (const f of loaded) {
        const id = f.json?.$id;
        if (typeof id !== "string" || id.trim().length === 0) {
            throw new errors_1.SchemaRuntimeError("SCHEMA_INVALID", `Schema missing $id: ${f.relPath}`, { relPath: f.relPath });
        }
        if (ids.has(id)) {
            throw new errors_1.SchemaRuntimeError("SCHEMA_INVALID", `Duplicate $id "${id}" in ${f.relPath} (already in ${ids.get(id)})`, { id, relPath: f.relPath, firstSeen: ids.get(id) });
        }
        ids.set(id, f.relPath);
    }
    // Add schemas deterministically
    try {
        for (const f of loaded) {
            const id = f.json.$id;
            ajv.addSchema(f.json, id);
            for (const a of aliasKeysFor(id)) {
                ajv.addSchema(f.json, a);
            }
        }
    }
    catch (err) {
        throw new errors_1.SchemaRuntimeError("SCHEMA_INVALID", `Schema compile failed: ${err?.message ?? String(err)}`, {
            cause: String(err?.message ?? err)
        });
    }
    const schemaIds = Array.from(ids.keys());
    const validate = (schemaId, data) => {
        const fn = ajv.getSchema(schemaId);
        if (!fn)
            return { ok: false, errors: [{ path: "", message: `schema not found: ${schemaId}` }] };
        const ok = fn(data);
        if (ok)
            return { ok: true, errors: null };
        return { ok: false, errors: mapAjvErrors(fn.errors) };
    };
    const validateOrThrow = (schemaId, data) => {
        const fn = ajv.getSchema(schemaId);
        if (!fn)
            throw new errors_1.SchemaRuntimeError("SCHEMA_NOT_FOUND", `schema not found: ${schemaId}`, { schemaId });
        const ok = fn(data);
        if (ok)
            return;
        throw new errors_1.SchemaRuntimeError("DATA_INVALID", `data invalid for schema: ${schemaId}`, {
            schemaId,
            errors: mapAjvErrors(fn.errors)
        });
    };
    return { ajv, schemaIds, validate, validateOrThrow };
}
function getSchemaRuntime() {
    if (_runtime)
        return _runtime;
    _runtime = buildSchemaRuntime();
    return _runtime;
}
function validateOrThrow(schemaId, data) {
    return getSchemaRuntime().validateOrThrow(schemaId, data);
}
//# sourceMappingURL=index.js.map