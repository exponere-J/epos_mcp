"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const ajv_1 = __importDefault(require("ajv"));
const ajv_formats_1 = __importDefault(require("ajv-formats"));
describe("Module 1: runtime hardening - unresolved $ref throws", () => {
    test("ajv.addSchema throws for bogus $ref under strictSchema", () => {
        const ajv = new ajv_1.default({ strict: true, strictSchema: true, allErrors: true, loadSchema: undefined });
        (0, ajv_formats_1.default)(ajv);
        const schema = {
            $id: "test.bogus_ref",
            $schema: "https://json-schema.org/draft/2020-12/schema",
            type: "object",
            additionalProperties: false,
            properties: {
                x: { $ref: "does.not.exist#/$defs/nope" }
            }
        };
        expect(() => ajv.addSchema(schema)).toThrow();
    });
});
//# sourceMappingURL=01_unresolved_ref_throws.test.js.map