import sys, time, os
from playwright.sync_api import sync_playwright
ids = sys.argv[1:]
out = r"C:\Research SP500\lab\du_lieu_cao\mql5"
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9224")
    ctx = b.contexts[0]
    for i, sid in enumerate(ids):
        if i: time.sleep(5.5)
        url = f"https://www.mql5.com/en/signals/{sid}/export/positions"
        r = ctx.request.get(url, headers={"Referer": f"https://www.mql5.com/en/signals/{sid}"}, timeout=60000)
        body = r.body()
        print(sid, r.status, len(body), flush=True)
        if r.status != 200 or len(body) < 200:
            print("DUNG: ma", r.status, body[:120]); break
        open(os.path.join(out, f"mql5_{sid}_positions.csv"), "wb").write(body)
