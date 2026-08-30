import re, time
from playwright.sync_api import sync_playwright
CDP="http://127.0.0.1:9224"
import json, urllib.request
tabs=json.loads(urllib.request.urlopen(CDP+"/json",timeout=6).read())
print("=== TAB trong CDP 9224 ===")
for t in tabs:
    if t.get("type")=="page":
        print("*", t.get("title","")[:40], "|", t.get("url","")[:70])
try:
    with sync_playwright() as p:
        b=p.chromium.connect_over_cdp(CDP)
        ctx=b.contexts[0]
        pages=ctx.pages
        print("pages:", len(pages))
        target=None
        for pg in pages:
            u=pg.url or ""
            if "darwinex" in u or "data" in u or "account" in u or u.endswith("newtab") or u=="":
                target=pg; break
        if target is None and pages: target=pages[0]
        if not target:
            print("khong co tab"); raise SystemExit
        print("dung tab:", target.url)
        target.goto("https://www.darwinex.com/data/darwin-api", timeout=30000, wait_until="domcontentloaded")
        time.sleep(6)
        txt=target.inner_text("body", timeout=25000)
        print("body len:", len(txt))
        mm=re.findall(r"([A-Za-z0-9]{32,80}|\|[A-Za-z0-9]{20,}|[A-Za-z0-9_\-]{40,})", txt)
        print("cand:", [x[:40] for x in mm[:10]])
        print("dang nhap?", ("sign out" in txt.lower()) or ("log out" in txt.lower()) or ("welcome" in txt.lower()) or ("account" in txt.lower()))
except Exception as e:
    print("ERR", repr(e)[:200])
