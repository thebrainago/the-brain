# -*- coding: utf-8 -*-
r"""nguon_dien_dan.py - NGUON DIEN DAN (khong can dang nhap): futures.io, Trade2Win,
Forex Factory Trading Systems, Quant StackExchange, Smart-Lab (ru), Traderviet (vi).
Dung Playwright (bin python) doc trang list, rut cac link bai + tieu de (heuristic,
khong can CSS rieng), luu vao bang muc + tao task scout cho Seeker.

Chay:  python nguon_dien_dan.py --dien-dan futures,quant,forexfactory
       python nguon_dien_dan.py                    (tat ca)
"""
import sys, time, json, re, pathlib, random, html as _h
from playwright.sync_api import sync_playwright

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

# (ten, trang_list, danh_sach bai loc theo marker trong href)
DIEN_DAN = [
    ("futures.io", "https://futures.io/forum", ["/thread/", "/forum"]),
    ("traderslaboratory", "https://www.traderslaboratory.com/forums/", ["/threads/", "/forums/"]),
    ("forexfactory", "https://www.forexfactory.com/thread/post/1#p1", ["/thread/"]),
    ("quant", "https://quant.stackexchange.com/questions", ["/questions/"]),
    ("smartlab", "https://smart-lab.ru/forum/", ["/forum/"]),
    ("traderviet", "https://traderviet.com/forums/", ["/threads/", "/forums/"]),
]
MARKER = ["/thread/", "/threads/", "/questions/", "/question/", "/topic/", "/forum/", "/forums/", "/showthread"]


def _doc_trang(page, url):
    for lan in range(3):
        try:
            page.goto(url, timeout=40000)
            break
        except Exception:
            if lan == 2:
                raise
            time.sleep(6 * (lan + 1))
    page.wait_for_timeout(2500)
    time.sleep(1.5)
    for _ in range(3):
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(800)
    return page

def _rut_page(page, ten_loai, marker):
    """Rut (link, tieu de) tu trang list. Heuristic: loc theo marker."""
    out, seen = [], set()
    for el in page.query_selector_all("a[href]"):
        href = el.get_attribute("href") or ""
        txt = (el.inner_text() or "").strip()
        if not txt or len(txt) < 18:
            continue
        if not any(m in href for m in marker):
            continue
        if href.startswith("/"):
            # doi sang absolute theo origin
            origin = page.evaluate("location.origin")
            href = origin + href
        if "reddit" in href or "javascript" in href or "google" in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        out.append({"ten": _h.unescape(re.sub(r"\s+", " ", txt))[:200], "url": href, "loai": ten_loai})
    return out[:80]

def chay(danh_sach=None, so_moi_forum=40):
    danh_sach = [d for d in DIEN_DAN if (not danh_sach) or d[0] in danh_sach]
    ds, thong_ke = [], {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                            viewport={"width":1440,"height":900}, locale="en-US")
        page = ctx.new_page()
        page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        for i, (ten, url, marker) in enumerate(danh_sach):
            if i > 0:
                time.sleep(random.uniform(6, 10))
            try:
                page = _doc_trang(page, url)
                posts = _rut_page(page, ten, marker)[:so_moi_forum]
                thong_ke[ten] = len(posts)
                for p_ in posts:
                    p_["nguon_y"] = ten
                    p_["tu_khoa"] = "dien_dan:" + ten
                    p_["thoi_gian"] = time.time()
                    ds.append(p_)
            except Exception as e:
                thong_ke[ten] = f"LOI {type(e).__name__}: {str(e)[:40]}"
        b.close()
    ts = time.strftime("%Y%m%d_%H%M%S")
    f = LAB / "reports" / f"dien_dan_{ts}.json"
    f.write_text(json.dumps({"thoi_gian": ts, "thong_ke": thong_ke, "bai": ds},
                            ensure_ascii=False, indent=1), encoding="utf-8")
    them = 0
    try:
        import bo_nao
        con = bo_nao.mo_db()
        for d in ds:
            mid = bo_nao.bam(d["url"])
            try:
                con.execute("INSERT OR IGNORE INTO muc(id,nguon,ten,url,ngay,da_xu) VALUES(?,?,?,?,?,0)",
                            (mid, "dien_dan", d["ten"], d["url"], time.time()))
                if con.execute("SELECT da_xu FROM muc WHERE id=?", (mid,)).fetchone()[0] == 0:
                    bo_nao.tao_task(con, "scout", {"ten": d["ten"], "url": d["url"], "van_ban": "",
                                                   "nguon_y": d["nguon_y"], "tu_khoa": d["tu_khoa"]},
                                    muc_id=mid, uu_tien=0, huong="seeker")
                    them += 1
            except Exception:
                pass
        con.commit()
    except Exception as e:
        print("LOI luu DB:", e)
    print(f"=== DIEN DAN: tong {len(ds)} bai, them moi {them} ===")
    for t, v in thong_ke.items():
        print(f"  {t}: {v}")
    for d in ds[:20]:
        print(f"  [{d['nguon_y']}] {d['ten'][:55]} | {d['url'][:60]}")

if __name__ == "__main__":
    danh_sach = None
    if "--dien-dan" in sys.argv:
        danh_sach = [x.strip() for x in sys.argv[sys.argv.index("--dien-dan")+1].split(",") if x.strip()]
    chay(danh_sach)

