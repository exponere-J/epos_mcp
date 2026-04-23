#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="${OUT_DIR:-./dist}"
mkdir -p "$OUT_DIR"

build_one() {
  local infile="$1" outfile="$2" title="$3"
  command -v pandoc >/dev/null 2>&1 \
    && pandoc "$infile" --metadata title="$title" -o "$outfile" && return 0
  echo "ERROR: install pandoc"; return 1
}

build_one README.md                              "$OUT_DIR/01_README.pdf"           "Brand DNA Kit — Overview"
build_one BRAND_DNA_GUIDE.md                     "$OUT_DIR/02_Guide.pdf"            "The Brand DNA Method"
build_one DISCOVERY_SCRIPT.md                    "$OUT_DIR/03_Discovery.pdf"        "Discovery Script (6 buckets)"
build_one TEMPLATE_BRAND_DNA_PROFILE.md          "$OUT_DIR/04_Template.pdf"         "Profile Template"
build_one examples/epos_brand_dna.md             "$OUT_DIR/05_Example_EPOS.pdf"     "Example — EPOS"
build_one examples/consultant_example.md         "$OUT_DIR/06_Example_Consultant.pdf" "Example — Consultant"
build_one examples/local_service_example.md      "$OUT_DIR/07_Example_LocalSvc.pdf" "Example — Local Service"

echo "Built PDFs → $OUT_DIR/"
