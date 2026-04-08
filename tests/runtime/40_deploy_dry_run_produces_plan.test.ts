import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { execSync } from "node:child_process";

function newestDirUnder(p: string): string | null {
  if (!fs.existsSync(p)) return null;
  const entries = fs
    .readdirSync(p)
    .map((d) => path.join(p, d))
    .filter((d) => fs.statSync(d).isDirectory());
  if (!entries.length) return null;
  entries.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  return entries[0];
}

describe("Shelf placement: deploy (dry-run)", () => {
  test("deploy writes deployment_plan.json under runs/<runId>/deploy/gumroad", () => {
    // Build once (deterministic for this test suite)
    execSync("npm run build", { stdio: "pipe" });

    // Create a temp “product pack”
    const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "epos_deploy_"));
    const packDir = path.join(tmpRoot, "pack");
    fs.mkdirSync(packDir, { recursive: true });

    // Minimal assets expected by connector
    const cover = path.join(packDir, "cover.png");
    const dl = path.join(packDir, "product_pack.zip");
    fs.writeFileSync(cover, "fakepng", "utf-8");
    fs.writeFileSync(dl, "fakezip", "utf-8");

    // Canonical listing file
    const listingPath = path.join(tmpRoot, "listing_canonical.json");
    const listing = {
      schema_id: "core.listing_canonical",
      product_id: "P_TEST",
      run_id: "RUN_TEST_DEPLOY",
      version: "0.0.1",
      title: "Test Product",
      short_description: "Short desc.",
      long_description: "Long desc.",
      tags: ["epos", "test"],
      category: "templates",
      audience: "operators",
      price: { currency: "USD", amount: 10, pricing_model: "one_time" },
      license: { name: "Personal", terms_url: "https://example.com/terms" },
      assets: {
        cover_image: "cover.png",
        gallery_images: [],
        downloadables: ["product_pack.zip"]
      },
      support: { contact: "support@example.com", update_policy: "best-effort" },
      brand_voice: { tone_rules: ["direct"], banned_phrases: [] },
      proof: {
        what_problem: "Problem",
        why_it_works: "Because",
        who_its_for: "People",
        who_its_not_for: "Not people"
      }
    };
    fs.writeFileSync(listingPath, JSON.stringify(listing, null, 2), "utf-8");

    // Deploy request file
    const reqPath = path.join(tmpRoot, "deploy_request.json");
    const req = {
      schema_id: "core.platform_deploy_request",
      run_id: "RUN_TEST_DEPLOY",
      product_id: "P_TEST",
      platform: "gumroad",
      mode: "dry_run",
      action: "create",
      artifacts: {
        product_pack_ref: packDir,
        listing_canonical_ref: listingPath
      },
      grants_required: ["publish_products", "upload_assets"]
    };
    fs.writeFileSync(reqPath, JSON.stringify(req, null, 2), "utf-8");

    // Execute deploy CLI
    execSync(`node dist/cli/deploy.js --request "${reqPath}"`, { stdio: "pipe" });

    const runsDir = path.join(process.cwd(), "runs");
    const runDir = path.join(runsDir, "RUN_TEST_DEPLOY");
    expect(fs.existsSync(runDir)).toBe(true);

    const outDir = path.join(runDir, "deploy", "gumroad");
    const planPath = path.join(outDir, "deployment_plan.json");
    expect(fs.existsSync(planPath)).toBe(true);

    const parsed = JSON.parse(fs.readFileSync(planPath, "utf-8"));
    expect(parsed.schema_id).toBe("core.platform_deployment");
    expect(parsed.platform).toBe("gumroad");
    expect(parsed.mode).toBe("dry_run");
    expect(parsed.status).toBe("planned");
  });
});
