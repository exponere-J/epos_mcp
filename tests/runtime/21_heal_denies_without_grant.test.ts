import fs from "node:fs";
import { execSync } from "node:child_process";

describe("Self-heal: heal", () => {
  test("epos:heal refuses without grants.local.json change_dependencies", () => {
    if (fs.existsSync("grants.local.json")) fs.unlinkSync("grants.local.json");

    let code = 0;
    try {
      execSync("npm run epos:heal", { stdio: "pipe" });
    } catch (e: any) {
      code = e?.status ?? 1;
    }

    expect(code).toBe(2);
  });
});
