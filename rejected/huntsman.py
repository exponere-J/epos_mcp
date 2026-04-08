import json
from typing import Any, Dict, Union
from playwright.async_api import async_playwright

def _spec(x: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(x, dict): return x
    if isinstance(x, str):
        try: return json.loads(x)
        except: return {"job":"open_url","url":x}
    return {"job":"open_url","url":str(x)}

async def run_browser(spec_in: Union[str, Dict[str, Any]]):
    spec = _spec(spec_in)
    job = spec.get("job","open_url")
    url = spec.get("url")
    headless = bool(spec.get("headless", True))
    
    if not url: return {"ok": False, "error": "Missing url"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")

        out = {"ok": False}
        if job == "screenshot":
            path = spec.get("path", "epos_hq/data/logs/screenshot.png")
            await page.screenshot(path=path)
            out = {"ok": True, "path": path}
        elif job == "extract_text":
            text = await page.inner_text("body")
            out = {"ok": True, "text": text[:2000]} # Limit size

        await browser.close()
        return out
