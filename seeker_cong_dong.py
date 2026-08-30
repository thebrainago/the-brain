# -*- coding: utf-8 -*-
"""seeker_cong_dong.py - Tang cong dong cua SEEKNER: tim CO NHOM nguoi chia se,
ban luan, ban method/signal tren nhieu ngon ngu + quoc gia. Ghi vao bang cong_dong
va reports/NGUOI_GIOI.md. Khong tu dang nhap nhom kin (ToS) - phan do ban tao.
Chay:  python seeker_cong_dong.py  (quet 1 luot mau)
       python seeker_cong_dong.py --ngon-ngu ru,zh  (rieng ngon ngu)
       python seeker_cong_dong.py --them "url|loai|ten|ngon_ngu"  (them tay)
"""
import sys, time, re, json, pathlib
import toc_do

LAB = pathlib.Path(__file__).parent
ROOT = LAB.parent

# ------------------------------------------------------------- loai + tu khoa theo ngon ngu
LOAI = ("trader_huyen_thoai", "trader_dang_dai", "trader_top", "nguoi_thang_1pct",
        "nguoi_loi_nhuan", "quy_giao_dich", "dien_dan", "cho_tin_hieu",
        "cho_phuong_phap", "cong_dong_nghien_cuu")

# tu khoa goc (en) cho moi loai
TU_KHOA_EN = {
    "trader_huyen_thoai": ["legendary trader", "famous trader history", "greatest traders of all time"],
    "trader_dang_dai":    ["top trader 2025", "best forex trader 2025", "successful trader today"],
    "trader_top":         ["top 1% traders", "elite trader", "best stock trader"],
    "nguoi_thang_1pct":   ["trading competition winner", "trading championship champion", "top 1% account"],
    "nguoi_loi_nhuan":    ["profitable trader track record", "verified trading profit", "myfxbook top systems"],
    "quy_giao_dich":      ["hedge fund", "CTA fund", "quant trading fund", "managed futures fund"],
    "dien_dan":           ["trading forum", "forex forum discuss", "quant forum community"],
    "cho_tin_hieu":       ["signal marketplace", "copy trading platform", "forex signals community"],
    "cho_phuong_phap":    ["trading strategy marketplace", "EA marketplace", "trading system for sale"],
    "cong_dong_nghien_cuu": ["algorithmic trading community", "quant research group", "trading research community"],
}

# them tu khoa cho 1 so ngon ngu chinh (thieu thi dung en)
TU_KHOA_TA = {
    "ru": {"trader_huyen_thoai":["легендарный трейдер","известный трейдер"], "dien_dan":["форум трейдеров","форум форекс"],
           "trader_top":["лучший трейдер","топ трейдер"], "quy_giao_dich":["хедж-фонд","квант фонд"],
           "cong_dong_nghien_cuu":["сообщество алготрейдинга","квант сообщество"], "cho_tin_hieu":["сигналы форекс"]},
    "zh": {"trader_huyen_thoai":["传奇交易员","著名交易员"], "dien_dan":["外汇论坛","交易论坛"],
           "trader_top":["顶级交易员","最佳交易员"], "quy_giao_dich":["对冲基金","量化基金"],
           "cong_dong_nghien_cuu":["量化交易社区","算法交易社区"], "cho_tin_hieu":["信号交易","跟单交易"]},
    "es": {"trader_huyen_thoai":["trader legendario","trader famoso"], "dien_dan":["foro de trading","foro forex"],
           "trader_top":["mejor trader","top trader"], "cong_dong_nghien_cuu":["comunidad de trading cuantitativo"]},
    "pt": {"trader_huyen_thoai":["trader lendário"], "dien_dan":["fórum de trading","fórum forex"],
           "trader_top":["melhor trader"]},
    "ar": {"trader_huyen_thoai":["متداول أسطوري"], "dien_dan":["منتدى فوركس","منتدى التداول"],
           "trader_top":["أفضل متداول"]},
    "vi": {"trader_huyen_thoai":["huyền thoại trade","trader nổi tiếng"], "dien_dan":["diễn đàn forex","diễn đàn chứng khoán"],
           "trader_top":["trader giỏi nhất","top trader việt nam"], "cong_dong_nghien_cuu":["cộng đồng đầu tư định lượng"],
           "cho_tin_hieu":["bán tín hiệu forex","copy trade"]},
    "ja": {"trader_huyen_thoai":["伝説のトレーダー"], "dien_dan":["FX掲示板","トレードフォーラム"],
           "trader_top":["最高のトレーダー"]},
    "ko": {"trader_huyen_thoai":["전설의 트레이더"], "dien_dan":["외환 포럼","트레이딩 포럼"],
           "trader_top":["최고의 트레이더"]},
    "fr": {"trader_huyen_thoai":["trader légendaire"], "dien_dan":["forum forex","forum de trading"],
           "trader_top":["meilleur trader"]},
    "de": {"trader_huyen_thoai":["legendärer Trader"], "dien_dan":["Forex Forum","Trading Forum"],
           "trader_top":["bester Trader"]},
    "tr": {"trader_huyen_thoai":["efsanevi trader"], "dien_dan":["forex forum","trading forum"],
           "trader_top":["en iyi trader"]},
    "id": {"trader_huyen_thoai":["trader legendaris"], "dien_dan":["forum forex","forum trading"],
           "trader_top":["trader terbaik"]},
}

NGON_NGU = {"en": "en", "ru": "ru", "zh": "zh", "es": "es", "pt": "pt", "ar": "ar",
            "vi": "vi", "ja": "ja", "ko": "ko", "fr": "fr", "de": "de", "tr": "tr",
            "id": "id"}
QUOC_GIA = {"en":"US/UK/AU", "ru":"RU", "zh":"CN", "es":"ES/LA", "pt":"PT/BR", "ar":"AR",
            "vi":"VN", "ja":"JP", "ko":"KR", "fr":"FR", "de":"DE", "tr":"TR", "id":"ID"}


def _tu_khoa(loai, ngon):
    """Tra tu khoa theo loai + ngon ngu (fallback en)."""
    if ngon != "en":
        ta = TU_KHOA_TA.get(ngon, {})
        if loai in ta:
            return ta[loai]
    return TU_KHOA_EN.get(loai, [])


def _ve_loai_ngon(msg):
    """Doan loai web tu url/ten (loai truy cap)."""
    u = (msg or "").lower()
    if "t.me/" in u or "telegram" in u: return "telegram"
    if "youtube" in u or "youtu.be" in u: return "youtube"
    if "facebook" in u or "fb.com" in u: return "facebook"
    if "discord" in u: return "discord"
    if "vkontakte" in u or "vk.com" in u: return "vk"
    if "reddit" in u: return "reddit"
    return "web"


def _sach(ds):
    """Them https + bo trung url."""
    seen, out = set(), []
    for ten, u in ds:
        if u.startswith("//"): u = "https:" + u
        if u in seen: continue
        seen.add(u); out.append((ten, u))
    return out


def _lay_ket_qua(q, ngon):
    """Tim qua Bing roi DuckDuckGo (both qua toc_do). Tra danh sach (ten,url)."""
    out = []
    # Bing
    r = toc_do.lay("https://www.bing.com/search",
                   nguon="web",
                   params={"q": q, "setlang": ngon, "cc": QUOC_GIA.get(ngon, "")},
                   headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=20)
    if r is not None:
        for m in re.finditer(r'<h2><a href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.S):
            t = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if t:
                out.append((t[:90], m.group(1)))
        if len(out) >= 5:
            return out[:8]
    # DuckDuckGo html
    r = toc_do.lay("https://html.duckduckgo.com/html/", nguon="web",
                   params={"q": q, "kl": "", "l": ngon},
                   headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=20)
    if r is not None:
        for m in re.finditer(r'class="result__a" href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.S):
            t = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            u = m.group(1)
            if "uddg=" in u:
                u = urllib.parse.unquote(u.split("uddg=", 1)[1].split("&")[0])
            elif u.startswith("//"):
                u = "https:" + u
            if t:
                out.append((t[:90], u))
    return _sach(out)[:8]


def mo_db():
    import sqlite3
    lab = str(LAB)
    if lab not in sys.path:
        sys.path.insert(0, lab)
    import bo_nao
    return bo_nao.mo_db()


def luu(con, ds):
    dem = 0
    for d in ds:
        try:
            con.execute("""INSERT INTO cong_dong(loai,ten,url,ngon_ngu,quoc_gia,truy_cap,ghi_chu,mau_khoa,luc)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                        (d.get("loai"), d.get("ten"), d.get("url"), d.get("ngon_ngu"),
                         d.get("quoc_gia"), d.get("truy_cap"), d.get("ghi_chu"),
                         d.get("mau_khoa"), time.time()))
            con.commit(); dem += 1
        except Exception:
            pass
    return dem


def quet(ngon_list=None, loai_list=None):
    ngon_list = ngon_list or list(NGON_NGU)
    loai_list = loai_list or list(LOAI)
    ds = []
    for ngon in ngon_list:
        for loai in loai_list:
            for kw in _tu_khoa(loai, ngon):
                try:
                    kq = _lay_ket_qua(f"{kw}", ngon)
                except Exception:
                    continue
                for ten, url in kq:
                    ds.append({"loai": loai, "ten": ten, "url": url,
                               "ngon_ngu": ngon, "quoc_gia": QUOC_GIA.get(ngon, ""),
                               "truy_cap": _ve_loai_ngon(url), "ghi_chu": "",
                               "mau_khoa": kw})
    # bo trung url
    seen, out = set(), []
    for d in ds:
        if d["url"] in seen: continue
        seen.add(d["url"]); out.append(d)
    return out


def ghi_md(con):
    md = ["# NGUOI_GIOI + CONG DONG (tu dong tong hop)\n",
          "> Cap nhat boi seeker_cong_dong.py. Phan nhom kin (facebook/telegram rieng) do ban duyet.\n"]
    for loai in LOAI:
        md.append(f"\n## {loai}\n")
        rows = con.execute("SELECT ten,url,ngon_ngu,truy_cap FROM cong_dong WHERE loai=? LIMIT 40", (loai,)).fetchall()
        for ten, url, nn, tc in rows:
            md.append(f"- [{ten}]({url})  _({nn} · {tc})_")
    out = LAB / "reports" / "NGUOI_GIOI.md"
    out.write_text("\n".join(md), encoding="utf-8")
    return out


def them_tay(s):
    """Them 1 dong tu tay dinh dang: url|loai|ten|ngon_ngu"""
    parts = s.split("|")
    url = parts[0].strip()
    loai = parts[1].strip() if len(parts) > 1 else "trader_top"
    ten = parts[2].strip() if len(parts) > 2 else url
    nn = parts[3].strip() if len(parts) > 3 else "en"
    con = mo_db()
    n = luu(con, [{"loai": loai, "ten": ten, "url": url, "ngon_ngu": nn,
                   "quoc_gia": QUOC_GIA.get(nn, ""), "truy_cap": _ve_loai_ngon(url),
                   "ghi_chu": "tay", "mau_khoa": "tay"}])
    print(f"Da them {n} vao cong_dong")
    ghi_md(con)


if __name__ == "__main__":
    args = sys.argv[1:]
    ngn = None; loai = None
    if "--ngon-ngu" in args:
        ngn = args[args.index("--ngon-ngu") + 1].split(",")
    if "--them" in args:
        them_tay(args[args.index("--them") + 1]); sys.exit(0)
    print("Quet cong dong ...")
    ds = quet(ngn)
    con = mo_db()
    n = luu(con, ds)
    md = ghi_md(con)
    print(f"Them {n} cong dong -> {md}")
    if n:
        for d in ds[:15]:
            print(f"  [{d['loai']}] ({d['ngon_ngu']}·{d['truy_cap']}) {d['ten'][:60]}")
