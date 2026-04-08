import Ajv from "ajv";
import addFormats from "ajv-formats";

describe("Module 1: runtime hardening - unresolved $ref throws", () => {
  test("ajv.addSchema throws for bogus $ref under strictSchema", () => {
    const ajv = new Ajv({ strict: true, strictSchema: true, allErrors: true, loadSchema: undefined });
    addFormats(ajv);

    const schema = {
      $id: "test.bogus_ref",
      $schema: "https://json-schema.org/draft/2020-12/schema",
      type: "object",
      additionalProperties: false,
      properties: {
        x: { $ref: "does.not.exist#/$defs/nope" }
      }
    };

    expect(() => ajv.addSchema(schema as any)).toThrow();
  });
});
