# -*- coding: utf-8 -*-
"""Chup man hinh trang Darwinex bang profile da dang nhap (dung cho screen-read)."""
import sys, pathlib, time
from playwright.sync_api import sync_playwright

LAB = pathlib.Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
PROFILE = LAB / ".browser_darwinex"
OUT = LAB / "reports" / "darwinex_shots"
OUT.mkdir(parents=True, exist_ok=True)
URLS = [
    "https://www.darwinex.com/data/darwin-api",
    "https://www.darwinex.com/account",
]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE), headless=True, user_agent=UA,
            viewport={"width": 1300, "height": 900}, locale="en-US",
            args=["--disable-blink-features=AutomationControlled"])
        page = ctx.new_page() if len(ctx.pages) == 0 else ctx.pages[0]
        for i, u in enumerate(URLS):
            try:
                page.goto(u, timeout=25000, wait_until="domcontentloaded")
                time.sleep(4)
                page.screenshot(path=str(OUT / f"shot_{i}_{u.split('/')[-1] or 'root'}.png"))
                print(f"[OK] {u} -> {OUT}\\shot_{i}_{u.split('/')[-1] or 'root'}.png | title={page.title()[:60]!r}")
                txt = page.evaluate("document.body ? document.body.innerText.slice(0,600) : ''")
                print("   TEXT:", txt.replace(chr(10), ' | ')[:300])
            except Exception as e:
                print(f"[LOI] {u} :: {str(e)[:120]}")
        ctx.close()

if __name__ == "__main__":
    main()
