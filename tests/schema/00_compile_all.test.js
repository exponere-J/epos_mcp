"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ajv_1 = require("./ajv");
describe("Module 1: compile gate - all schemas", () => {
    test("compiles all *.schema.json with strict AJV and unique $id", () => {
        const rt = (0, ajv_1.getRuntime)();
        expect(rt.schemaIds.length).toBeGreaterThan(0);
        // core required by Module 2
        expect(rt.schemaIds).toContain("_defs");
        expect(rt.schemaIds).toContain("core.telemetry_envelope");
    });
});
//# sourceMappingURL=00_compile_all.test.js.map