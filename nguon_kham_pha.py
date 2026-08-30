# -*- coding: utf-8 -*-
"""nguon_kham_pha.py - TU KHAM PHA NGUON (SEENER): tu sinh keyword, tu do
username kenh/nhom, tu doc kenh cong khai KHONG CAN LOGIN hay bot.

Cac me:
  1) Telegram: doc kenh cong khai qua t.me/s/<username> (khong can bot). Tu sinh
     username tu keyword + de seed, do xem ton tai khong, roi doc tin.
  2) Mang xa hoi (X/TikTok/Facebook/Reddit): quet lead tu search engine (best-effort,
     neu mang org thi bo qua). Reddit co API cong khai JSON.
  3) Ghi vao bang muc + tao task scout (huong seeker).

Chay:
  python nguon_kham_pha.py                : kham pha day du + luu
  python nguon_kham_pha.py --xem          : chi in ket qua, khong luu
"""
import sys, time, json, pathlib, re, html
import requests
import concurrent.futures
import toc_do

LAB = pathlib.Path(__file__).parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}

# ------------------------------------------------------------------ keyword bank
# Tu khoa goc theo chu de (en) de phat sinh username + tim kiem.
TU_KHOA = {
    "en": ["forex signals", "forex trading", "trading strategy", "top trader",
           "quant trading", "price action", "crypto trading", "day trading",
           "swing trading", "gold signals", "stock signals", "prop firm",
           "backtest", "trading community", "warrior trading", "stock market"],
    "vi": ["tín hiệu forex", "giao dịch forex", "chiến lược trading", "trader chuyên nghiệp",
           "phân tích vàng", "cộng đồng trading", "tín hiệu crypto"],
    "ru": ["форекс сигналы", "трейдинг", "торговая стратегия", "сигналы биткоин"],
    "es": ["señales forex", "trading", "estrategia de trading", "señales crypto"],
    "pt": ["sinais forex", "trading", "estratégia de trading"],
    "zh": ["外汇信号", "交易策略", "加密货币信号"],
    "tr": ["forex sinyalleri", "trading", "kripto sinyalleri"],
    "ar": ["إشارات فوركس", "تداول", "استراتيجية"],
}

# Seed kenh cong khai (username) da biet / thu.
SEED_KENH = [
    "forexsignals", "tradingview", "fxstreetnews", "babypips", "dailyforex",
    "earnforex", "investingcom", "trading212", "octafx", "fxtm", "exness",
    "forexfactory", "metatrader", "icmarkets", "pepperstone", "thinkingtrader",
    "pipmailer", "silverbulletfx", "forextime", "tradersunion",
]


def _lam_sach_ten(s):
    return re.sub(r"[^A-Za-z0-9_]", "", s.lower())


def _bien_the_username(goc):
    """Tu 1 cum tu -> cac ung vien username kenh."""
    goc = _lam_sach_ten(goc)
    cac = {goc}
    for sep in ("", "_", "-"):
        w = sep.join(goc.split())
        if w != goc:
            cac.add(w)
    # them cac tien/hau to thong dung
    for c in list(cac):
        for suf in ("signals", "channel", "fx", "trading", "news", "group"):
            cac.add(c + suf)
    # gop bo tu thua
    for w in ("forex", "trading", "signals", "signal"):
        cac.add(w)
    return [c for c in cac if 3 <= len(c) <= 32]


# ------------------------------------------------------------------ doc kenh
def doc_kenh(username, so=8):
    """Doc kenh cong khai qua t.me/s/<username>. Tra (dict|None).
    dict: {username, title, url, posts:[{text, time, url}]}"""
    username = username.lstrip("@")
    toc_do.TOC_DO.cho("telegram")
    url = f"https://t.me/s/{username}"
    for lan in range(2):
        try:
            r = requests.get(url, headers=UA, timeout=45)
            if r.status_code == 429:
                toc_do.TOC_DO.doi_429("telegram")
                continue
            if r.status_code != 200:
                return None
            c = r.text
            m_t = re.search(r"<title>(.*?)</title>", c, re.S)
            title = html.unescape(m_t.group(1).strip()) if m_t else username
            m_title = re.search(r'tgme_page_title[^>]*>(.*?)</div>', c, re.S)
            if m_title:
                title = html.unescape(re.sub(r"<[^>]+>", "", m_title.group(1))).strip()
            # tach cac message
            posts = []
            for blk in re.split(r'tgme_widget_message ', c)[1:]:
                m_text = re.search(r'tgme_widget_message_text[^>]*>(.*?)</div>', blk, re.S)
                if not m_text:
                    continue
                text = html.unescape(re.sub(r"<[^>]+>", " ", m_text.group(1)))
                text = re.sub(r"\s+", " ", text).strip()
                if not text:
                    continue
                m_time = re.search(r'datetime="([^"]+)"', blk)
                m_id = re.search(r"t\.me/[^'\"]+/(\d+)", blk)
                pid = m_id.group(1).split("/")[-1] if m_id else ""
                posts.append({"text": text[:400], "time": m_time.group(1) if m_time else "",
                              "url": f"https://t.me/{username}/{pid}" if pid else url})
                if len(posts) >= so:
                    break
            if not posts:
                return None
            return {"username": username, "title": title[:120], "url": url,
                    "posts": posts}
        except requests.RequestException:
            time.sleep(1.5)
    return None


# ------------------------------------------------------------------ kham pha
def _probe_nhanh(username):
    """Doc kenh nhanh (khong qua bo dem toc do) de discovery. Tra dict|None."""
    username = username.lstrip("@")
    url = f"https://t.me/s/{username}"
    try:
        r = requests.get(url, headers=UA, timeout=8)
        if r.status_code != 200:
            return None
        c = r.text
        if "tgme_widget_message_text" not in c:
            return None
        m_t = re.search(r"<title>(.*?)</title>", c, re.S)
        title = html.unescape(m_t.group(1).strip()) if m_t else username
        m_title = re.search(r'tgme_page_title[^>]*>(.*?)</div>', c, re.S)
        if m_title:
            title = html.unescape(re.sub(r"<[^>]+>", "", m_title.group(1))).strip()
        return {"username": username, "title": title[:120], "url": url}
    except requests.RequestException:
        return None


def kham_pha_telegram(so_kenh=8, posts_moi_kenh=4, luong=8):
    """Kham pha co gioi han (nhanh): do seed + mot so ung vien tu keyword dau,
    doc kenh ton tai song song, tra ds bai dang. Gioi han de khong mat thoi gian."""
    # ung vien: seed + vui it keyword dau (khong lan cat hang tram)
    cac_ung_vien = list(SEED_KENH)
    for tk in TU_KHOA["en"][:6]:
        cac_ung_vien += _bien_the_username(tk)[:4]
    try:
        import keywords_nguon as kw
        for dm in ("cho_tin_hieu", "dang_doi", "quy", "cong_dong"):
            cac_ung_vien += kw.tao_ung_vien_username(dm, toi_da=8)
    except Exception:
        pass
    cac_ung_vien = [c for c in dict.fromkeys(cac_ung_vien) if len(c) <= 32]
    cac_ung_vien = cac_ung_vien[:70]
    # 1) probe song song
    tim_thay = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=luong) as ex:
        futs = {ex.submit(_probe_nhanh, u): u for u in cac_ung_vien}
        for fut in concurrent.futures.as_completed(futs):
            k = fut.result()
            if k:
                tim_thay.append(k)
                if len(tim_thay) >= so_kenh:
                    break
    # 2) doc bai trong cac kenh tim thay
    ds = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=luong) as ex:
        futs = [ex.submit(doc_kenh, k["username"], max(posts_moi_kenh, 1)) for k in tim_thay]
        for fut in concurrent.futures.as_completed(futs):
            k = fut.result()
            if not k:
                continue
            for post in k["posts"]:
                ds.append({"ten": k["title"], "url": post["url"], "kenh": k["username"],
                           "text": post["text"], "ngon_ngu": "", "tu_khoa": "telegram_channel",
                           "thoi_gian": post["time"]})
    return ds
def kham_pha_dan_mang(so=25):
    """Best-effort: tim lead tren X/TikTok/Facebook/Reddit qua search engine.
    Dung nguon tu keyboard bank (keywords_nguon). Neu mang khong truy cap duoc
    se bo qua (khong loi). Tra ds lead."""
    try:
        import keywords_nguon as kw
    except Exception:
        kw = None
    ds = []
    dang = [("reddit", "reddit_sub", lambda l: "reddit.com/r/" in l),
            ("x", "x_profile", lambda l: "x.com/" in l),
            ("tiktok", "tiktok_profile", lambda l: "tiktok.com/@" in l),
            ("facebook", "facebook_page", lambda l: "facebook.com" in l)]
    tu = []
    if kw:
        for dm in ("cho_tin_hieu", "dang_doi", "nguoi_thang", "cong_dong", "cho_phuong_phap"):
            tu += kw.DANH_MUC[dm]["tu_khoa"].get("en", [])[:3]
    else:
        tu = TU_KHOA["en"][:6]
    tu = list(dict.fromkeys(tu))
    for nn, kind, ktra in dang:
        for tk in tu[:8]:
            q = f"site:{'reddit.com' if nn=='reddit' else nn+'.com'} {tk} trader signals"
            for link in _search_engine(q):
                if not ktra(link):
                    continue
                ds.append({"ten": kind, "url": link.split("?")[0], "kenh": kind,
                           "text": "", "ngon_ngu": nn, "tu_khoa": tk,
                           "thoi_gian": ""})
                if len(ds) >= so:
                    return ds
    return ds


def _search_engine(q, toi_da=8):
    """Thu nhieu search engine, tra danh sach link (khong loi neu mang org)."""
    qq = q.replace(" ", "+")
    out = []
    for base in ("https://www.bing.com/search?q=", "https://html.duckduckgo.com/html/?q="):
        try:
            toc_do.TOC_DO.cho("search")
            r = requests.get(base + qq, headers=UA, timeout=25)
            c = r.text or ""
            for m in re.finditer(r'https?://[^\s"<>]+', c):
                link = m.group(0).rstrip(".,);")
                if "t.me" in link or "reddit.com/r/" in link or "x.com/" in link \
                   or "tiktok.com/@" in link or "facebook.com" in link:
                    out.append(link)
            if len(out) >= toi_da:
                break
        except requests.RequestException:
            continue
    return list(dict.fromkeys(out))[:toi_da]


# ------------------------------------------------------------------ luu
def luu(con, ds):
    """Ghi bai/lead vao muc + tao task scout. Tra so luong them moi."""
    import bo_nao
    them = 0
    for d in ds:
        mid = bo_nao.bam(d["url"])
        ten = d["ten"] or (d["text"] or d["url"])[:120]
        try:
            con.execute("INSERT OR IGNORE INTO muc(id,nguon,ten,url,ngay,da_xu) "
                        "VALUES(?,?,?,?,?,0)",
                        (mid, "kham_pha", ten, d["url"], time.time()))
            row = con.execute("SELECT da_xu FROM muc WHERE id=?", (mid,)).fetchone()
            if row and row[0] == 0:
                bo_nao.tao_task(con, "scout",
                                {"ten": ten, "url": d["url"],
                                 "van_ban": d.get("text", ""),
                                 "kenh": d.get("kenh", ""),
                                 "tu_khoa": d.get("tu_khoa", "")},
                                muc_id=mid, uu_tien=0, huong="seeker")
                them += 1
        except Exception:
            pass
    con.commit()
    return them


def main():
    import bo_nao
    only_xem = "--xem" in sys.argv
    print(">>> Kham pha Telegram (doc kenh cong khai, khong can bot)...")
    ds = kham_pha_telegram()
    print(f"Telegram: {len(ds)} bai tu kenh cong khai")
    for d in ds[:12]:
        print(f"  [{d['kenh']}] {d['ten'][:50]} :: {(d['text'] or '')[:60]}")
    print(">>> Kham pha mang xa hoi (best-effort)...")
    ds2 = kham_pha_dan_mang()
    print(f"Mang xa hoi: {len(ds2)} lead")
    for d in ds2[:12]:
        print(f"  [{d['ngon_ngu']}] {d['url'][:70]}")
    tat = ds + ds2
    if only_xem:
        print(f"\nTong: {len(tat)}. Chua luu (--xem).")
        return
    con = bo_nao.mo_db()
    n = luu(con, tat)
    print(f"\nLuu: tong {len(tat)}, them moi {n} vao muc + scout")


if __name__ == "__main__":
    main()
