"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const schema_runtime_1 = require("../../src/schema_runtime");
const error_codes_1 = require("../../src/schema_runtime/error_codes");
describe("Module 1: gate - missing $id fails loud", () => {
    test("missing $id yields SCHEMA_INVALID", () => {
        const tmpDir = path_1.default.join(process.cwd(), "tests", "fixtures", "schema_tmp");
        fs_1.default.mkdirSync(tmpDir, { recursive: true });
        const file = path_1.default.join(tmpDir, "bad.schema.json");
        fs_1.default.writeFileSync(file, JSON.stringify({
            $schema: "https://json-schema.org/draft/2020-12/schema",
            type: "object",
            additionalProperties: false
        }, null, 2));
        // Temporarily simulate by copying into schemas/ and restoring
        const schemasDir = path_1.default.join(process.cwd(), "schemas");
        const target = path_1.default.join(schemasDir, "bad.schema.json");
        const hadExisting = fs_1.default.existsSync(target);
        const existing = hadExisting ? fs_1.default.readFileSync(target, "utf-8") : null;
        try {
            fs_1.default.copyFileSync(file, target);
            expect(() => (0, schema_runtime_1.buildSchemaRuntime)()).toThrow(error_codes_1.SchemaRuntimeError);
            try {
                (0, schema_runtime_1.buildSchemaRuntime)();
            }
            catch (e) {
                expect(e.code).toBe("SCHEMA_INVALID");
            }
        }
        finally {
            if (hadExisting && existing != null)
                fs_1.default.writeFileSync(target, existing);
            else if (fs_1.default.existsSync(target))
                fs_1.default.unlinkSync(target);
        }
    });
});
//# sourceMappingURL=10_missing_id_is_invalid.test.js.map