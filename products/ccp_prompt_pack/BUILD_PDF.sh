#!/usr/bin/env bash
# Build PDFs for the CCP Prompt Pack.
#
# Uses pandoc if available; falls back to weasyprint; falls back to a
# curl-to-public-converter note. Dark mode styling via CSS.

set -euo pipefail

OUT_DIR="${OUT_DIR:-./dist}"
mkdir -p "$OUT_DIR"

STYLE_CSS="$(mktemp /tmp/epos_dark_XXXX.css)"
cat > "$STYLE_CSS" <<'CSS'
body {
  background: #1a1a1a;
  color: #e5e5e5;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  line-height: 1.6;
  max-width: 780px;
  margin: 2em auto;
  padding: 0 2em;
}
h1, h2, h3, h4 { color: #f5b642; }
h1 { border-bottom: 2px solid #f5b642; padding-bottom: .3em; }
h2 { border-bottom: 1px solid #444; padding-bottom: .2em; margin-top: 2em; }
code {
  background: #2a2a2a;
  color: #f5b642;
  padding: .15em .3em;
  border-radius: 3px;
  font-size: .92em;
}
pre {
  background: #2a2a2a;
  padding: 1em;
  border-left: 3px solid #f5b642;
  border-radius: 3px;
  overflow-x: auto;
}
pre code { background: none; color: #e5e5e5; }
a { color: #4ec9b0; }
blockquote {
  border-left: 3px solid #f5b642;
  margin-left: 0;
  padding-left: 1em;
  color: #aaa;
}
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #444; padding: .5em; }
th { background: #2a2a2a; }
CSS

build_one() {
  local infile="$1" outfile="$2" title="$3"
  if command -v pandoc >/dev/null 2>&1; then
    pandoc "$infile" \
      --pdf-engine=weasyprint \
      --css="$STYLE_CSS" \
      --metadata title="$title" \
      -o "$outfile" 2>/dev/null && return 0
    # Fallback to pandoc built-in
    pandoc "$infile" --metadata title="$title" -o "$outfile" && return 0
  fi
  if command -v weasyprint >/dev/null 2>&1; then
    # weasyprint requires HTML; render markdown first if pandoc present
    if command -v pandoc >/dev/null 2>&1; then
      pandoc "$infile" -o "${infile%.md}.html" --css="$STYLE_CSS"
      weasyprint "${infile%.md}.html" "$outfile"
      return 0
    fi
  fi
  echo "ERROR: no PDF generator found. Install one of:"
  echo "  - pandoc + weasyprint (recommended)"
  echo "  - wkhtmltopdf"
  echo "  - prince"
  return 1
}

build_one README.md                      "$OUT_DIR/01_README.pdf"                "CCP Pack — Overview"
build_one CCP_METHODOLOGY_GUIDE.md       "$OUT_DIR/02_Methodology_Guide.pdf"     "The Concentric Context Protocol"
build_one QUICK_START.md                 "$OUT_DIR/03_Quick_Start.pdf"           "CCP Quick Start"
build_one templates/01_strategic_intent.md   "$OUT_DIR/04_Templates_Strategic.pdf"    "CCP Templates — Strategic Intent"
build_one templates/02_audience_modeling.md  "$OUT_DIR/05_Templates_Audience.pdf"     "CCP Templates — Audience Modeling"
build_one templates/03_content_production.md "$OUT_DIR/06_Templates_Content.pdf"      "CCP Templates — Content Production"
build_one templates/04_diagnostics.md        "$OUT_DIR/07_Templates_Diagnostics.pdf"  "CCP Templates — Diagnostics"
build_one templates/05_voice_to_structure.md "$OUT_DIR/08_Templates_Voice.pdf"        "CCP Templates — Voice to Structure"

echo ""
echo "Built PDFs → $OUT_DIR/"
ls -la "$OUT_DIR"
