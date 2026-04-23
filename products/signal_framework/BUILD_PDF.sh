#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="${OUT_DIR:-./dist}"; mkdir -p "$OUT_DIR"
build() { command -v pandoc >/dev/null && pandoc "$1" --metadata title="$3" -o "$2" && return 0; echo "install pandoc"; return 1; }
build README.md                             "$OUT_DIR/01_README.pdf"    "Signal Framework Overview"
build SIGNAL_FRAMEWORK_GUIDE.md             "$OUT_DIR/02_Guide.pdf"     "Dream 100 + FOTW"
build DREAM_100_WORKBOOK.md                 "$OUT_DIR/03_Workbook.pdf"  "Dream 100 Workbook"
build SIGNAL_LOG_TEMPLATE.md                "$OUT_DIR/04_LogTemplate.pdf" "Weekly Signal Log"
build examples/5_signal_extractions.md      "$OUT_DIR/05_Examples.pdf"  "5 Worked Examples"
echo "PDFs → $OUT_DIR/"
