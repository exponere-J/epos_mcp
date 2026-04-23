#!/usr/bin/env bash
# Build PDFs for the Pre-Mortem Kit.
# Same dark-mode styling as the CCP Pack.

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
code { background: #2a2a2a; color: #f5b642; padding: .15em .3em; border-radius: 3px; }
pre { background: #2a2a2a; padding: 1em; border-left: 3px solid #f5b642; overflow-x: auto; }
pre code { background: none; color: #e5e5e5; }
a { color: #4ec9b0; }
blockquote { border-left: 3px solid #f5b642; margin-left: 0; padding-left: 1em; color: #aaa; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #444; padding: .5em; }
th { background: #2a2a2a; }
CSS

build_one() {
  local infile="$1" outfile="$2" title="$3"
  if command -v pandoc >/dev/null 2>&1; then
    pandoc "$infile" --pdf-engine=weasyprint --css="$STYLE_CSS" \
           --metadata title="$title" -o "$outfile" 2>/dev/null && return 0
    pandoc "$infile" --metadata title="$title" -o "$outfile" && return 0
  fi
  echo "ERROR: install pandoc (and optionally weasyprint for dark-mode styling)"
  return 1
}

build_one README.md                                "$OUT_DIR/01_README.pdf"                     "Pre-Mortem Kit — Overview"
build_one PRE_MORTEM_FRAMEWORK.md                  "$OUT_DIR/02_Framework.pdf"                  "The Pre-Mortem Framework"
build_one constitutional/01_EPOS_Constitution.md   "$OUT_DIR/03_Constitution.pdf"               "EPOS Constitution"
build_one constitutional/02_Failure_Scenarios.md   "$OUT_DIR/04_Failure_Scenarios.pdf"          "Failure Scenarios"
build_one constitutional/03_Path_Clarity_Rules.md  "$OUT_DIR/05_Path_Clarity.pdf"               "Path Clarity Rules"
build_one constitutional/04_Pre_Flight_Checklist.md "$OUT_DIR/06_Pre_Flight.pdf"                "Pre-Flight Checklist"
build_one constitutional/05_Environment_Spec.md    "$OUT_DIR/07_Environment_Spec.pdf"           "Environment Spec"
build_one EPOS_DOCTOR_REFERENCE.md                 "$OUT_DIR/08_Doctor_Reference.pdf"           "EPOS Doctor Reference"

echo ""
echo "Built PDFs → $OUT_DIR/"
ls -la "$OUT_DIR"
