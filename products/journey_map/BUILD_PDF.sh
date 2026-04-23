#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="${OUT_DIR:-./dist}"; mkdir -p "$OUT_DIR"
build() { command -v pandoc >/dev/null && pandoc "$1" --metadata title="$3" -o "$2" && return 0; echo "install pandoc"; return 1; }
build README.md                       "$OUT_DIR/01_README.pdf"    "Journey Map Overview"
build JOURNEY_MAP_GUIDE.md            "$OUT_DIR/02_Guide.pdf"     "The 31x13 Journey Map"
build TEMPLATE_31_TOUCHPOINTS.md      "$OUT_DIR/03_Template.pdf"  "Blank Template"
build LAYER_CHEATSHEET.md             "$OUT_DIR/04_Layers.pdf"    "13-Layer Cheatsheet"
echo "PDFs → $OUT_DIR/"
