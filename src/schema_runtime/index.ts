import type Ajv from "ajv";
import { createAjvStrict } from "./ajv_factory";
import { loadSchemaFiles } from "./loader";
import { SchemaRuntimeError } from "./errors";

export { SchemaRuntimeError } from "./errors";

export type ValidateResult =
  | { ok: true; errors: null }
  | { ok: false; errors: Array<{ path: string; message: string }> };

export type SchemaRuntime = {
  ajv: Ajv;
  schemaIds: string[];
  validate: (schemaId: string, data: unknown) => ValidateResult;
  validateOrThrow: (schemaId: string, data: unknown) => void;
};

let _runtime: SchemaRuntime | null = null;

function mapAjvErrors(errors: any[] | null | undefined): Array<{ path: string; message: string }> {
  if (!errors || errors.length === 0) return [{ path: "", message: "validation error" }];
  return errors.map((e) => ({
    path: e.instancePath || e.schemaPath || "",
    message: e.message || "validation error"
  }));
}

function aliasKeysFor(id: string): string[] {
  // Deterministic aliasing: only where the test contract expects short keys.
  // Extend later if you add more “short key” expectations.
  if (id === "core.telemetry_envelope") return ["telemetry_envelope"];
  return [];
}

export function buildSchemaRuntime(): SchemaRuntime {
  const ajv = createAjvStrict();
  const loaded = loadSchemaFiles();

  // Gate: must have $id, must be unique
  const ids = new Map<string, string>(); // id -> relPath
  for (const f of loaded) {
    const id = f.json?.$id;
    if (typeof id !== "string" || id.trim().length === 0) {
      throw new SchemaRuntimeError("SCHEMA_INVALID", `Schema missing $id: ${f.relPath}`, { relPath: f.relPath });
    }
    if (ids.has(id)) {
      throw new SchemaRuntimeError(
        "SCHEMA_INVALID",
        `Duplicate $id "${id}" in ${f.relPath} (already in ${ids.get(id)})`,
        { id, relPath: f.relPath, firstSeen: ids.get(id) }
      );
    }
    ids.set(id, f.relPath);
  }

  // Add schemas deterministically
  try {
    for (const f of loaded) {
      const id = f.json.$id as string;
      ajv.addSchema(f.json, id);
      for (const a of aliasKeysFor(id)) {
        ajv.addSchema(f.json, a);
      }
    }
  } catch (err: any) {
    throw new SchemaRuntimeError("SCHEMA_INVALID", `Schema compile failed: ${err?.message ?? String(err)}`, {
      cause: String(err?.message ?? err)
    });
  }

  const schemaIds = Array.from(ids.keys());

  const validate = (schemaId: string, data: unknown): ValidateResult => {
    const fn = ajv.getSchema(schemaId);
    if (!fn) return { ok: false, errors: [{ path: "", message: `schema not found: ${schemaId}` }] };
    const ok = fn(data) as boolean;
    if (ok) return { ok: true, errors: null };
    return { ok: false, errors: mapAjvErrors(fn.errors) };
  };

  const validateOrThrow = (schemaId: string, data: unknown): void => {
    const fn = ajv.getSchema(schemaId);
    if (!fn) throw new SchemaRuntimeError("SCHEMA_NOT_FOUND", `schema not found: ${schemaId}`, { schemaId });
    const ok = fn(data) as boolean;
    if (ok) return;
    throw new SchemaRuntimeError("DATA_INVALID", `data invalid for schema: ${schemaId}`, {
      schemaId,
      errors: mapAjvErrors(fn.errors)
    });
  };

  return { ajv, schemaIds, validate, validateOrThrow };
}

export function getSchemaRuntime(): SchemaRuntime {
  if (_runtime) return _runtime;
  _runtime = buildSchemaRuntime();
  return _runtime;
}

export function validateOrThrow(schemaId: string, data: unknown): void {
  return getSchemaRuntime().validateOrThrow(schemaId, data);
}

