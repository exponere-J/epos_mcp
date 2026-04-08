import fs from "fs";
import path from "path";

export type LoadedSchemaFile = {
  absPath: string;
  relPath: string;
  json: any;
};

function isSchemaFile(filename: string): boolean {
  return filename.endsWith(".schema.json");
}

export function listSchemaFiles(rootDir: string): string[] {
  // recursive crawl; allow only *.schema.json, but include _defs.schema.json explicitly if present.
  const out: string[] = [];

  const walk = (dir: string) => {
    const entries = fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name));
    for (const ent of entries) {
      const abs = path.join(dir, ent.name);
      if (ent.isDirectory()) walk(abs);
      else if (ent.isFile() && isSchemaFile(ent.name)) out.push(abs);
    }
  };

  walk(rootDir);

  // enforce allowlist + deterministic ordering: _defs first, then the rest
  const defs = out.filter((p) => path.basename(p) === "_defs.schema.json");
  const rest = out.filter((p) => path.basename(p) !== "_defs.schema.json");

  return [...defs, ...rest].sort((a, b) => {
    // keep _defs first even after sort
    const aIsDefs = path.basename(a) === "_defs.schema.json";
    const bIsDefs = path.basename(b) === "_defs.schema.json";
    if (aIsDefs && !bIsDefs) return -1;
    if (!aIsDefs && bIsDefs) return 1;
    return a.localeCompare(b);
  });
}

export function loadSchemaFiles(): LoadedSchemaFile[] {
  const schemaRoot = path.join(process.cwd(), "schemas");
  const files = listSchemaFiles(schemaRoot);

  return files.map((absPath) => {
    const relPath = path.relative(process.cwd(), absPath);
    const raw = fs.readFileSync(absPath, "utf-8");
    const json = JSON.parse(raw);
    return { absPath, relPath, json };
  });
}
