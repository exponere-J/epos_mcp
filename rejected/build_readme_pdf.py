from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import os

NAVY = colors.HexColor("#0A1628")
BLUE = colors.HexColor("#00D4FF")
GOLD = colors.HexColor("#FFB84D")
TEXT = colors.HexColor("#F0F4F8")
MUTED = colors.HexColor("#8892b0")

OUT_PATH = "README.pdf"

TITLE = "MEMORY VAULT"
SUBTITLE = "by Next Steps™"
TAGLINE = "Your Conversations. Your Filesystem. Your Control."
VERSION = "Version 1.0"

PAGES = [
    ("WHAT IS MEMORY VAULT?",
     [
         ("THE PROBLEM", [
             "You spend hours having breakthrough conversations with AI assistants.",
             "Then you close the tab.",
             "Gone. Unsearchable. Unrecoverable."
         ]),
         ("THE SOLUTION", [
             "Memory Vault captures conversations before the tab closes.",
             "Saves them locally. Structures them. Makes them searchable forever."
         ]),
         ("KEY FEATURES", [
             "Multi-platform support (ChatGPT, Claude, Perplexity)",
             "Local-first architecture (zero cloud dependency)",
             "Clean Markdown exports (universal format)",
             "One-time purchase model (no subscriptions)"
         ])
     ]),

    ("QUICK START",
     [
         ("INSTALLATION (3 minutes)", [
             "1) Extract MemoryVault_v1.0.zip to any folder",
             "2) Double-click setup.bat",
             "3) Wait for dependencies to install (automatic)",
             "4) Done — Memory Vault is ready"
         ]),
         ("FIRST USE", [
             "1) Double-click launch.bat",
             "2) Open: http://localhost:8501",
             "3) Paste a ChatGPT/Claude/Perplexity URL",
             "4) Click “EXTRACT & ARCHIVE”",
             "5) Find exports in the exports/ folder"
         ])
     ]),

    ("ARCHITECTURE & PRIVACY",
     [
         ("HOW IT WORKS", [
             "Memory Vault uses browser automation to extract conversation content.",
             "Everything runs locally on your machine."
         ]),
         ("PRIVACY GUARANTEE", [
             "No API keys required",
             "No cloud upload",
             "No telemetry / tracking",
             "Your data never leaves your computer"
         ]),
         ("TECHNICAL DETAILS", [
             "Language: Python 3.10+",
             "UI: Streamlit",
             "Storage: Markdown + local folders",
             "Automation: Playwright-based extraction"
         ])
     ]),

    ("TROUBLESHOOTING",
     [
         ("“Python not found”", [
             "Install Python 3.10+ from python.org, then rerun setup.bat"
         ]),
         ("“Browser login required”", [
             "If login is detected, log in manually, then retry extraction."
         ]),
         ("“Extraction timeout”", [
             "Disable headless mode in the UI and try again.",
             "Confirm your connection and that the target page loads."
         ]),
         ("SUPPORT", [
             "If you need help, reply to your purchase receipt email with details."
         ])
     ]),

    ("FUTURE ROADMAP",
     [
         ("COMING SOON", [
             "Advanced search (semantic, not just keyword)",
             "Auto-tagging by topic/project",
             "Export targets (Obsidian/Notion/Roam)",
             "Browser extension (one-click capture)"
         ]),
         ("MODEL", [
             "One-time purchase. Lifetime updates. No subscriptions."
         ])
     ]),
]

def draw_header(c, w, h, page_title=None):
    c.setFillColor(NAVY)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(w/2, h - 1.25*inch, TITLE)

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 12)
    c.drawCentredString(w/2, h - 1.55*inch, f"{SUBTITLE}  •  {VERSION}")

    if page_title:
        c.setFillColor(BLUE)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(0.85*inch, h - 2.05*inch, page_title)

    c.setStrokeColor(colors.HexColor("#233554"))
    c.setLineWidth(1)
    c.line(0.75*inch, h - 2.15*inch, w - 0.75*inch, h - 2.15*inch)

def draw_footer(c, w):
    c.setFillColor(colors.HexColor("#445"))
    c.setFont("Helvetica", 9)
    c.drawCentredString(w/2, 0.55*inch, "NEXT STEPS™ // SOVEREIGN TECH")

def draw_section(c, x, y, heading, bullets, w, line_h=14):
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, heading)
    y -= 0.18*inch

    c.setFillColor(TEXT)
    c.setFont("Helvetica", 11)

    for b in bullets:
        # wrap crude
        words = b.split()
        line = ""
        lines = []
        for word in words:
            test = (line + " " + word).strip()
            if c.stringWidth(test, "Helvetica", 11) > (w - 2*x):
                lines.append(line)
                line = word
            else:
                line = test
        if line:
            lines.append(line)

        for ln in lines:
            c.drawString(x, y, f"• {ln}" if ln == lines[0] else f"  {ln}")
            y -= line_h
        y -= 4
    y -= 6
    return y

def main():
    w, h = letter
    c = canvas.Canvas(OUT_PATH, pagesize=letter)

    # Cover
    draw_header(c, w, h, None)
    c.setFillColor(TEXT)
    c.setFont("Helvetica", 14)
    c.drawCentredString(w/2, h - 2.05*inch, TAGLINE)

    c.setFillColor(colors.HexColor("#233554"))
    c.roundRect(w/2 - 2.2*inch, h - 3.15*inch, 4.4*inch, 0.75*inch, 8, fill=0, stroke=1)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(w/2, h - 2.75*inch, "SYSTEM: ONLINE  //  SOVEREIGN ARCHIVE")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 10)
    c.drawCentredString(w/2, 1.25*inch, f"Generated: {datetime.now().strftime('%Y-%m-%d')}")
    draw_footer(c, w)
    c.showPage()

    # Content pages
    for title, sections in PAGES:
        draw_header(c, w, h, title)
        y = h - 2.55*inch
        x = 0.85*inch
        for heading, bullets in sections:
            y = draw_section(c, x, y, heading, bullets, w)
            if y < 1.6*inch:
                draw_footer(c, w)
                c.showPage()
                draw_header(c, w, h, title + " (cont.)")
                y = h - 2.55*inch
        draw_footer(c, w)
        c.showPage()

    c.save()
    print(f"[OK] Wrote {OUT_PATH}")

if __name__ == "__main__":
    main()
