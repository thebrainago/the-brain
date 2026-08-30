import re, time, json
from pathlib import Path
lab=Path(r"C:\Users\SV STORE\Downloads\Research SP500\lab")
from playwright.sync_api import sync_playwright
CDP="http://127.0.0.1:9224"
try:
    with sync_playwright() as p:
        b=p.chromium.connect_over_cdp(CDP)
        ctx=b.contexts[0]
        pg=ctx.new_page()
        r={}
        for u,label in [("https://www.darwinex.com/","home"),
                        ("https://www.darwinex.com/account","account"),
                        ("https://www.darwinex.com/data/darwin-api","api")]:
            try:
                pg.goto(u, timeout=30000, wait_until="load")
                time.sleep(6)
                t=pg.inner_text("body", timeout=25000)
                low=t.lower()
                r[label]={"len":len(t),
                          "login": any(k in low for k in ["sign out","log out","my account","logout","dashboard","portfolio","darwin"]),
                          "token?_": bool(re.search(r"[A-Za-z0-9_\-]{40,}", t))}
                print(label, r[label])
            except Exception as e:
                print(label,"ERR",repr(e)[:80])
        pg.close()
        (lab/"reports"/"darwin_session.json").write_text(json.dumps(r,ensure_ascii=False,indent=1),encoding="utf-8")
except Exception as e:
    print("ERR",repr(e)[:200])
