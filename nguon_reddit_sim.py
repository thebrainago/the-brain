# -*- coding: utf-8 -*-
r"""nguon_reddit_sim.py - REDDIT qua trinh duyet that (Playwright), vi JSON API
bi reddit chan. Chay bang python co playwright (AppData\Local\Python\bin).
Rut bai post (tieu de + link) tu HTML, ghi reports/reddit_sim_<ts>.json + luu DB.
Chay:  python nguon_reddit_sim.py              (SUB_MAC_DINH dau)
       python nguon_reddit_sim.py --sub Forex,algotrading
"""
import sys, time, json, re, pathlib, html as _h
from playwright.sync_api import sync_playwright

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

SUB_MAC_DINH = ["Forex", "algotrading", "options", "Daytrading", "swingtrading",
                "futures", "Trading", "quantitative", "TradingView"]

def _doc_sub(page, sub, so_mong=60):
    """Mo 1 sub, cuon nguoi, rut cac post (tieu de + link)."""
    url = f"https://www.reddit.com/r/{sub}/"
    page.goto(url, timeout=40000)
    page.wait_for_timeout(2500)
    # cuon nguoi de load them
    for _ in range(4):
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(900)
    posts = []
    try:
        items = page.query_selector_all('a[href*="/comments/"]')
        for el in items:
            href = el.get_attribute("href") or ""
            txt = (el.inner_text() or "").strip()
            if "/comments/" not in href or href in [p["url"] for p in posts]:
                continue
            if txt:
                posts.append({"ten": _h.unescape(txt)[:200], "url": "https://www.reddit.com"+href})
            if len(posts) >= so_mong:
                break
    except Exception:
        pass
    return posts

def chay(subs=None, so_mong=40):
    subs = subs or SUB_MAC_DINH
    ds = []
    seen = set()
    thong_ke = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True,
                              args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                            viewport={"width":1440,"height":900}, locale="en-US")
        page = ctx.new_page()
        page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        for sub in subs:
            try:
                posts = _doc_sub(page, sub, so_mong)
                thong_ke[sub] = len(posts)
                for _p in posts:
                    if _p["url"] in seen:
                        continue
                    seen.add(_p["url"])
                    _p["nguon_y"] = sub
                    _p["tu_khoa"] = "reddit:sim"
                    _p["thoi_gian"] = time.time()
                    ds.append(_p)
            except Exception as e:
                thong_ke[sub] = f"LOI {type(e).__name__}"
        b.close()
    # luu JSON
    ts = time.strftime("%Y%m%d_%H%M%S")
    f = LAB / "reports" / f"reddit_sim_{ts}.json"
    f.write_text(json.dumps({"thoi_gian": ts, "thong_ke": thong_ke, "bai": ds},
                            ensure_ascii=False, indent=1), encoding="utf-8")
    # luu DB
    them = 0
    try:
        import nguon_reddit as nr, bo_nao
        con = bo_nao.mo_db()
        them = nr.luu(con, ds)
    except Exception as e:
        print("LOI luu DB:", e)
    print(f"=== REDDIT SIM: {sum(v for v in thong_ke.values() if isinstance(v,int))} bai, them moi {them} ===")
    for sub, v in thong_ke.items():
        print(f"  r/{sub}: {v}")
    for d in ds[:12]:
        print(f"  [{d['nguon_y']}] {d['ten'][:55]}")

if __name__ == "__main__":
    subs = None
    if "--sub" in sys.argv:
        subs = [s.strip() for s in sys.argv[sys.argv.index("--sub")+1].split(",") if s]
    chay(subs)

