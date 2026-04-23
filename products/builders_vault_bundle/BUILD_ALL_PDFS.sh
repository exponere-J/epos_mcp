#!/usr/bin/env bash
# Build every PDF across all 6 products in the bundle.
set -euo pipefail

ROOT="$(dirname "$(realpath "$0")")/.."
OUT_DIR="${OUT_DIR:-./dist}"
mkdir -p "$OUT_DIR"

for product in ccp_prompt_pack premortem_kit brand_dna_kit journey_map voice_pack signal_framework; do
  echo "=== Building $product ==="
  pushd "$ROOT/$product" >/dev/null
  OUT_DIR="$PWD/../builders_vault_bundle/dist/$product" bash BUILD_PDF.sh
  popd >/dev/null
done

echo ""
echo "=== Bundle complete ==="
find "$ROOT/builders_vault_bundle/dist" -name "*.pdf" | wc -l
echo "PDFs built total."
