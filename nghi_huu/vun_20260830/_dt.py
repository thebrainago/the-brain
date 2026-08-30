import re, json, time
from playwright.sync_api import sync_playwright
CDP = "http://127.0.0.1:9224"
urls = ["https://www.darwinex.com/data/darwin-api",
        "https://www.darwinex.com/es/data/darwin-api"]
try:
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(CDP)
        ctx = b.contexts[0] if b.contexts else b.new_context()
        pg = ctx.new_page()
        got = ""
        for u in urls:
            try:
                pg.goto(u, timeout=25000, wait_until="domcontentloaded")
                time.sleep(4)
                txt = pg.inner_text("body", timeout=20000)
                got += txt
                print("URL", u, "len", len(txt))
                break
            except Exception as e:
                print("nav err", u, repr(e)[:80])
        # quet tim token/key
        m = re.findall(r"([A-Za-z0-9_\-\.]{40,})", got)
        print("cand:", [x[:30] for x in m[:8]])
        print("co 'Access Token'?", "access token" in got.lower(), "| 'Sign in'?", "sign in" in got.lower(), "| mat khau?", "password" in got.lower())
        pg.close()
except Exception as e:
    print("ERR", repr(e)[:200])
