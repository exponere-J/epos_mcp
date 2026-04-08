import argparse
import time
import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- NEXT STEPS™: SELECTOR LIBRARY ---
# Decoupled selectors for easy updates
SELECTORS = {
  "chatgpt": {
    "wait_for": "div[data-message-author-role]",
    "container": "article", 
    "content_selector": ".markdown" 
  },
  "claude": {
    "wait_for": ".font-claude-message",
    "container": ".font-user-message, .font-claude-message",
    "content_selector": ".font-claude-message"
  },
  "perplexity": {
    "wait_for": "div.prose",
    "container": "div.prose",
    "content_selector": "div.prose"
  }
}

def extract(url, platform, output_format="md", headless=False):
    print(f"🔹 Next Steps™ A1: Connecting to {platform}...")
    
    with sync_playwright() as p:
        # ATTEMPT TO CONNECT TO USER'S EXISTING CHROME SESSION
        # This is the "Magic" feature - no login required if Chrome is open/used recently
        user_data = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
        try:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data, 
                headless=headless, 
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"]
            )
        except Exception as e:
            print(f"⚠️  Session Note: Could not attach to main Chrome profile. Using isolated session.\n   (Error: {e})")
            browser = p.chromium.launch(headless=False).new_context()

        page = browser.new_page()
        try:
            page.goto(url)
            # SMART WAIT
            sel = SELECTORS.get(platform, {}).get("wait_for", "body")
            page.wait_for_selector(sel, timeout=20000)
            print("✅ Thread Loaded.")
        except Exception as e:
            print(f"❌ Error loading page: {e}")
            browser.close()
            return

        # EXTRACTION LOGIC
        config = SELECTORS.get(platform, {})
        elements = page.query_selector_all(config.get("container", "div"))
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # MARKDOWN OUTPUT (The "Research" Product)
        if output_format == "md":
            out_text = f"# Next Steps Extraction: {platform.upper()}\n"
            out_text += f"**Source:** {url}\n**Date:** {timestamp}\n\n---\n\n"
            for el in elements:
                out_text += f"{el.inner_text()}\n\n---\n"
            
            # Save to 'exports' folder relative to where script is run, or user defined
            if not os.path.exists("exports"): os.makedirs("exports")
            filename = f"exports/extraction_{platform}_{int(time.time())}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(out_text)
        
        # JSON OUTPUT (The "Automation" Product)
        elif output_format == "json":
            data = {"source": url, "platform": platform, "date": timestamp, "messages": []}
            for el in elements:
                data["messages"].append(el.inner_text())
            
            if not os.path.exists("exports"): os.makedirs("exports")
            filename = f"exports/extraction_{platform}_{int(time.time())}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        print(f"💾 Saved to: {os.path.abspath(filename)}")
        time.sleep(1) 
        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Next Steps™ Context Extractor")
    parser.add_argument("url", help="The URL of the chat thread")
    parser.add_argument("--platform", required=True, choices=["chatgpt", "claude", "perplexity"])
    parser.add_argument("--format", choices=["md", "json"], default="md", help="Output format")
    parser.add_argument("--headless", action="store_true", help="Run invisibly")
    
    args = parser.parse_args()
    extract(args.url, args.platform, args.format, args.headless)
