import crypto from "node:crypto";

export type PlatformName = "gumroad";
export type DeployMode = "dry_run" | "live";
export type DeployAction = "create" | "update" | "publish" | "unpublish";

export type ListingCanonical = {
  schema_id: "core.listing_canonical";
  product_id: string;
  run_id: string;
  version: string;
  title: string;
  short_description: string;
  long_description: string;
  tags: string[];
  category: string;
  audience: string;
  price: { currency: string; amount: number; pricing_model: "one_time" | "subscription" | "pay_what_you_want" };
  license: { name: string; terms_url: string };
  assets: { cover_image: string; gallery_images: string[]; downloadables: string[] };
  support: { contact: string; update_policy: string };
  brand_voice: { tone_rules: string[]; banned_phrases: string[] };
  proof: { what_problem: string; why_it_works: string; who_its_for: string; who_its_not_for: string };
};

export type PlatformDeployRequest = {
  schema_id: "core.platform_deploy_request";
  run_id: string;
  product_id: string;
  platform: PlatformName;
  mode: DeployMode;
  action: DeployAction;
  target?: { listing_id?: string; storefront?: string };
  artifacts: { product_pack_ref: string; listing_canonical_ref: string };
  grants_required: string[];
};

export type ConnectorViolation = {
  code: string;
  message: string;
};

export type ValidatePackResult = {
  ok: boolean;
  violations: ConnectorViolation[];
};

export type PreparedListing = {
  platform: PlatformName;
  payload: Record<string, unknown>;
  warnings: string[];
};

export type Connector = {
  platform: PlatformName;

  validatePack: (args: {
    req: PlatformDeployRequest;
    listing: ListingCanonical;
    packAbsPath: string;
    rootDir: string;
  }) => ValidatePackResult;

  prepareListing: (args: {
    req: PlatformDeployRequest;
    listing: ListingCanonical;
    packAbsPath: string;
    rootDir: string;
  }) => PreparedListing;

  /**
   * Phase A: dry-run only. If you later add live deploy:
   * - must be permission-gated upstream
   * - must emit receipts
   */
  supportsLive: boolean;
};

export function fingerprint(obj: unknown): string {
  const raw = JSON.stringify(obj);
  return crypto.createHash("sha256").update(raw, "utf-8").digest("hex").slice(0, 16);
}
