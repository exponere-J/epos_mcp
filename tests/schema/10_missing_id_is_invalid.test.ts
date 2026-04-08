import fs from "fs";
import path from "path";
import { buildSchemaRuntime } from "../../src/schema_runtime";
import { SchemaRuntimeError } from "../../src/schema_runtime/error_codes";

describe("Module 1: gate - missing $id fails loud", () => {
  test("missing $id yields SCHEMA_INVALID", () => {
    const tmpDir = path.join(process.cwd(), "tests", "fixtures", "schema_tmp");
    fs.mkdirSync(tmpDir, { recursive: true });

    const file = path.join(tmpDir, "bad.schema.json");
    fs.writeFileSync(
      file,
      JSON.stringify(
        {
          $schema: "https://json-schema.org/draft/2020-12/schema",
          type: "object",
          additionalProperties: false
        },
        null,
        2
      )
    );

    // Temporarily simulate by copying into schemas/ and restoring
    const schemasDir = path.join(process.cwd(), "schemas");
    const target = path.join(schemasDir, "bad.schema.json");

    const hadExisting = fs.existsSync(target);
    const existing = hadExisting ? fs.readFileSync(target, "utf-8") : null;

    try {
      fs.copyFileSync(file, target);
      expect(() => buildSchemaRuntime()).toThrow(SchemaRuntimeError);
      try {
        buildSchemaRuntime();
      } catch (e: any) {
        expect(e.code).toBe("SCHEMA_INVALID");
      }
    } finally {
      if (hadExisting && existing != null) fs.writeFileSync(target, existing);
      else if (fs.existsSync(target)) fs.unlinkSync(target);
    }
  });
});
