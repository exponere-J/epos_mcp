"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const additional_properties_audit_1 = require("../../src/schema_runtime/additional_properties_audit");
describe("Module 1: audit gate - additionalProperties:false", () => {
    test("all object schemas must set additionalProperties:false", () => {
        const violations = (0, additional_properties_audit_1.auditAdditionalProperties)();
        if (violations.length > 0) {
            const msg = violations
                .slice(0, 25)
                .map((v) => `${v.schemaPath} @ ${v.jsonPointer}: ${v.message}`)
                .join("\n");
            throw new Error(`additionalProperties audit failed (${violations.length}):\n${msg}`);
        }
        expect(violations).toHaveLength(0);
    });
});
//# sourceMappingURL=99_additional_properties_audit.test.js.map