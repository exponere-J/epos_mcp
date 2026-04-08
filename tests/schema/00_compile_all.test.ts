import { getRuntime } from "./ajv";

describe("Module 1: compile gate - all schemas", () => {
  test("compiles all *.schema.json with strict AJV and unique $id", () => {
    const rt = getRuntime();
    expect(rt.schemaIds.length).toBeGreaterThan(0);
    // core required by Module 2
    expect(rt.schemaIds).toContain("_defs");
    expect(rt.schemaIds).toContain("core.telemetry_envelope");
  });
});
