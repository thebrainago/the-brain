# -*- coding: utf-8 -*-
"""nguon_bai_viet.py - NGUON VAN XUOI: bai viet chien luoc, lay qua RSS/Atom.

VI SAO CAN MODULE NAY (do that tren so cai 23/08/2026):
  `noi_dung` co 326 ban doc: 167 ban `khong_doc_duoc` (0 ky tu), 121 ban
  `ma_nguon` (repo GitHub do nguyen si), 38 ban `khac`. **Khong mot ban nao la
  mot bai viet mo ta chien luoc bang chu.** Kho nguon cu huong hoan toan vao
  metadata hoc thuat (openalex/crossref/arxiv - phan lon la tieu de + tom tat,
  ban day du la PDF nen truot) va ma nguon (github). Bo doc van xuoi
  (`nhan/doc_hieu.py`) vi the khong co gi de doc.

VI SAO LA RSS CHU KHONG PHAI CRAWL:
  Do that 23/08 tren 20 trang: `quantpedia.com/strategies` tra 362 KB "text" ma
  toan bo la CSS cua mot ung dung Next.js; `quantocracy.com` khong co mot link
  bai nao trong HTML tho; `quantifiedstrategies.com` tra 1.980 byte tuong
  altcha. Cung nhung trang do, **feed RSS tra ve san ca bai**: financial-hacker
  10 bai/74 KB, quantinsti 15 bai/1,6 MB, priceactionlab 20 bai/212 KB.
  Feed la giao dien on dinh, re, va co `content:encoded` = **toan van**, nen
  khong can lan doc thu hai va khong sinh them ban `khong_doc_duoc`.

RANH GIOI:
  Module nay CHI thu thap va luu. No khong doc hieu, khong de xuat co che,
  khong xep viec backtest. Do la viec cua `nhan/doc_hieu.py` va QUANTLAB.
"""
from __future__ import annotations

import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

#: Feed da DO THAT ngay 23/08/2026 (so muc / so byte trong ngoac).
#: `hang`: A = co ket qua kiem chung duoc; B = co phuong phap; C = thao luan.
#: `toan_van`: feed co `content:encoded` day du -> khong can lan doc thu hai.
FEEDS: dict[str, dict] = {
    "fh_financial_hacker": {
        "url": "https://financial-hacker.com/feed/", "hang": "A",
        "toan_van": True, "loai": "blog",
        "ghi_chu": "10 muc / 74 KB - bai co luat + code Zorro, mat do luat cao nhat"},
    "quantinsti": {
        "url": "https://blog.quantinsti.com/rss/", "hang": "B",
        "toan_van": True, "loai": "blog",
        "ghi_chu": "15 muc / 1,6 MB - bai day, nhieu bai co luat va tham so"},
    "priceactionlab": {
        "url": "https://www.priceactionlab.com/Blog/feed/", "hang": "B",
        "toan_van": True, "loai": "blog", "ghi_chu": "20 muc / 212 KB"},
    "alphaarchitect": {
        "url": "https://alphaarchitect.com/feed/", "hang": "A",
        "toan_van": True, "loai": "blog",
        "ghi_chu": "trang /blog/ tra 403 nhung FEED tra 200 - 5 muc / 93 KB"},
    "allocatesmartly": {
        "url": "https://allocatesmartly.com/feed/", "hang": "A",
        "toan_van": True, "loai": "blog",
        "ghi_chu": "10 muc / 123 KB - chuyen ta luat phan bo tai san"},
    "qoppac": {
        "url": "https://qoppac.blogspot.com/feeds/posts/default", "hang": "A",
        "toan_van": True, "loai": "blog", "ghi_chu": "25 muc / 846 KB (Rob Carver)"},
    "mrzepczynski": {
        "url": "https://mrzepczynski.blogspot.com/feeds/posts/default", "hang": "C",
        "toan_van": True, "loai": "blog", "ghi_chu": "25 muc / 147 KB"},
    "tr8dr": {
        "url": "https://tr8dr.github.io/feed.xml", "hang": "B",
        "toan_van": True, "loai": "blog", "ghi_chu": "10 muc / 124 KB"},
    "thinknewfound": {
        "url": "https://blog.thinknewfound.com/feed/", "hang": "B",
        "toan_van": False, "loai": "blog", "ghi_chu": "10 muc / 18 KB - tom tat"},
    "robotwealth": {
        "url": "https://robotwealth.com/feed/", "hang": "B",
        "toan_van": False, "loai": "blog", "ghi_chu": "12 muc / 20 KB - tom tat"},
    "quantpedia_blog": {
        "url": "https://quantpedia.com/feed/", "hang": "A",
        "toan_van": False, "loai": "blog",
        "ghi_chu": "10 muc / 15 KB - tom tat; trang /strategies/ la SPA khong doc duoc"},
    "followingthetrend": {
        "url": "https://www.followingthetrend.com/feed/", "hang": "B",
        "toan_van": False, "loai": "blog", "ghi_chu": "10 muc / 13 KB"},
    "tradingmarkets": {
        "url": "https://tradingmarkets.com/feed/", "hang": "C",
        "toan_van": False, "loai": "blog", "ghi_chu": "12 muc / 15 KB"},
    "mql5_articles": {
        "url": "https://www.mql5.com/en/articles/rss", "hang": "B",
        "toan_van": False, "loai": "bai_bao",
        "ghi_chu": "10 muc - BAI VIET (khac Code Base o nhan/ma_nguon.py)"},
    "reddit_algotrading": {
        "url": "https://www.reddit.com/r/algotrading/.rss", "hang": "C",
        "toan_van": True, "loai": "dien_dan",
        "ghi_chu": "25 muc - duong .rss VAO DUOC du www.reddit.com tra 403"},
    "reddit_quant": {
        "url": "https://www.reddit.com/r/quant/.rss", "hang": "C",
        "toan_van": True, "loai": "dien_dan",
        "ghi_chu": "duong .rss; reddit tra 429 khi goi hai sub lien tiep - "
                   "de chu ky lech nhau, dung goi cung luot"},
    # --- dot hai, do that cung ngay ---
    "quantitativo": {
        "url": "https://quantitativo.substack.com/feed", "hang": "A",
        "toan_van": True, "loai": "blog",
        "ghi_chu": "20 muc / 1,46 MB - blog dang luat ro rang nhat trong ca hai dot"},
    "hangukquant": {
        "url": "https://hangukquant.substack.com/feed", "hang": "B",
        "toan_van": True, "loai": "blog", "ghi_chu": "20 muc / 359 KB"},
    "quantdare": {
        "url": "https://quantdare.com/feed/", "hang": "B",
        "toan_van": True, "loai": "blog", "ghi_chu": "12 muc / 147 KB"},
    "tradingview_blog": {
        "url": "https://www.tradingview.com/feed/", "hang": "C",
        "toan_van": True, "loai": "blog", "ghi_chu": "30 muc / 170 KB"},
    "reddit_algotrading_nam": {
        "url": "https://www.reddit.com/r/algotrading/top/.rss?t=year", "hang": "C",
        "toan_van": True, "loai": "dien_dan",
        "ghi_chu": "25 bai TOP nam - chat luong cao hon feed moi nhat"},
    "headlandstech": {
        "url": "https://blog.headlandstech.com/feed/", "hang": "B",
        "toan_van": True, "loai": "blog", "ghi_chu": "5 muc / 105 KB"},
    "quantumtrading": {
        "url": "https://www.quantumtrading.com/feed/", "hang": "C",
        "toan_van": True, "loai": "blog", "ghi_chu": "10 muc / 130 KB"},
    "alvarezquant": {
        "url": "https://alvarezquanttrading.com/feed/", "hang": "A",
        "toan_van": False, "loai": "blog",
        "ghi_chu": "10 muc tom tat - Cesar Alvarez, luat rat ro, phai doc them trang"},
    "buildalpha": {
        "url": "https://www.buildalpha.com/feed/", "hang": "B",
        "toan_van": False, "loai": "blog", "ghi_chu": "10 muc tom tat"},
    "gestaltu": {
        "url": "https://gestaltu.com/feed", "hang": "B",
        "toan_van": False, "loai": "blog", "ghi_chu": "10 muc tom tat"},
    "newtraderu": {
        "url": "https://www.newtraderu.com/feed/", "hang": "C",
        "toan_van": False, "loai": "blog", "ghi_chu": "10 muc tom tat"},
}

#: Feed DA THU VA HONG - giu lai lam mon no ro rang thay vi im lang bo qua.
FEED_HONG = {
    "quantstart": "rss.xml 404; trang /articles/ doc duoc bang HTML tho",
    "cssanalytics": "403 - chan theo user-agent; thu lai bang UA_BOT chua lam",
    "marketsci": "feed rong (114 byte)",
    "quantstrattrader": "feed 304 KB nhung 0 muc - WordPress tra trang HTML",
    "quantconnect_blog": "252 KB nhung 0 muc - tra trang HTML thay vi RSS",
    "pyquantnews": "404 tai /feed", "tradeciety": "404 tai /feed",
    "osquant": "404 tai /feed.xml", "wisesheets": "404 tai /blog/rss.xml",
    "tradingtuitions": "404 tai /feed", "elearnmarkets": "feed rong (762 byte)",
    "systematicindividualinvestor": "403 - chan bot", "macrosynergy": "403 - chan bot",
    "raposa": "ConnectionError - ten mien khong phan giai",
    "quantitativo_com": "ConnectionError - dung ban substack thay the",
}

#: UA TU KHAI BAO cho cac trang chan trinh duyet. KHONG gia danh Googlebot:
#: do that 23/08 cho thay tuong altcha cua quantifiedstrategies chi bat UA
#: TRINH DUYET, con mot UA bot tu khai bao trung thuc thi duoc phuc vu day du
#: (256 KB thay vi 1.980 byte). Va `robots.txt` cua ho la
#: `User-agent: * / Disallow:` - tuc cho phep tat ca.
UA_BOT = "Mozilla/5.0 (compatible; TheBrainResearchBot/1.0)"

#: NGUON DANG DUYET TRANG (khong co feed dung duoc). Bo sung cho FEEDS, khong
#: thay the: feed re hon nhieu, chi duyet trang khi khong con cach khac.
#:
#: Vi sao dang bo cong: mat do LUAT moi la rang buoc, khong phai so bai. 259
#: bai blog qua feed chi cho 3 co che; MOT trang cua quantifiedstrategies cho
#: 2 - vi ho viet luat bang so ("Buy = RSI(30)>50 AND RSI(2)<15").
TRANG: dict[str, dict] = {
    "quantifiedstrategies": {
        "seed": ["https://www.quantifiedstrategies.com/rsi-trading-strategy/",
                 "https://www.quantifiedstrategies.com/trading-strategies/",
                 "https://www.quantifiedstrategies.com/rsi2-on-spy/"],
        "mau_link": r"^https://www\.quantifiedstrategies\.com/[a-z0-9\-]+/$",
        "loai_tru": r"/(?:category|tag|page|feed|author|platinumsubscription"
                    r"|about|contact|privacy|terms|disclaimer|shop|cart)/",
        "ua": UA_BOT, "hang": "A", "loai": "blog", "cham_giay": 2.0,
        "bat": False,
        "ghi_chu": "TAT tu 23/08. Ban dau UA bot tu khai bao doc duoc day du "
                   "(256 KB) va robots.txt la `Disallow:` rong, nhung sau MOT "
                   "bai thi ho chuyen sang 403 cho moi request ke ca cham 6 "
                   "giay - tuc ho tu choi chung ta o muc IP. KHONG di tim "
                   "duong lach: ho da noi khong. Muon doc tiep thi hoac qua "
                   "CDP voi trinh duyet that cua nguoi dung, hoac mua goi cua "
                   "ho. Da giu lai 1 bai lay duoc luc con duoc phuc vu."},
}

#: Bai ngan hon nguong nay thi doc them trang goc. Duoi 1.500 ky tu thuong chi
#: la doan mo dau, khong du de co mot cau luat day du.
NGUONG_DOC_THEM = 1500
#: Tran ky tu moi bai. Bai dai nhat trong lan do that la 120 KB.
TRAN_KY_TU = 200_000


def tat_ca_feed() -> dict[str, dict]:
    """FEED khai bao tay + FEED do `nhan/vuon_nguon.py` TU TIM duoc.

    Khai bao tay la nhung nguon da doc bang mat va biet ro; nguon tu tim vao
    dien THU (tham do) va tu chet neu sau `HAN_THAM_DO_BAI` bai van khong sinh
    duoc ung vien nao. Hai ho gop o day de moi cho khac trong he chi phai biet
    MOT danh sach.
    """
    ra = dict(FEEDS)
    try:
        from nhan import vuon_nguon as VN
        for ma, c in VN.feed_dang_bat().items():
            if ma not in ra:
                ra[ma] = c
    except Exception:
        pass
    return ra


def _lay(url: str, timeout: int = 25, ua: str | None = None) -> str | None:
    try:
        import requests
        r = requests.get(url, timeout=timeout, headers={"User-Agent": ua or UA})
        if r.status_code == 200 and r.text:
            return r.text
    except Exception:
        return None
    return None


def _the(el, *ten) -> str:
    """Lay text cua the dau tien khop, bo qua namespace."""
    for t in ten:
        for con in el.iter():
            if con.tag.rsplit("}", 1)[-1].lower() == t.lower():
                if con.text and con.text.strip():
                    return con.text
                # Atom: <content type="html"> co the chua node con
                noi = "".join(con.itertext()).strip()
                if noi:
                    return noi
    return ""


def _link(el) -> str:
    for con in el.iter():
        ten = con.tag.rsplit("}", 1)[-1].lower()
        if ten == "link":
            if con.text and con.text.strip().startswith("http"):
                return con.text.strip()
            href = con.attrib.get("href", "")
            if href.startswith("http") and con.attrib.get("rel", "alternate") == "alternate":
                return href
    return ""


def doc_feed(xml_text: str) -> list[dict]:
    """RSS 2.0 hoac Atom -> [{tieu_de, url, van_ban, nguon_van_ban}].

    Uu tien `content:encoded` (RSS) va `content` (Atom) - do la TOAN VAN.
    `description`/`summary` chi la tom tat, danh dau lai de biet co can doc
    them trang goc khong.
    """
    try:
        goc = ET.fromstring(xml_text.encode("utf-8", "replace"))
    except ET.ParseError:
        return []
    muc = [e for e in goc.iter()
           if e.tag.rsplit("}", 1)[-1].lower() in ("item", "entry")]
    ra = []
    for e in muc:
        tt = _the(e, "title")
        if not tt:
            continue
        day_du = _the(e, "encoded", "content")
        tom_tat = _the(e, "description", "summary", "subtitle")
        vb = day_du or tom_tat
        ra.append({
            "tieu_de": re.sub(r"\s+", " ", tt).strip()[:400],
            "url": _link(e),
            "van_ban": vb or "",
            "day_du": bool(day_du) and len(day_du) > len(tom_tat or ""),
        })
    return ra


def _bo_the(vb: str) -> str:
    from nhan import doc_hieu as DH
    return DH._chuan(vb)


def thu_thap(ma: str, so_bai: int = 12, doc_them: int = 4,
             ngan_sach_giay: int = 120) -> dict:
    """Mot feed -> ghi `tai_lieu` + `noi_dung` (kieu 'bai_bao').

    Ghi THANG ca toan van, khong qua tang DOC: feed da co san noi dung, va
    tang DOC la cho 167 ban `khong_doc_duoc` duoc sinh ra.
    """
    c = tat_ca_feed().get(ma)
    if not c:
        return {"loi": f"khong co feed '{ma}'"}
    t0 = time.time()
    xml_text = _lay(c["url"])
    if not xml_text:
        return {"nguon": ma, "loi": "khong lay duoc feed"}
    muc = doc_feed(xml_text)[:so_bai]
    bao = {"nguon": ma, "lay_ve": len(muc), "tai_lieu_moi": 0, "ban_doc_moi": 0,
           "doc_them": 0, "ky_tu": 0, "bo_qua_ngan": 0}
    da_doc_them = 0
    for m in muc:
        url = m["url"] or ""
        vb = _bo_the(m["van_ban"])
        if len(vb) < NGUONG_DOC_THEM and url and da_doc_them < doc_them \
                and time.time() - t0 < ngan_sach_giay:
            trang = _lay(url)
            da_doc_them += 1
            bao["doc_them"] += 1
            if trang:
                day = _bo_the(trang)
                if len(day) > len(vb):
                    vb = day
        if len(vb) < 400:
            bao["bo_qua_ngan"] += 1
            continue
        vb = vb[:TRAN_KY_TU]
        vt = SO.van_tay(url or m["tieu_de"])
        with SO.ket_noi() as cn:
            cur = cn.execute(
                "INSERT OR IGNORE INTO tai_lieu(van_tay,nguon,loai,tieu_de,url,"
                "tom_tat,tu_khoa,diem,luc) VALUES(?,?,?,?,?,?,?,?,?)",
                (vt, ma, c.get("loai", "blog"), m["tieu_de"], url,
                 vb[:2000], c.get("hang", "C"),
                 {"A": 3.0, "B": 2.0}.get(c.get("hang", "C"), 1.0), SO.bay_gio()))
            bao["tai_lieu_moi"] += cur.rowcount
            row = cn.execute("SELECT id FROM tai_lieu WHERE van_tay=?", (vt,)).fetchone()
            if not row:
                continue
            cur2 = cn.execute(
                "INSERT OR IGNORE INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,"
                "so_ky_tu,so_ky_tu_goc,van_ban,luc,da_boc) "
                "VALUES(?,?,?,'bai_bao',?,?,?,?,?,0)",
                (row[0], SO.van_tay("nd", url or m["tieu_de"]), url,
                 "rss" if m["day_du"] else "rss+trang",
                 len(vb), len(m["van_ban"] or ""), vb, SO.bay_gio()))
            if cur2.rowcount:
                bao["ban_doc_moi"] += 1
                bao["ky_tu"] += len(vb)
    return bao


BIEN_GIOI = Path(__file__).resolve().parent.parent / "reports" / "bien_gioi_trang.json"


def _doc_bien_gioi() -> dict:
    import json
    try:
        return json.loads(BIEN_GIOI.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _luu_bien_gioi(d: dict) -> None:
    import json
    BIEN_GIOI.parent.mkdir(parents=True, exist_ok=True)
    # Giu bien gioi trong tam kiem soat: mot trang tin tuc co the sinh hang van
    # link va bien gioi phinh ra thanh mot con crawler khong ai dinh viet.
    for ma in d:
        d[ma]["cho"] = list(dict.fromkeys(d[ma].get("cho", [])))[:400]
        d[ma]["da"] = list(dict.fromkeys(d[ma].get("da", [])))[-2000:]
    BIEN_GIOI.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def thu_thap_trang(ma: str, so_trang: int = 6, ngan_sach_giay: int = 120) -> dict:
    """Duyet trang cho nguon khong co feed. BFS co bien gioi luu tren dia.

    KHONG phai mot con crawler tong quat: chi di trong mot ten mien, chi theo
    `mau_link` da khai bao, co tran moi luot va co cham nhip. Mot trang co
    hang nghin bai thi nhieu luot moi het - do la co y, khong phai gioi han
    ky thuat.
    """
    c = TRANG.get(ma)
    if not c:
        return {"loi": f"khong co nguon trang '{ma}'"}
    t0 = time.time()
    bg = _doc_bien_gioi()
    tt = bg.setdefault(ma, {"cho": list(c["seed"]), "da": []})
    if not tt["cho"]:
        tt["cho"] = [u for u in c["seed"] if u not in tt["da"]] or list(c["seed"])
    khop = re.compile(c["mau_link"], re.I)
    tru = re.compile(c["loai_tru"], re.I) if c.get("loai_tru") else None
    bao = {"nguon": ma, "doc": 0, "tai_lieu_moi": 0, "ban_doc_moi": 0,
           "ky_tu": 0, "link_moi": 0, "bo_qua": 0}

    while tt["cho"] and bao["doc"] < so_trang and time.time() - t0 < ngan_sach_giay:
        url = tt["cho"].pop(0)
        if url in tt["da"]:
            continue
        tt["da"].append(url)
        html = _lay(url, ua=c.get("ua", UA))
        bao["doc"] += 1
        time.sleep(float(c.get("cham_giay", 1.5)))
        if not html:
            continue
        for u in dict.fromkeys(re.findall(r'href="(https?://[^"#?]+/)"', html)):
            if khop.match(u) and not (tru and tru.search(u)) \
                    and u not in tt["da"] and u not in tt["cho"]:
                tt["cho"].append(u)
                bao["link_moi"] += 1
        vb = _bo_the(html)
        if len(vb) < 800:
            bao["bo_qua"] += 1
            continue
        tieu_de = ""
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        if m:
            tieu_de = re.sub(r"\s+", " ", _bo_the(m.group(1))).strip()[:400]
        vb = vb[:TRAN_KY_TU]
        vt = SO.van_tay(url)
        with SO.ket_noi() as cn:
            cur = cn.execute(
                "INSERT OR IGNORE INTO tai_lieu(van_tay,nguon,loai,tieu_de,url,"
                "tom_tat,tu_khoa,diem,luc) VALUES(?,?,?,?,?,?,?,?,?)",
                (vt, ma, c.get("loai", "blog"), tieu_de or url[-80:], url,
                 vb[:2000], c.get("hang", "C"),
                 {"A": 3.0, "B": 2.0}.get(c.get("hang", "C"), 1.0), SO.bay_gio()))
            bao["tai_lieu_moi"] += cur.rowcount
            row = cn.execute("SELECT id FROM tai_lieu WHERE van_tay=?", (vt,)).fetchone()
            if not row:
                continue
            cur2 = cn.execute(
                "INSERT OR IGNORE INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,"
                "so_ky_tu,so_ky_tu_goc,van_ban,luc,da_boc) "
                "VALUES(?,?,?,'bai_bao','duyet_trang',?,?,?,?,0)",
                (row[0], SO.van_tay("nd", url), url, len(vb), len(html), vb,
                 SO.bay_gio()))
            if cur2.rowcount:
                bao["ban_doc_moi"] += 1
                bao["ky_tu"] += len(vb)
    bao["con_cho"] = len(tt["cho"])
    _luu_bien_gioi(bg)
    return bao


def thu_thap_tat_ca(gioi_han_nguon: int = 5, so_bai: int = 12,
                    ngan_sach_giay: int = 240) -> dict:
    """Quet cac feed den han, xoay vong theo `nguon.lan_cuoi`."""
    t0 = time.time()
    tong = {"da_quet": [], "tai_lieu_moi": 0, "ban_doc_moi": 0, "ky_tu": 0,
            "loi": []}
    xep = []
    kho_feed = tat_ca_feed()
    for ma, c in kho_feed.items():
        r = SO.mot("SELECT lan_cuoi, trang_thai, chu_ky_giay FROM nguon WHERE ma=?",
                   "rss_" + ma)
        if r and (r["trang_thai"] or "BAT") != "BAT":
            continue
        lan_cuoi = (r["lan_cuoi"] if r else 0) or 0
        chu_ky = (r["chu_ky_giay"] if r else 0) or 21600
        if time.time() - lan_cuoi < chu_ky:
            continue
        xep.append((lan_cuoi, ma))
    for _, ma in sorted(xep)[:gioi_han_nguon]:
        if time.time() - t0 > ngan_sach_giay:
            break
        try:
            b = thu_thap(ma, so_bai=so_bai,
                         ngan_sach_giay=max(30, int(ngan_sach_giay / 3)))
        except Exception as e:
            b = {"nguon": ma, "loi": f"{type(e).__name__}: {str(e)[:100]}"}
        if b.get("loi"):
            tong["loi"].append({ma: b["loi"]})
            SO.chay("INSERT INTO nguon(ma,ten,loai,url,chu_ky_giay,lan_cuoi,so_lan,"
                    "so_loi,loi_lien_tuc,ghi_chu) VALUES(?,?,?,?,?,?,1,1,1,?) "
                    "ON CONFLICT(ma) DO UPDATE SET lan_cuoi=excluded.lan_cuoi, "
                    "so_loi=so_loi+1, loi_lien_tuc=loi_lien_tuc+1, "
                    "ghi_chu=excluded.ghi_chu",
                    "rss_" + ma, f"RSS {ma}", kho_feed[ma].get("loai", "blog"),
                    kho_feed[ma]["url"], 21600, time.time(), str(b["loi"])[:100])
            continue
        tong["da_quet"].append(ma)
        for k in ("tai_lieu_moi", "ban_doc_moi", "ky_tu"):
            tong[k] += b.get(k, 0)
        SO.chay("INSERT INTO nguon(ma,ten,loai,url,chu_ky_giay,lan_cuoi,so_lan,"
                "thu_hoach,trang_thai) VALUES(?,?,?,?,?,?,1,?,'BAT') "
                "ON CONFLICT(ma) DO UPDATE SET lan_cuoi=excluded.lan_cuoi, "
                "so_lan=so_lan+1, loi_lien_tuc=0, "
                "thu_hoach=thu_hoach+excluded.thu_hoach",
                "rss_" + ma, f"RSS {ma}", kho_feed[ma].get("loai", "blog"),
                kho_feed[ma]["url"], 21600, time.time(), b.get("ban_doc_moi", 0))
    # PHA HAI: nguon khong co feed. Chay sau feed vi feed re hon nhieu.
    tong["trang"] = {}
    for ma, ct in TRANG.items():
        if time.time() - t0 > ngan_sach_giay:
            break
        if not ct.get("bat", True):
            continue
        r = SO.mot("SELECT lan_cuoi, trang_thai, chu_ky_giay FROM nguon WHERE ma=?",
                   "trang_" + ma)
        if r and (r["trang_thai"] or "BAT") != "BAT":
            continue
        if time.time() - ((r["lan_cuoi"] if r else 0) or 0) <                 ((r["chu_ky_giay"] if r else 0) or 21600):
            continue
        try:
            b = thu_thap_trang(ma, so_trang=6,
                               ngan_sach_giay=max(40, int(ngan_sach_giay / 3)))
        except Exception as e:
            b = {"loi": f"{type(e).__name__}: {str(e)[:100]}"}
        tong["trang"][ma] = b
        tong["ban_doc_moi"] += b.get("ban_doc_moi", 0)
        tong["ky_tu"] += b.get("ky_tu", 0)
        SO.chay("INSERT INTO nguon(ma,ten,loai,url,chu_ky_giay,lan_cuoi,so_lan,"
                "thu_hoach,trang_thai) VALUES(?,?,?,?,?,?,1,?,'BAT') "
                "ON CONFLICT(ma) DO UPDATE SET lan_cuoi=excluded.lan_cuoi, "
                "so_lan=so_lan+1, thu_hoach=thu_hoach+excluded.thu_hoach",
                "trang_" + ma, f"duyet trang {ma}", TRANG[ma].get("loai", "blog"),
                TRANG[ma]["seed"][0], 21600, time.time(), b.get("ban_doc_moi", 0))

    SO.ghi_chi_so("nguon_bai_viet_ban_doc_moi", tong["ban_doc_moi"], tong)
    return tong


if __name__ == "__main__":
    import json
    SO.khoi_tao()
    print(json.dumps(thu_thap_tat_ca(gioi_han_nguon=16, so_bai=15,
                                     ngan_sach_giay=600),
                     ensure_ascii=False, indent=1))
