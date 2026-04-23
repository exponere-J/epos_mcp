#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="${OUT_DIR:-./dist}"; mkdir -p "$OUT_DIR"
build() { command -v pandoc >/dev/null && pandoc "$1" --metadata title="$3" -o "$2" && return 0; echo "install pandoc"; return 1; }
build README.md                  "$OUT_DIR/01_README.pdf"     "Voice Pack Overview"
build VOICE_PACK_GUIDE.md        "$OUT_DIR/02_Guide.pdf"      "Voice-First Prompting"
build 30_PROMPTS.md              "$OUT_DIR/03_30_Prompts.pdf" "30 Voice Prompts"
build VOCABULARY_CORRECTIONS.md  "$OUT_DIR/04_Vocab.pdf"      "Vocabulary Corrections"
echo "PDFs → $OUT_DIR/"
