NEXT STEPS™ A1: CONTEXT EXTRACTOR
=================================
Version: 1.0.0 | (c) 2025 Exponere

STOP LOSING YOUR GENIUS IN THE CHAT HISTORY.
Next Steps™ A1 is a headless, local tool that extracts clean data from your AI conversations.

FEATURES:
- 🔒 Runs Locally: No data sent to third-party clouds.
- ⚡ Pipeline Ready: Output to Markdown (for notes) or JSON (for automations).
- 🧩 Platform Agnostic: Works with ChatGPT, Claude, and Perplexity.
- 🔑 No API Keys Needed: Uses your existing browser session.

QUICK START:
1. Ensure you have Python installed.
2. Open this folder in your terminal.
3. Install the engine:
   pip install playwright
   playwright install chromium

USAGE:
   # Basic Extraction (Markdown)
   python src/extract.py "YOUR_CHAT_URL" --platform perplexity
   
   # Automation Mode (JSON)
   python src/extract.py "YOUR_CHAT_URL" --platform claude --format json

TROUBLESHOOTING:
- If Chrome fails to launch, ensure all Chrome windows are closed or use the --headless flag.
