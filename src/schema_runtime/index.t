// src/schema_runtime/index.ts
import fs from "node:fs";
import path from "node:path";
import Ajv from "ajv";
import addFormats from "ajv-formats";

export class SchemaRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SchemaRuntimeError";
  }
}

export type SchemaRuntime = {
  ajv: Ajv;
  schemaIds: string[];
  validateOrThrow: (schemaId: string, data: unknown) => void;
};

let _runtime: SchemaRuntime | null = null;

function listSchemaFiles(root: string): string[] {
  const out: string[] = [];
  const walk = (dir: string) => {
    for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, ent.name);
      if (ent.isDirectory()) walk(p);
      else if (ent.isFile() && ent.name.endsWith(".schema.json")) out.push(p);
    }
  };
  walk(root);
  return out;
}

function schemaIdsFromAjv(ajv: Ajv): string[] {
  // Ajv stores schemas in ajv.schemas with keys like "id" or "schemaId"
  const ids = new Set<string>();
  const store: any = (ajv as any).schemas ?? {};
  for (const k of Object.keys(store)) {
    // keys often equal the $id; store[k].schema?.$id may also exist
    ids.add(k);
    const sid = store[k]?.schema?.$id;
    if (typeof sid === "string") ids.add(sid);
  }
  return Array.from(ids);
}

export function buildSchemaRuntime(): SchemaRuntime {
  if (_runtime) return _runtime;

  const schemasRoot = path.join(process.cwd(), "schemas");
  if (!fs.existsSync(schemasRoot)) {
    throw new SchemaRuntimeError(`schemas/ directory not found at: ${schemasRoot}`);
  }

  const ajv = new Ajv({
    allErrors: true,
    strict: true,
    allowUnionTypes: true
  });
  addFormats(ajv);

  const files = listSchemaFiles(schemasRoot);

  for (const file of files) {
    const raw = fs.readFileSync(file, "utf-8");
    const json = JSON.parse(raw);

    if (!json.$id || typeof json.$id !== "string") {
      throw new SchemaRuntimeError(`Schema missing $id: ${file}`);
    }

    // Important: addSchema(id) must use $id to satisfy tests that check IDs
    ajv.addSchema(json, json.$id);
  }

  const runtime: SchemaRuntime = {
    ajv,
    schemaIds: schemaIdsFromAjv(ajv),
    validateOrThrow: (schemaId: string, data: unknown) => {
      const v: any = ajv.getSchema(schemaId);
      if (!v) throw new SchemaRuntimeError(`Unknown schemaId: ${schemaId}`);
      const ok = v(data);
      if (!ok) {
        const details = (v.errors ?? [])
          .map((e: any) => `${e.instancePath || "<root>"} ${e.message ?? ""}`.trim())
          .join("; ");
        throw new SchemaRuntimeError(`Schema validation failed for '${schemaId}': ${details}`);
      }
    }
  };

  _runtime = runtime;
  return runtime;
}

export function validateOrThrow(schemaId: string, data: unknown): void {
  buildSchemaRuntime().validateOrThrow(schemaId, data);
}
