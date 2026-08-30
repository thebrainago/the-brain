from playwright.sync_api import sync_playwright
targets = [
  ("X|QuantConnect", "https://twitter.com/QuantConnect"),
  ("X|Quant_Research", "https://twitter.com/quant_research"),
  ("Web|Quantpedia", "https://quantpedia.com/"),
]
try:
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9224")
        ctx = b.contexts[0]
        for name, url in targets:
            try:
                pg = ctx.new_page()
                pg.goto(url, timeout=25000)
                pg.wait_for_timeout(2500)
                t = pg.inner_text("body")
                print("== ", name, "len=", len(t))
                print("   ", t[:400].replace("\n", " | "))
                pg.close()
            except Exception as e:
                print("== ", name, "ERR", repr(e)[:120])
except Exception as e:
    print("CONNECT ERR", repr(e)[:200])
