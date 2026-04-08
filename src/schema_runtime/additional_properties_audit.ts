import fs from "fs";
import path from "path";
import { listSchemaFiles } from "./loader";

type Violation = { schemaPath: string; jsonPointer: string; message: string };

function isObjectSchema(node: any): boolean {
  if (!node || typeof node !== "object") return false;
  if (node.type === "object") return true;
  // some schemas omit explicit type but have properties; treat as object-ish for audit
  if (node.properties && typeof node.properties === "object") return true;
  return false;
}

function walk(node: any, schemaPath: string, jsonPointer: string, out: Violation[]) {
  if (!node || typeof node !== "object") return;

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
    const v = (node as any)[k];
    if (v && typeof v === "object") {
      if (Array.isArray(v)) {
        v.forEach((item, idx) => walk(item, schemaPath, `${jsonPointer}/${k}/${idx}`, out));
      } else {
        walk(v, schemaPath, `${jsonPointer}/${k}`, out);
      }
    }
  }
}

export function auditAdditionalProperties(): Violation[] {
  const schemaRoot = path.join(process.cwd(), "schemas");
  const files = listSchemaFiles(schemaRoot);

  const violations: Violation[] = [];
  for (const abs of files) {
    const base = path.basename(abs);
    if (base === "_defs.schema.json") continue; // defs can contain $defs objects without AP false in each node; we keep it permissive
    const rel = path.relative(process.cwd(), abs);
    const json = JSON.parse(fs.readFileSync(abs, "utf-8"));
    walk(json, rel, "", violations);
  }
  return violations;
}
