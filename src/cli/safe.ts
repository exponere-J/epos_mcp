import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

function run(cmd: string, args: string[]) {
  const r = spawnSync(cmd, args, { stdio: "inherit", shell: true });
  return { code: typeof r.status === "number" ? r.status : 1 };
}

function runCapture(cmd: string) {
  const r = spawnSync(cmd, { stdio: ["ignore", "pipe", "pipe"], shell: true, encoding: "utf-8" as any });
  const stdout = (r.stdout ?? "").toString();
  const stderr = (r.stderr ?? "").toString();
  const code = typeof r.status === "number" ? r.status : 1;
  return { code, stdout, stderr, combined: `${stdout}\n${stderr}` };
}

function shouldDoctorFromText(text: string): boolean {
  const needles = ["deprecated", "unsupported", "EBADENGINE", "npm WARN", "ERR!"];
  const t = text.toLowerCase();
  return needles.some((n) => t.includes(n.toLowerCase()));
}

function hasGrant(): boolean {
  const p = path.join(process.cwd(), "grants.local.json");
  if (!fs.existsSync(p)) return false;
  try {
    const j = JSON.parse(fs.readFileSync(p, "utf-8"));
    return j?.change_dependencies === true;
  } catch {
    return false;
  }
}

function main() {
  const mode = process.argv[2];
  if (!mode || !["install", "update", "test"].includes(mode)) {
    // eslint-disable-next-line no-console
    console.error("Usage: node dist/cli/safe.js <install|update|test>");
    process.exit(2);
  }

  if (mode === "install") {
    const r = runCapture("npm install");
    if (r.code !== 0 || shouldDoctorFromText(r.combined)) {
      run("npm", ["run", "epos:doctor"]);
    }
    process.exit(r.code);
  }

  if (mode === "update") {
    const r = runCapture("npm update");
    // Always doctor after update (deterministic signal snapshot)
    run("npm", ["run", "epos:doctor"]);
    process.exit(r.code);
  }

  // mode === "test"
  const t = runCapture("npm test");
  if (t.code !== 0) {
    run("npm", ["run", "epos:doctor"]);
    // Optional: do NOT auto-heal here. Healing remains explicit.
    // If you want auto-heal only when granted, flip EPOS_AUTO_HEAL=1
    const autoHeal = process.env.EPOS_AUTO_HEAL === "1";
    if (autoHeal && hasGrant()) {
      run("npm", ["run", "epos:heal"]);
    }
  }
  process.exit(t.code);
}

main();
