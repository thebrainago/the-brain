# -*- coding: utf-8 -*-
r"""doc_cdp.py - Doc X/TikTok/Facebook qua CDP tren TRINH DUYET DA DANG NHAP
(.browser_thebrain2). Noi toi Chrome dang chay tai 127.0.0.1:9222, dieu khien
cac tab, tim kiem theo tu khoa va trich noi dung.

Chay (python co playwright - AppData\Local\Python\bin\python.exe):
  python doc_cdp.py --xem            : chi in, khong luu
  python doc_cdp.py --quet <tu_khoa> : quet 1 tu khoa
  python doc_cdp.py                  : quet theo keyword bank
"""
import sys, time, pathlib, json, html as _h, re

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))
CDP = "http://127.0.0.1:9222"


def _mo():
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    b = p.chromium.connect_over_cdp(CDP)
    return p, b


def _trang(b, dau):
    for ctx in b.contexts:
        for pg in ctx.pages:
            if dau in pg.url:
                return pg
    return None


def _mo_trang(b, url):
    for ctx in b.contexts:
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            pg.bring_to_front()
            pg.goto(url, timeout=25000, wait_until="domcontentloaded")
            pg.wait_for_timeout(4000)
            return pg
        except Exception:
            return pg
    return None


def _noi_dung(pg, vong_cuon=3):
    """Cuon doc va trich toan bo text."""
    mo = []
    for _ in range(vong_cuon):
        try:
            pg.mouse.wheel(0, 2500)
            pg.wait_for_timeout(1500)
        except Exception:
            pass
    try:
        mo = pg.evaluate("document.body.innerText")
    except Exception:
        mo = ""
    return mo


# ---------------- X ----------------
def doc_x(tk, so=10):
    from playwright.sync_api import sync_playwright
    p, b = _mo()
    try:
        pg = _mo_trang(b, f"https://x.com/search?q={tk.replace(' ','%20')}&f=live")
        if not pg:
            return []
        _noi_dung(pg, 3)
        try:
            arts = pg.evaluate("""() => Array.from(document.querySelectorAll('article')).map(a => a.innerText)""")
        except Exception:
            arts = []
        return arts[:so]
    finally:
        b.close(); p.stop()


# ---------------- TikTok ----------------
def doc_tiktok(tk, so=10):
    p, b = _mo()
    try:
        pg = _mo_trang(b, f"https://www.tiktok.com/search/video?q={tk.replace(' ','%20')}")
        if not pg:
            return []
        _noi_dung(pg, 3)
        try:
            txt = pg.evaluate("document.body.innerText")
        except Exception:
            txt = ""
        return [t for t in txt.split("\n") if t.strip()][:so]
    finally:
        b.close(); p.stop()


# ---------------- Facebook ----------------
def doc_facebook(tk, so=10):
    p, b = _mo()
    try:
        pg = _mo_trang(b, f"https://www.facebook.com/search/posts?q={tk.replace(' ','%20')}")
        if not pg:
            return []
        _noi_dung(pg, 3)
        try:
            txt = pg.evaluate("document.body.innerText")
        except Exception:
            txt = ""
        return [t for t in txt.split("\n") if t.strip()][:so]
    finally:
        b.close(); p.stop()


def luu(con, ds):
    import bo_nao
    them = 0
    for d in ds:
        if not d.get("url"):
            continue
        mid = bo_nao.bam(d["url"])
        ten = (d.get("ten") or (d.get("text") or d["url"])[:120])
        try:
            con.execute("INSERT OR IGNORE INTO muc(id,nguon,ten,url,ngay,da_xu) "
                        "VALUES(?,?,?,?,?,0)", (mid, d.get("nguon", "social"), ten, d["url"], time.time()))
            row = con.execute("SELECT da_xu FROM muc WHERE id=?", (mid,)).fetchone()
            if row and row[0] == 0:
                bo_nao.tao_task(con, "scout",
                                {"ten": ten, "url": d["url"], "van_ban": d.get("text", ""),
                                 "tu_khoa": d.get("tu_khoa", "")},
                                muc_id=mid, uu_tien=0, huong="seeker")
                them += 1
        except Exception:
            pass
    con.commit()
    return them


NOISE = {"log in", "for you", "explore", "following", "live", "upload", "profile",
          "more", "filters", "all", "people", "reels", "marketplace", "videos",
          "users", "groups", "pages", "events", "see more", "see new posts", "post",
          "your home timeline", "show 35 posts", "what's happening"}
GIOI_HAN_NEN = 5


def _sach(t):
    t = (t or "").strip()
    if len(t) < 25:
        return False
    if t.lower() in NOISE:
        return False
    return True


def quet(tu_khoa, nguon="tat_ca"):
    """Doc 1 tu khoa tren cac nen tang. Tra ds bai."""
    ds = []
    def _theo(nguon_, mang, mo):
        for mang_i, t in enumerate(mang[:GIOI_HAN_NEN], 1):
            if not _sach(t):
                continue
            ds.append({"nguon": nguon_, "url": f"https://{mo}/search?q={tu_khoa.replace(' ','%20')}#{mang_i}",
                       "ten": f"{nguon_}: {tu_khoa}", "text": t[:400], "tu_khoa": tu_khoa})
    if nguon in ("tat_ca", "x"):
        _theo("x", doc_x(tu_khoa), "x.com")
    if nguon in ("tat_ca", "tiktok"):
        _theo("tiktok", doc_tiktok(tu_khoa), "www.tiktok.com")
    if nguon in ("tat_ca", "facebook"):
        _theo("facebook", doc_facebook(tu_khoa), "www.facebook.com")
    # loai trung noi dung
    da = set(); kq = []
    for d in ds:
        if d["text"] in da:
            continue
        da.add(d["text"]); kq.append(d)
    return kq


def main():
    args = sys.argv
    ds = []
    if "--quet" in args:
        tk = args[args.index("--quet") + 1]
        ds = quet(tk)
    else:
        try:
            import keywords_nguon as kw
            tu = []
            for dm in ("cho_tin_hieu", "dang_doi", "cong_dong"):
                tu += [k for k in kw.DANH_MUC[dm]["tu_khoa"].get("en", []) if len(k) > 3][:4]
            tu = list(dict.fromkeys(tu))
        except Exception:
            tu = ["forex signals", "top trader", "trading community"]
        for tk in tu[:4]:
            ds += quet(tk)
    print(f"QUET duoc {len(ds)} bai")
    for d in ds[:20]:
        print(f"  [{d['nguon']}] {d['text'][:70]}")
    if "--xem" not in args and ds:
        import bo_nao
        con = bo_nao.mo_db()
        n = luu(con, ds)
        print(f"LUU them {n}")


if __name__ == "__main__":
    main()
