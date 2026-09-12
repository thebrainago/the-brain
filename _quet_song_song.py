# -*- coding: utf-8 -*-
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
MUC_TIEU = [
  ("Reddit r/algotrading", "https://www.reddit.com/r/algotrading/hot/"),
  ("Reddit r/quant", "https://www.reddit.com/r/quant/hot/"),
  ("MQL5 Signals", "https://www.mql5.com/en/signals"),
  ("Myfxbook", "https://www.myfxbook.com/"),
  ("Collective2", "https://www.collective2.com/"),
  ("TikTok EN", "https://www.tiktok.com/search/video?q=quant"),
  ("TikTok RU", "https://www.tiktok.com/search/video?q=%D0%BA%D0%B2%D0%B0%D0%BD%D1%82"),
  ("TikTok ZH", "https://www.tiktok.com/search/video?q=%E9%87%8F%E5%8C%96"),
  ("X EN", "https://x.com/search?q=quant&f=live"),
  ("X ES", "https://x.com/search?q=trading%20cuantitativo&f=live"),
  ("Facebook", "https://www.facebook.com/search/posts?q=quant"),
  ("YouTube algo", "https://www.youtube.com/results?search_query=algorithmic+trading"),
  ("YouTube RU", "https://www.youtube.com/results?search_query=%D0%B0%D0%BB%D0%B3%D0%BE%D1%80%D0%B8%D1%82%D0%BC%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B0%D1%8F+%D1%82%D0%BE%D1%80%D0%B3%D0%BE%D0%B2%D0%BB%D1%8F"),
]
async def mo(b, ctx, ten, url):
    pg = await ctx.new_page()
    try:
        await pg.bring_to_front()
    except Exception:
        pass
    try:
        await pg.goto(url, timeout=25000, wait_until="domcontentloaded")
        try:
            await pg.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        ttl = await pg.title()
        txt = await pg.inner_text("body")
        return ten, (ttl or url)[:45], len(txt or "")
    except Exception as e:
        return ten, "LOI " + type(e).__name__, 0
async def main():
    from playwright.async_api import async_playwright
    from nhan import doc_trinh_duyet as DT
    port = DT.cdp_dang_chay()
    print("cdp:", port)
    if not port:
        print("chua mo CDP"); return
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp("http://127.0.0.1:%d" % port)
        ctx = b.contexts[0] if b.contexts else await b.new_context()
        ds = await asyncio.gather(*[mo(b, ctx, t, u) for t, u in MUC_TIEU])
        print("mo %d tab song song:" % len(ds))
        for t, u, n in ds:
            print("  [%s] len=%d %s" % (t, n, u))
asyncio.run(main())
