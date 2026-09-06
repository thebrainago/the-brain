# -*- coding: utf-8 -*-
"""seeker.py - TRU SEEKER. Phong thu thap thong tin va kien thuc 24/7.

Khac ban cu (`seeker_quy_tac.py` chay 8.719 lan/5,3 gio, moi lan 0,2 giay, doc
lai mot file tinh - tuc 8.718 lan la vong lap rong):

  1. MOI NGUON CO CHU KY RIENG, luu trong bang `nguon`. Het chu ky moi goi.
     Khong con vong lap 2 giay.
  2. NGUON TU TAT khi loi lien tuc, tu bat lai sau thoi gian cach ly.
  3. TU MO RONG TU KHOA: rut cum tu tu tai lieu diem cao, cham diem tu khoa
     theo NANG SUAT (so ket qua / so lan dung) - tu khoa te tu chet.
  4. PHAN HANG TIN HIEU: A = co ket qua that kiem chung duoc; B = cong trinh
     co phuong phap; C = thao luan/y tuong.
  5. DAU RA V2 LA ARTIFACT BAT BIEN: SEEKER chi thu thap, chuan hoa va truy
     nguyen. NGHI/QUANTLAB moi duoc suy luan co che va quyet dinh kiem dinh.

Thiet ke de dung cho LINH VUC KHAC: `nguon` va `tu_khoa` deu co cot `linh_vuc`.
Doi linh vuc = doi bo nguon + bo tu khoa goc, khong phai viet lai tru.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nhan import (du_lieu as DL, hop_dong as HD, mau as MAU, ngu_phap as NP,
                  san_cong_cu as SCC, so as SO, thu_hoi_thanh_phan as THTP,
                  toan_van as TV, tri_tue as TT)

TRU = "SEEKER"
REPORTS = Path(__file__).resolve().parent.parent / "reports"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

#: SO TU KHOA MOI NGUON MOI LUOT. Truoc 03/09/2026 con so nay viet CUNG trong
#: than tung ham (`tu_khoa[:3]`, `tu_khoa[:2]`), nen khong ai chinh duoc va
#: khong ai thay no dang chan.
#:
#: Do duoc 03/09: bang `tu_khoa` co 126 tu, moi nguon chi hoi 2-3 tu moi luot
#: -> can ~50 luot moi di het MOT VONG. Rieng TradingView: tu truoc den nay moi
#: hoi **15 tu khoa**, va mot lan noi tran cho ngay 120 bai moi.
#:
#: Muc mac dinh giu nguyen hanh vi cu (phanh chi phi + ton trong quota API).
#: `muc_tieu.san*` noi tran cho RIENG luot chien dich cua no.
SO_TU_KHOA_MOI_NGUON = {
    "arxiv": 3, "github": 3, "openalex": 3, "stackexchange": 2,
    "hackernews": 2, "crossref": 2, "semantic": 2, "mql5_code": 3,
}


def _so_tu_khoa(nguon: str, mac_dinh: int = 3) -> int:
    return int(SO_TU_KHOA_MOI_NGUON.get(nguon, mac_dinh))


TU_KHOA_GOC = [
    "trading strategy backtest", "momentum factor", "mean reversion equity",
    "statistical arbitrage", "market microstructure", "volatility risk premium",
    "trend following managed futures", "pairs trading cointegration",
    "intraday seasonality", "order flow imbalance", "expert advisor mql5",
    "algorithmic trading python", "portfolio optimization robust",
    "overfitting backtest deflated sharpe", "regime switching model",
]


#: Ma tra ve cua lan lay cuoi, cho nguoi goi PHAN BIET duoc ba truong hop.
#: Truoc 03/09/2026 `_lay` tra `None` cho ca ba, va `n_mql5_code` dich `None`
#: thanh "qua trang cuoi" -> mot lan chan tam thoi cat VINH VIEN con tro bien
#: gioi. Do that: con tro ghi `trang_cuoi = 3` cho gan het danh muc trong khi
#: MQL5 Code Base co hang chuc trang, va tu do nguon lang le bao "het trang".
LAN_LAY_CUOI: dict = {}

#: Header cua mot trinh duyet THAT. Chu du an 03/09/2026: *"mo phong thao tac
#: tay nguoi dung chu dung lam nhu bot"*. Do that tren mql5.com: chi gui
#: `User-Agent` thi 403; gui du bo nay thi **200**.
_DAU_TRANG_DUYET = {
    "User-Agent": UA,
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "image/avif,image/webp,*/*;q=0.8"),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Connection": "keep-alive",
}


def _lay(url: str, timeout: int = 25) -> str | None:
    """Tra van ban khi 200, `None` khi khong. Ghi CHI TIET vao `LAN_LAY_CUOI`.

    Nguoi goi nao can phan biet "404 = het trang" voi "khong noi duoc mang"
    thi doc `LAN_LAY_CUOI` ngay sau khi goi. Khong doi chu ky ham vi co ~20
    cho goi no va phan lon khong quan tam.
    """
    LAN_LAY_CUOI.clear()
    # Ten mien bi DNS DAU DOC tren mang nay -> phan giai sang IP that. Giu
    # nguyen ten trong URL nen SNI va chung chi TLS van dung. Xem
    # `nhan/dns_vuot.py` (chan doan day du o docstring cua no).
    try:
        from nhan import dns_vuot as _DV
        _can_vuot = any(t in url for t in _DV.BAN_DO)
    except Exception:
        _DV, _can_vuot = None, False
    if _can_vuot:
        _DV.bat()
    try:
        import requests
        r = requests.get(url, timeout=timeout, headers=_DAU_TRANG_DUYET)
        LAN_LAY_CUOI.update({"url": url, "ma": r.status_code, "loi": None})
        if r.status_code == 200:
            return r.text
    except Exception as e:
        LAN_LAY_CUOI.update({"url": url, "ma": None,
                             "loi": f"{type(e).__name__}: {str(e)[:100]}"})
        return None
    return None


def lay_that_bai_vi_mang() -> bool:
    """Lan `_lay` vua roi hong vi MANG/CHAN, khong phai vi trang khong ton tai."""
    d = LAN_LAY_CUOI
    return bool(d.get("loi")) or (d.get("ma") not in (None, 200) and
                                  int(d.get("ma") or 0) >= 500)


def _sach(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


# --------------------------------------------------- CON TRO BIEN GIOI
# Vi sao co: do that 01/09 cho thay `n_mql5_code` goi DUNG HAI URL (trang 1 cua
# experts va indicators) roi cat con 30 link, nen ca kho MQL5 Code Base chi thu
# ve **35 tai lieu**. Tu luot thu hai tro di no doc lai dung trang do -> khong
# co gi moi -> he tu ket luan "chu ky nguon qua day". Chan doan do la SAI: van
# de la DO SAU QUET, khong phai tan suat.
#
# Do that cung ngay (requests, khong doan): `/en/code/<mt5|mt4>/<danh muc>/pageN`
# tra 200 va 40 link/trang, trang qua cuoi tra 404, va cac trang KHONG trung
# nhau (giao p1&p2 = 0, p2&p3 = 0). Trang cuoi do bang tim nhi phan:
#   mt5/indicators 146 · mt5/experts 42 · mt4/indicators 65 · mt4/experts 31
#   · mt5/libraries 11 · mt5/scripts 10   ->  ~12.200 muc, so voi 35 da lay.
#
# Con tro nay ghi DA QUET TOI TRANG NAO cho tung danh muc, luu trong cot
# `nguon.lay_gi` (JSON). `dang_ky_nguon` khong ghi de cot do khi ON CONFLICT nen
# con tro song qua moi lan khoi dong. Moi luot di TIEP tu cho da dung, het bien
# thi quay ve trang 1 (bat muc moi dang len dau) va tang `vong`.
def _con_tro(ma: str) -> dict:
    r = SO.mot("SELECT lay_gi FROM nguon WHERE ma=?", ma)
    try:
        d = json.loads((r["lay_gi"] if r else "") or "{}")
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _ghi_con_tro(ma: str, d: dict) -> None:
    SO.chay("UPDATE nguon SET lay_gi=? WHERE ma=?",
            json.dumps(d, ensure_ascii=False)[:4000], ma)


# ------------------------------------------------------------------- NGUON
def n_arxiv(tu_khoa: list[str]) -> list[dict]:
    """arXiv q-fin. HANG B: cong trinh co phuong phap viet ra."""
    ra = []
    truy_van = ["cat:q-fin.ST", "cat:q-fin.PM", "cat:q-fin.TR", "cat:q-fin.CP"]
    truy_van += [f'all:"{t}"' for t in tu_khoa[:_so_tu_khoa("arxiv")]]
    for q in truy_van[:5]:
        u = ("http://export.arxiv.org/api/query?search_query=" + q.replace(" ", "+") +
             "&start=0&max_results=25&sortBy=submittedDate&sortOrder=descending")
        txt = _lay(u)
        if not txt:
            continue
        for kh in re.findall(r"<entry>(.*?)</entry>", txt, re.S):
            m_tt = re.search(r"<title>(.*?)</title>", kh, re.S)
            tm = re.search(r"<summary>(.*?)</summary>", kh, re.S)
            lk = re.search(r"<id>(.*?)</id>", kh, re.S)
            tt = _sach(m_tt.group(1)) if m_tt else ""
            if not tt:
                continue
            ra.append({"tieu_de": tt[:250], "url": (lk.group(1) if lk else "").strip(),
                       "tom_tat": _sach(tm.group(1))[:900] if tm else "",
                       "hang": "B", "loai": "hoc_thuat"})
        time.sleep(1.2)
    return ra


#: Ngon ngu cua ma CHIEN LUOC, khong chi Python. Truoc 03/09/2026 truy van
#: ghim cung `language:python` va bo het repo Pine/MQL/C++.
GH_NGON_NGU = ["python", "pine", "mql5", "mql4", "cpp"]

#: Cach xep. `sort=stars` mot minh la ly do suat github chi 1,2%: MOI tu khoa
#: deu tra ve cung mot nhom framework noi tieng (finmarketpy, OctoBot,
#: backtesting.py) chu khong ra chien luoc. Do la THU VIEN, khong phai LUAT.
#: Xen ke `updated` va best-match de cham duoc DUOI DAI - noi nguoi ta dang
#: chien luoc le.
GH_CACH_XEP = [("", ""), ("updated", "desc"), ("stars", "desc")]


def n_github(tu_khoa: list[str]) -> list[dict]:
    """GitHub. HANG A khi repo co CODE CHAY DUOC - ta backtest lai duoc ngay.

    Ban 03/09/2026 doi ba dieu, deu do suat 1,2% chi ra:
      - khong ghim `language:python` nua, xoay vong qua 5 ngon ngu
      - khong chi `sort=stars` nua, xen ke `updated`/best-match de vao duoi dai
      - `per_page` 20 -> 100
    """
    ra = []
    ct = _con_tro("github")
    xoay = int(ct.get("xoay", 0))
    for i, t in enumerate(tu_khoa[:_so_tu_khoa("github")]):
        nn = GH_NGON_NGU[(xoay + i) % len(GH_NGON_NGU)]
        xep, thu_tu = GH_CACH_XEP[(xoay + i) % len(GH_CACH_XEP)]
        u = ("https://api.github.com/search/repositories?q=" +
             t.replace(" ", "+") + f"+language:{nn}&per_page=100")
        if xep:
            u += f"&sort={xep}&order={thu_tu}"
        txt = _lay(u)
        if not txt:
            time.sleep(2)
            continue
        try:
            for it in json.loads(txt).get("items", []):
                sao = it.get("stargazers_count", 0)
                ra.append({
                    "tieu_de": f"[{sao}*] {it.get('full_name')}",
                    "url": it.get("html_url", ""),
                    "tom_tat": (it.get("description") or "")[:500],
                    "hang": "A" if sao >= 300 else "B", "loai": "ma_nguon",
                    "diem_them": min(sao / 1000.0, 2.0)})
        except Exception:
            pass
        time.sleep(2)
    ct["xoay"] = xoay + max(1, len(tu_khoa[:_so_tu_khoa("github")]))
    _ghi_con_tro("github", ct)
    return ra


def n_openalex(tu_khoa: list[str]) -> list[dict]:
    """OpenAlex - kho cong trinh mo, khong can khoa. Thay cho SSRN (bi SSL chan)."""
    ra = []
    for t in tu_khoa[:_so_tu_khoa("openalex")]:
        u = ("https://api.openalex.org/works?search=" + t.replace(" ", "%20") +
             "&per-page=25&sort=cited_by_count:desc")
        txt = _lay(u)
        if not txt:
            continue
        try:
            for it in json.loads(txt).get("results", []):
                tr = it.get("cited_by_count") or 0
                tt = it.get("title") or ""
                # OpenAlex tra tom tat duoi dang chi muc dao nguoc
                idx = it.get("abstract_inverted_index") or {}
                tom = " ".join(list(idx)[:80]) if idx else ""
                ra.append({"tieu_de": tt[:250],
                           "url": it.get("doi") or it.get("id") or "",
                           "tom_tat": tom[:900],
                           "hang": "B" if tr >= 20 else "C", "loai": "hoc_thuat",
                           "diem_them": min(tr / 200.0, 1.5)})
        except Exception:
            pass
        time.sleep(1.5)
    return ra


def n_stackexchange(tu_khoa: list[str]) -> list[dict]:
    """Quant StackExchange. HANG C nhung chat luong cau hoi cao, tot de mo tu khoa."""
    ra = []
    for t in tu_khoa[:_so_tu_khoa("stackexchange")]:
        u = ("https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=votes"
             "&q=" + t.replace(" ", "%20") + "&site=quant&pagesize=20&filter=withbody")
        txt = _lay(u)
        if not txt:
            continue
        try:
            for it in json.loads(txt).get("items", []):
                ra.append({"tieu_de": _sach(it.get("title", ""))[:250],
                           "url": it.get("link", ""),
                           "tom_tat": _sach(it.get("body", ""))[:600],
                           "hang": "C", "loai": "cong_dong",
                           "diem_them": min(it.get("score", 0) / 20.0, 1.0)})
        except Exception:
            pass
        time.sleep(2)
    return ra


def n_hackernews(tu_khoa: list[str]) -> list[dict]:
    ra = []
    for t in tu_khoa[:_so_tu_khoa("hackernews")]:
        u = ("https://hn.algolia.com/api/v1/search?query=" + t.replace(" ", "%20") +
             "&tags=story&hitsPerPage=20")
        txt = _lay(u)
        if not txt:
            continue
        try:
            for it in json.loads(txt).get("hits", []):
                ra.append({"tieu_de": _sach(it.get("title") or "")[:250],
                           "url": it.get("url") or f"https://news.ycombinator.com/item?id={it.get('objectID')}",
                           "tom_tat": _sach(it.get("story_text") or "")[:400],
                           "hang": "C", "loai": "cong_dong",
                           "diem_them": min((it.get("points") or 0) / 200.0, 1.0)})
        except Exception:
            pass
        time.sleep(2)
    return ra


# ==========================================================================
# NGUON MOI 16/08 - deu da DO THAT tu may nay truoc khi viet (khong doan).
# Ket qua do: QuantConnect forum 200 / Forex Factory 200 / MQL5 code 200 /
# TradingView scripts 200 / Lean Algorithm.Python 200 / NBER 200 / Zenodo 200 /
# Crossref 200 / DOAJ 200 / Alpha Architect + Robot Wealth + Quantpedia RSS 200.
# Van chan: Reddit (403 ca api lan redlib), SSRN (SSL), Elite Trader (SSL),
# CORE (timeout), OSF (400), GitHub code search (401 - can khoa).
# ==========================================================================

def _rss(url: str, nguon: str, hang: str = "B") -> list[dict]:
    """Boc mot nguon RSS/Atom thanh danh sach tai lieu.

    Blog nghien cuu la nguon TOT hon dien dan cho muc dich cua ta: bai co co che
    ro rang, thuong kem so lieu va giai doan kiem dinh, va tac gia chiu trach
    nhiem ten tuoi. Doi lai chung it hon va cham hon.
    """
    txt = _lay(url, timeout=30)
    if not txt:
        return []
    ra = []
    for kh in re.findall(r"<(?:item|entry)\b[^>]*>(.*?)</(?:item|entry)>", txt, re.S | re.I):
        tt = re.search(r"<title[^>]*>(.*?)</title>", kh, re.S | re.I)
        lk = re.search(r"<link[^>]*href=[\"']([^\"']+)", kh, re.I) or \
            re.search(r"<link[^>]*>(.*?)</link>", kh, re.S | re.I)
        mt = re.search(r"<(?:description|summary|content:encoded)[^>]*>(.*?)"
                       r"</(?:description|summary|content:encoded)>", kh, re.S | re.I)
        tieu_de = _sach(tt.group(1)) if tt else ""
        if not tieu_de:
            continue
        ra.append({"tieu_de": tieu_de[:250],
                   "url": (lk.group(1).strip() if lk else ""),
                   "tom_tat": _sach(mt.group(1))[:900] if mt else "",
                   "hang": hang, "loai": "blog_nghien_cuu"})
    return ra


def n_blog_nghien_cuu(tu_khoa: list[str]) -> list[dict]:
    """Blog dinh luong co ky ten. HANG B - co phuong phap, doi khi co ca ma."""
    ra = []
    for u in ("https://alphaarchitect.com/feed/",
              "https://robotwealth.com/feed/",
              "https://quantpedia.com/feed/"):
        ra += _rss(u, "blog", "B")
        time.sleep(1.0)
    return ra


def n_quantconnect(tu_khoa: list[str]) -> list[dict]:
    """Dien dan QuantConnect. Nguoi o day dan CODE CHAY DUOC (Lean) kem thao luan.

    **DO 22/08: nguon nay tra ve 0 va se TIEP TUC tra ve 0 qua HTTP.** Trang la
    SPA - moi duong dan (`.json`, `.rss`, `/services/...`) deu tra ve CUNG mot
    vo HTML 250 KB, va trong vo do chi co 2 link "Permalink" toi mot bai duy
    nhat. Danh sach that duoc dung bang JS sau khi tai.

    Giu ham lai (khong xoa) vi hai le: no van bat duoc bai le neu QC doi cach
    render, va xoa di thi lan sau lai co nguoi viet lai tu dau. Nhung **dung
    trong doi no co du lieu** - muon lay QC thi phai di qua CDP
    (`NGUON_CAN_TRINH_DUYET`), khong phai qua `requests`.
    """
    txt = _lay("https://www.quantconnect.com/forum/discussions/1/latest", timeout=30)
    if not txt:
        return []
    ra, da = [], set()
    # ... va o day la LOI NGUOC LAI cua `n_mql5_code`: ban truoc doi href TUONG
    # DOI nhung QuantConnect xuat href TUYET DOI
    # (`https://www.quantconnect.com/forum/discussion/15237/...`). Cung mot loi,
    # hai chieu, ca hai deu tra ve rong trong im lang.
    for m in re.finditer(
            r'href="(?:https://www\.quantconnect\.com)?(/forum/discussion/[^"#?]+)"[^>]*>(.*?)</a>',
            txt, re.S | re.I):
        u, tt = m.group(1), _sach(m.group(2))
        if len(tt) < 15 or u in da:
            continue
        da.add(u)
        ra.append({"tieu_de": tt[:250], "url": "https://www.quantconnect.com" + u,
                   "tom_tat": "", "hang": "B", "loai": "dien_dan"})
    return ra[:25]


def n_lean_algo(tu_khoa: list[str]) -> list[dict]:
    """Thu vien thuat toan mau cua Lean (QuantConnect) - MA CHAY DUOC, hang A.

    511.157 ky tu ma chien luoc that trong mot thu muc. Day dung la thu memory
    `quet-rong-tham-khao-nguoi-khac` doi: "code ngoai lam nguon logic".
    """
    txt = _lay("https://api.github.com/repos/QuantConnect/Lean/contents/Algorithm.Python",
               timeout=30)
    if not txt:
        return []
    ra = []
    try:
        for it in json.loads(txt):
            ten = it.get("name") or ""
            if not ten.endswith(".py") or (it.get("size") or 0) < 800:
                continue
            ra.append({"tieu_de": f"[Lean] {ten[:-3]}",
                       "url": it.get("html_url") or "",
                       "tom_tat": f"Thuat toan mau Lean, {it.get('size')} byte",
                       "hang": "A", "loai": "ma_nguon",
                       "_raw": it.get("download_url")})
    except Exception:
        return []
    return ra[:40]


# Sau danh muc THAT cua MQL5 Code Base (do 01/09 bang tim nhi phan tren so
# trang): mt5/indicators 146 trang · mt5/experts 42 · mt4/indicators 65 ·
# mt4/experts 31 · mt5/libraries 11 · mt5/scripts 10. Xep EA truoc chi bao vi
# `bien_dich_ung_vien.loai_ma_nguon` chi nhan cai MO VI THE MOI.
MQL5_DANH_MUC = ["mt5/experts", "mt4/experts", "mt5/indicators",
                 "mt4/indicators", "mt5/scripts", "mt5/libraries"]
MQL5_SO_TRANG_MOI_LUOT = 3


def n_mql5_code(tu_khoa: list[str]) -> list[dict]:
    """Kho ma MQL5 - EA/chi bao that dang chay tren MT5. CO PHAN TRANG.

    Ghi chu cu bao "mql5 render bang JS" la noi ve trang SIGNALS. Trang
    /en/code tra HTML tho co link (do that 16/08: 200, 20.942 ky tu van ban).

    Ban 01/09: khong con doc trang 1 roi thoi. Moi luot lay `SO_TRANG_MOI_LUOT`
    trang KE TIEP theo con tro bien gioi (xem `_con_tro`), xoay vong qua 6 danh
    muc de khong danh het ngan sach cho mot cai. Ngan sach ~90 giay/luot nen de
    3 trang: 3 x (1 GET + 1,5s nghi) ~ 8 giay.
    """
    ra, da = [], set()
    ct = _con_tro("mql5_code")
    trang = ct.setdefault("trang", {})          # danh muc -> trang KE TIEP se lay
    cuoi = ct.setdefault("trang_cuoi", {})      # danh muc -> trang cuoi da biet
    vong = ct.setdefault("vong", 0)
    # xoay vong danh muc: bat dau tu cai sau cai lan truoc, de moi danh muc deu
    # duoc di sau chu khong chi cai dau bang.
    bd = ct.get("danh_muc_ke", 0) % len(MQL5_DANH_MUC)
    thu_tu = MQL5_DANH_MUC[bd:] + MQL5_DANH_MUC[:bd]

    # HAI VIEC MOI LUOT, va viec thu hai la chu du an chi ra (01/09):
    #   - DI SAU: lay tiep trang ke tiep theo con tro bien gioi.
    #   - QUAY VE TRANG 1: muc MOI luon xuat hien o dau danh sach, nen di sau mai
    #     ma khong soi lai dau thi khong bao gio thay cai vua dang. Con tro chi
    #     tien la mot bo thu thap KHONG BAO GIO cap nhat.
    # Nen mot suat moi luot danh cho trang 1 (xoay vong danh muc), phan con lai
    # danh cho bien gioi. Soi lai trang 1 gan nhu mien phi: `luu_tai_lieu` khu
    # trung theo van tay nen chi cai THAT SU moi mo di tiep.
    lich = []
    muc_dau = thu_tu[0]
    lich.append((muc_dau, 1))                       # soi lai dau danh sach
    for muc in thu_tu:
        if len(lich) >= MQL5_SO_TRANG_MOI_LUOT:
            break
        n0 = int(trang.get(muc, 1))
        if (muc, n0) not in lich:
            lich.append((muc, n0))
    ct["lan_soi_dau"] = int(ct.get("lan_soi_dau", 0)) + 1
    da_lay = 0
    for muc, n in lich:
        u = f"https://www.mql5.com/en/code/{muc}" + ("" if n == 1 else f"/page{n}")
        soi_dau = (n == 1 and int(trang.get(muc, 1)) != 1)
        txt = _lay(u, timeout=30)
        da_lay += 1
        if not txt:
            # PHAN BIET hai truong hop, va do la ban va 03/09/2026:
            #   - hong vi MANG/CHAN -> KHONG dung dat gi vao con tro. Mot lan
            #     mql5.com bi loc SNI tung ghi `trang_cuoi = 3` cho gan het
            #     danh muc, va tu do nguon lang le bao "het trang" MAI MAI.
            #   - 404 that -> moi la qua trang cuoi.
            if lay_that_bai_vi_mang():
                ct["lan_hong_mang"] = int(ct.get("lan_hong_mang", 0)) + 1
                ct["hong_mang_cuoi"] = LAN_LAY_CUOI.get("loi") or LAN_LAY_CUOI.get("ma")
                time.sleep(1.5)
                continue
            if n > 1:
                cuoi[muc] = n - 1
                trang[muc] = 1
                ct["vong"] = vong + 1
            time.sleep(1.5)
            continue
        # HREF TUONG DOI. Ban truoc doi `href="https://www.mql5.com/en/code/123"`
        # nhung trang that dung `href="/en/code/76331"`, nen regex khop 0/40 va
        # ham tra ve rong SUOT - khong loi, khong canh bao. Doi chieu 22/08:
        # trang 82.894 ky tu, 40 link tuong doi, 0 link tuyet doi.
        n_link = 0
        for m in re.finditer(
                r'href="(?:https://www\.mql5\.com)?(/en/code/\d+)"[^>]*>(.*?)</a>',
                txt, re.S | re.I):
            u2, tt = "https://www.mql5.com" + m.group(1), _sach(m.group(2))
            if len(tt) < 10 or u2 in da:
                continue
            da.add(u2)
            n_link += 1
            ra.append({"tieu_de": f"[MQL5 {muc}] {tt[:200]}", "url": u2,
                       "tom_tat": "", "hang": "B", "loai": "ma_nguon"})
        # trang 200 nhung khong co link nao = da het thuc su (MQL5 tra 200 cho
        # trang rong o vai danh muc) -> xu ly nhu 404.
        # Luot SOI DAU khong duoc dong vao con tro bien gioi: no la mot chuyen
        # di rieng ve dau danh sach, khong phai buoc tien cua mui khoan.
        if not soi_dau:
            trang[muc] = (n + 1) if n_link else 1
        if not n_link and n > 1 and not soi_dau:
            cuoi[muc] = n - 1
            ct["vong"] = vong + 1
        time.sleep(1.5)
    ct["danh_muc_ke"] = (bd + da_lay) % len(MQL5_DANH_MUC)
    ct["da_quet_trang"] = int(ct.get("da_quet_trang", 0)) + da_lay
    _ghi_con_tro("mql5_code", ct)
    return ra


# TradingView: DUNG O SEARCH, KHONG DUYET TRANG DANH MUC (chu du an chot 01/09).
#
# Do that 01/09 tren ba duong:
#  - `/scripts/?script_type=strategies&page=N`: `page` KHONG phan trang, moi
#    trang tra dung 21 link giong het nhau (danh sach cuon bang JS).
#  - trang `/script/<slug>/`: 575 KB HTML nhung **khong co mot dong Pine nao**
#    (`//@version` dem duoc 0 lan) - ma do trinh duyet dung JS.
#  - `/scripts/?q=<tu khoa>`: 403.
# Nen ca ba duong "bam vao tung script roi lay code" deu khong di duoc bang
# `requests`, va di bang CDP thi ton mot lan mo trinh duyet cho MOI script.
#
# Duong that: `pubscripts-suggest-json/?search=<tu khoa>` - dung cai o search
# cua TradingView goi ra - tra JSON 50 ket qua moi truy van, va **ban ghi co san
# truong `scriptSource` chua NGUYEN MA PINE**. Do that: 12-20/50 ban ghi co ma
# (so con lai la script dong nguon), ma dai trung binh 1.200-3.700 ky tu, kem
# `type`, `access`, `author`, `agreeCount`. Sau truy van dau tien cho 271 script
# rieng biet.
#
# Tuc mot request thay cho mot lan bam + mot lan tai. Va vi ma da nam trong tay,
# ham nay ghi THANG vao `noi_dung` - khong de tang doc phai keo lai lan nua.
TV_PINE_URL = "https://www.tradingview.com/pubscripts-suggest-json/?search={k}"
TV_SO_TRUY_VAN_MOI_LUOT = 3


def _ghi_ban_doc(url: str, van_ban: str, kieu: str = "ma_nguon") -> None:
    """Ghi thang mot ban doc da co san vao `noi_dung` (khong tai lai)."""
    r = SO.mot("SELECT id FROM tai_lieu WHERE url=?", url)
    if not r:
        return
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT OR IGNORE INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,"
            "so_ky_tu,so_ky_tu_goc,van_ban,luc) VALUES(?,?,?,?,'suggest-json',?,?,?,?)",
            (r["id"], SO.van_tay("nd", url), url, kieu,
             len(van_ban), len(van_ban), van_ban, SO.bay_gio()))


def n_tradingview_pine(tu_khoa: list[str]) -> list[dict]:
    """Pine Script cong khai tu o search TradingView. Hang A: ma CHAY DUOC."""
    ct = _con_tro("tradingview_pine")
    da_hoi = ct.setdefault("da_hoi", [])
    # xoay vong bo tu khoa: tu khoa nao lau chua hoi nhat di truoc.
    kho = [t for t in (tu_khoa or []) if t] or ["strategy", "indicator"]
    chua = [t for t in kho if t not in da_hoi]
    # MOT SUAT MOI LUOT DANH CHO TU KHOA CU (chu du an chi ra 01/09). Ket qua tim
    # duoc xep theo do moi, nen script vua dang nam o dau danh sach cua chinh
    # nhung tu khoa DA hoi. Chi hoi tu khoa chua hoi la mot bo thu thap khong bao
    # gio cap nhat: voi 92 tu khoa va 3 truy van moi luot, mot tu khoa phai cho
    # 31 luot moi den luot lai.
    cu_nhat = [t for t in da_hoi if t in kho]
    lich = ([cu_nhat[0]] if cu_nhat else []) + (chua or kho)
    ra = []
    for k in lich[:TV_SO_TRUY_VAN_MOI_LUOT]:
        import urllib.parse as _ur
        txt = _lay(TV_PINE_URL.format(k=_ur.quote(k)), timeout=30)
        da_hoi.append(k)
        if not txt:
            time.sleep(1.0)
            continue
        try:
            ds = (json.loads(txt) or {}).get("results") or []
        except Exception:
            time.sleep(1.0)
            continue
        for x in ds:
            ma = (x.get("scriptSource") or "").strip()
            slug = x.get("scriptIdPart") or ""
            ten = _sach(x.get("scriptName") or x.get("title") or "")
            if not ten or not slug:
                continue
            u = f"https://www.tradingview.com/script/{slug}/"
            # KHONG bo ban ghi khong co ma. Script dong nguon van la mot muc luc
            # co that (ten + tac gia + so nguoi thich); no chi khong doc duoc.
            # Bo im lang thi sau nay khong ai biet da gap no.
            # `type` PHAN BIET STRATEGY VOI INDICATOR, va do la thong tin quan
            # trong nhat trong ban ghi. Do doi chieu voi ma that tren 5 truy van:
            # type=2 la strategy voi do chinh xac **100% (17/17)**, type=1 la
            # indicator (25/25). Truoc khi dung no, kho thu ve 155 indicator so
            # voi 20 strategy - va chi strategy moi co `strategy.entry` de bo doc
            # lan ra dieu kien vao lenh. Tuc 88% cong thu thap do vao thu khong
            # rut duoc chien luoc.
            #
            # Khong VUT indicator: mot chi bao van cho toan hang dung duoc (xem
            # `thu_hoi_thanh_phan`). Chi ha hang de hang doi doc uu tien strategy.
            la_chien_luoc = str(x.get("type")) == "2"
            ra.append({
                "tieu_de": f"[Pine{'/CL' if la_chien_luoc else ''}] {ten[:176]}",
                "url": u,
                "tom_tat": (f"{'chien_luoc' if la_chien_luoc else 'chi_bao'} · "
                            f"{x.get('author') or ''} · "
                            f"{x.get('agreeCount') or 0} thich · "
                            f"{'CO ma Pine' if ma else 'dong nguon'}")[:400],
                "hang": ("A" if la_chien_luoc else "B") if ma else "C",
                "loai": "ma_nguon",
                "_pine": ma,
                "_chien_luoc": la_chien_luoc,
            })
        time.sleep(1.0)
    # Xoay vong: tu khoa vua hoi lai di ve CUOI hang doi, de lan sau den luot cai khac.
    ct["da_hoi"] = [t for t in da_hoi if t != (cu_nhat[0] if cu_nhat else None)]
    if cu_nhat:
        ct["da_hoi"].append(cu_nhat[0])
    ct["da_hoi"] = ct["da_hoi"][-120:]
    ct["truy_van_da_hoi"] = int(ct.get("truy_van_da_hoi", 0)) + len(chua[:TV_SO_TRUY_VAN_MOI_LUOT])
    _ghi_con_tro("tradingview_pine", ct)
    return ra


def n_crossref(tu_khoa: list[str]) -> list[dict]:
    """Crossref - muc luc cong trinh co DOI. Dung de bat bai KHONG co tren arXiv."""
    ra = []
    for t in tu_khoa[:_so_tu_khoa("crossref")]:
        txt = _lay("https://api.crossref.org/works?rows=20&sort=score&query=" +
                   t.replace(" ", "+"), timeout=30)
        if not txt:
            continue
        try:
            for it in json.loads(txt).get("message", {}).get("items", []):
                tt = (it.get("title") or [""])[0]
                if not tt:
                    continue
                tr = it.get("is-referenced-by-count") or 0
                ra.append({"tieu_de": tt[:250],
                           "url": it.get("URL") or "",
                           "tom_tat": _sach(it.get("abstract") or "")[:900],
                           "hang": "B" if tr >= 20 else "C", "loai": "hoc_thuat",
                           "diem_them": min(tr / 200.0, 1.5)})
        except Exception:
            pass
        time.sleep(1.5)
    return ra


def n_semantic_scholar(tu_khoa: list[str]) -> list[dict]:
    ra = []
    for t in tu_khoa[:_so_tu_khoa("semantic")]:
        u = ("https://api.semanticscholar.org/graph/v1/paper/search?query=" +
             t.replace(" ", "+") + "&limit=20&fields=title,abstract,year,citationCount,url")
        txt = _lay(u)
        if not txt:
            continue
        try:
            for it in json.loads(txt).get("data", []):
                tr = it.get("citationCount") or 0
                ra.append({"tieu_de": (it.get("title") or "")[:250],
                           "url": it.get("url") or "",
                           "tom_tat": (it.get("abstract") or "")[:900],
                           "hang": "B" if tr >= 20 else "C", "loai": "hoc_thuat",
                           "diem_them": min(tr / 200.0, 1.5)})
        except Exception:
            pass
        time.sleep(3)
    return ra


NGUON = {
    # Hai nguon HOC THUAT xuong uu_tien 3 ngay 30/08/2026 — do that, khong
    # phai cam giac. Suat ra artifact tren moi tai lieu: github 140/179
    # (78%), mql5 71/~102 (70%), youtube 18/62 (29%), **openalex 17/281
    # (6%), arxiv 1/133 (0,8%)**. Ve co che thi ca hai cho DUNG 0 tren
    # 414 ban. Bai hoc thuat ta PHUONG PHAP, khong ta LUAT.
    # KHONG tat — chi di sau, vi ngan sach quet chi 90 giay/luot nen thu
    # tu quyet dinh ai duoc quet that.
    "arxiv":         {"ham": n_arxiv, "chu_ky": 21600, "uu_tien": 3, "loai": "hoc_thuat"},
    "github":        {"ham": n_github, "chu_ky": 43200, "uu_tien": 1, "loai": "ma_nguon"},
    "openalex":      {"ham": n_openalex, "chu_ky": 43200, "uu_tien": 3, "loai": "hoc_thuat"},
    "stackexchange": {"ham": n_stackexchange, "chu_ky": 43200, "uu_tien": 3, "loai": "cong_dong"},
    "hackernews":    {"ham": n_hackernews, "chu_ky": 43200, "uu_tien": 3, "loai": "cong_dong"},
    # Semantic Scholar tra 429 khi khong co khoa -> chu ky dai, backoff tu dong lo not.
    "semantic":      {"ham": n_semantic_scholar, "chu_ky": 172800, "uu_tien": 4,
                      "loai": "hoc_thuat"},
    # --- them 16/08 ---
    "lean_algo":     {"ham": n_lean_algo, "chu_ky": 86400, "uu_tien": 1, "loai": "ma_nguon"},
    "mql5_code":     {"ham": n_mql5_code, "chu_ky": 43200, "uu_tien": 2, "loai": "ma_nguon"},
    "blog":          {"ham": n_blog_nghien_cuu, "chu_ky": 43200, "uu_tien": 2, "loai": "blog"},
    "quantconnect":  {"ham": n_quantconnect, "chu_ky": 43200, "uu_tien": 3, "loai": "dien_dan"},
    "crossref":      {"ham": n_crossref, "chu_ky": 86400, "uu_tien": 3, "loai": "hoc_thuat"},
    # --- them 01/09: Pine Script kem MA, khong can CDP ---
    "tradingview_pine": {"ham": n_tradingview_pine, "chu_ky": 21600, "uu_tien": 1,
                         "loai": "ma_nguon"},
}

# Nguon DA KIEM THAT ngay 15/08 va KHONG vao duoc bang `requests`.
# Deu la nguon co gia tri cao, nen chung nam day nhu mot mon no ro rang chu
# khong bi im lang bo qua. EVO se bao lai moi ngay cho toi khi noi duoc.
NGUON_CAN_TRINH_DUYET = {
    "mql5_signals": "trang render bang JS - HTML tho khong co link signal nao",
    "reddit": "403 voi ca www.reddit.com lan old.reddit.com",
    "myfxbook": "SSLError khi bat tay",
    "ssrn": "SSLError khi bat tay",
    "cftc_cot": "403 tu publicreporting.cftc.gov",
    "darwinex": "can dang nhap",
    "fred": "ConnectionReset - Banker da chuyen sang Yahoo/ECB/WorldBank",
}

try:
    from nhan import doc_trinh_duyet as DT
except Exception:
    DT = None

try:
    import telethon_ban as TG     # nguon TELEGRAM qua tai khoan that (Telethon)
except Exception:
    TG = None


# Nhung nguon cao gia tri ma `requests` khong hien duoc (403 / render JS / can
# dang nhap) nhung DOC DUOC qua con Chrome CDP da dang nhap san (.browser_darwinex
# / 9224). Khong tu mo trinh duyet moi (tranh khoa profile / sinh OTP) - chi doc
# khi con CDP dang bat, va tinh-lieu-tu-ngoai len khi khong co.
# `kieu": "trang"` = danh sach trang seed (boc link+text); `kieu": "tu_khoa"`
# = tao URL tim kiem theo tu khoa dang cay bang {k} (giogn doc_cdp.py/bo_nao).
# Tat ca deu CHI doc qua con Chrome CDP dang mo va dang nhap san (.browser_darwinex
# / 9224); khong co CDP thi bo qua (mon no de EVO thay la ket noi thieu).
NGUON_TRINH_DUYET = {
    "mql5_signals": {"kieu": "trang", "trang": ["https://www.mql5.com/en/signals"],
                     "hang": "B", "loai": "ma_nguon", "chu_ky": 43200, "uu_tien": 1},
    "myfxbook":     {"kieu": "trang",
                     "trang": ["https://www.myfxbook.com/"],
                     "hang": "B", "loai": "track_record", "chu_ky": 43200, "uu_tien": 1},
    "collective2":  {"kieu": "trang", "trang": ["https://www.collective2.com/"],
                     "hang": "B", "loai": "track_record", "chu_ky": 86400, "uu_tien": 2},
    "fxblue":       {"kieu": "trang", "trang": ["https://www.fxblue.com/marketdata/systemlist"],
                     "hang": "B", "loai": "track_record", "chu_ky": 86400, "uu_tien": 2},
    "etoro":        {"kieu": "trang",
                     "trang": ["https://www.etoro.com/strategy-investing/copy-open-book-strategies/"],
                     "hang": "B", "loai": "track_record", "chu_ky": 86400, "uu_tien": 2},
    "zulutrade":    {"kieu": "trang", "trang": ["https://www.zulutrade.com/"],
                     "hang": "B", "loai": "track_record", "chu_ky": 86400, "uu_tien": 2},
    "darwinex":     {"kieu": "trang",
                     "trang": ["https://www.darwinex.com/data/darwin-api",
                               "https://www.darwinex.com/account"],
                     "hang": "B", "loai": "track_record", "chu_ky": 86400, "uu_tien": 2},
    "reddit_td":    {"kieu": "trang",
                     "trang": ["https://www.reddit.com/r/algotrading/hot/",
                               "https://www.reddit.com/r/quant/hot/",
                               "https://www.reddit.com/r/options/hot/"],
                     "hang": "B", "loai": "cong_dong", "chu_ky": 21600, "uu_tien": 3},
    # Bon nguon nay dung `tu_khoa_lien_ket`: trang tim kiem cua chung khong co
    # noi dung, chi co link. `loc_lien_ket` giu lai duong dan cua BAI THAT va bo
    # link dieu huong (dang nhap, cai dat, ho tro...).
    "x":            {"kieu": "tu_khoa_lien_ket",
                     "mau": "https://x.com/search?q={k}&f=live",
                     "loc_lien_ket": r"x\.com/[^/]+/status/\d+",
                     "hang": "B", "loai": "social", "chu_ky": 21600, "uu_tien": 3},
    "tiktok":       {"kieu": "tu_khoa_lien_ket",
                     "mau": "https://www.tiktok.com/search/video?q={k}",
                     "loc_lien_ket": r"tiktok\.com/@[^/]+/video/\d+",
                     "hang": "B", "loai": "social", "chu_ky": 21600, "uu_tien": 3},
    "facebook":     {"kieu": "tu_khoa_lien_ket",
                     "mau": "https://www.facebook.com/search/posts?q={k}",
                     "loc_lien_ket": r"facebook\.com/.*(/posts/|/videos/|story_fbid|permalink)",
                     "hang": "B", "loai": "social", "chu_ky": 21600, "uu_tien": 3},
    # UU TIEN 1 tu 30/08/2026 — theo SUAT DO DUOC, khong theo cam giac.
    # Do tren 1.143 ban doc: youtube 20 cau luat -> **5 co che**, ty le cao
    # nhat moi nguon (github 51 -> 6; arxiv 133 ban va openalex 281 ban cho
    # **0**). Phu de tu dong cua YouTube la van xuoi ta luat that su, trong khi
    # bai hoc thuat ta phuong phap. `uu_tien: 3` cu khong phai danh gia chat
    # luong — no chi la cho cac nguon mang xa hoi roi vao hoi con chua ai doc
    # truong `uu_tien` (loi da sua 30/08).
    "youtube":      {"kieu": "tu_khoa_lien_ket",
                     "mau": "https://www.youtube.com/results?search_query={k}",
                     "loc_lien_ket": r"youtube\.com/watch\?v=",
                     "hang": "B", "loai": "video", "chu_ky": 21600, "uu_tien": 1},
    # --- them 30/08/2026 ---
    # TradingView la kho chien luoc CONG KHAI lon nhat con thieu: truoc hom nay
    # so cai co 14 ban tu `tradingview_blog` va **khong mot Pine Script nao**.
    # Trang `/scripts/<chu-de>/` liet ke script that; `a[href*="/script/"]` la
    # bo chon on dinh (ten class cua TradingView doi dinh ky - bo chon cu
    # `[class*="script-"]` tra ve 0 ket qua khi do lai 30/08).
    "tradingview_scripts": {
        "kieu": "trang",
        "trang": ["https://www.tradingview.com/scripts/meanreversion/",
                  "https://www.tradingview.com/scripts/breakout/",
                  "https://www.tradingview.com/scripts/momentum/",
                  "https://www.tradingview.com/scripts/volatility/"],
                     # PHAN TRANG (them 01/09). Do that: `/page-N/` tra 200 va noi
                     # dung KHAC (page-2 co 22 link script, khac hoan toan page 1)
                     # nhung QUA BIEN thi im lang tra lai DUNG page 1 (page-99 va
                     # page-500 giong page 1 tung byte) - khong 404 nhu MQL5. Nen
                     # bien duoc phat hien bang VAN TAY trang 1, xem `_trang_phan_trang`.
                     "mau_trang": "{u}page-{n}/",
                     "trang_moi_luot": 2,
        "hang": "A", "loai": "ma_nguon", "chu_ky": 43200, "uu_tien": 1},
    # --- MQL5 sau khi DANG NHAP (30/08/2026) ---
    #
    # Do that: `mql5_articles` co **58.272 ky tu trung binh moi bai** - CAO NHAT
    # trong moi nguon cua du an, ngang arXiv (53.756) va hon GitHub (46.155).
    # Vay ma so cai chi co **4 bai**. Do la bai ky thuat dai kem MA DAY DU do
    # chinh nguoi viet EA viet ra - dung thu du an can nhat.
    #
    # Trang liet ke cho 42-45 link bai va 40 link ma moi trang.
    #
    # Dang nhap bang GOOGLE (tai khoan Vanh1799). Ten dang nhap KHAC email -
    # do la ly do mot vong thu dang nhap bang 'thebrainago' that bai.
    "mql5_bai_viet": {
        "kieu": "trang",
        "trang": ["https://www.mql5.com/en/articles/trading_systems",
                  "https://www.mql5.com/en/articles/tester",
                  "https://www.mql5.com/en/articles/machine_learning",
                  "https://www.mql5.com/en/articles/statistics"],
        "loc_lien_ket": r"mql5\.com/en/articles/\d+",
        "hang": "A", "loai": "ma_nguon", "chu_ky": 43200, "uu_tien": 1},
    "mql5_ma_expert": {
        "kieu": "trang",
        "trang": ["https://www.mql5.com/en/code/mt5/experts",
                  "https://www.mql5.com/en/code/mt5/indicators"],
        "loc_lien_ket": r"mql5\.com/en/code/\d+",
        "hang": "A", "loai": "ma_nguon", "chu_ky": 43200, "uu_tien": 1},

    # --- bon nguon them 30/08/2026 ---
    # Do that: deu vao duoc KHONG CAN dang nhap, va deu tra ve trang day chu
    # (paperswithcode 1,5 trieu ky tu / quantpedia 641k / quantconnect 265k /
    # elitetrader 70k). Day la HANG cua arXiv va GitHub - dung thu dang thieu,
    # vi hai nguon do da doc CAN.
    "paperswithcode": {
        "kieu": "trang",
        "trang": ["https://paperswithcode.com/search?q=trading",
                  "https://paperswithcode.com/search?q=time+series+forecasting",
                  "https://paperswithcode.com/search?q=portfolio+optimization"],
        "loc_lien_ket": r"paperswithcode\.com/paper/",
        "hang": "A", "loai": "hoc_thuat", "chu_ky": 43200, "uu_tien": 1},
    "quantpedia": {
        "kieu": "trang",
        "trang": ["https://quantpedia.com/strategies/"],
        "loc_lien_ket": r"quantpedia\.com/strategies/[a-z0-9-]{6,}",
        "hang": "A", "loai": "co_che", "chu_ky": 86400, "uu_tien": 1},
    "quantconnect_forum": {
        "kieu": "trang",
        "trang": ["https://www.quantconnect.com/forum/discussions"],
        "loc_lien_ket": r"quantconnect\.com/forum/discussion/\d+",
        "hang": "B", "loai": "dien_dan", "chu_ky": 43200, "uu_tien": 2},
    "elitetrader": {
        "kieu": "trang",
        "trang": ["https://www.elitetrader.com/et/forums/automated-trading.15/",
                  "https://www.elitetrader.com/et/forums/strategy-building.10/"],
        "loc_lien_ket": r"elitetrader\.com/et/threads/",
        "hang": "B", "loai": "dien_dan", "chu_ky": 43200, "uu_tien": 2},
    # --- CONG DONG NGOAI TIENG ANH (them 30/08/2026) ---
    #
    # Chu du an: "tim da ngon ngu de tan dung toi da cac cong dong". Kho hien
    # tai gan nhu chi tieng Anh. Ba cong dong quant lon nhat ngoai tieng Anh
    # (Trung, Nga, Nhat) co truyen thong chia se ma nguon rat manh va ho KHONG
    # viet bang tieng Anh.
    #
    # Do that 30/08 - vao duoc va giau chu: qiita 308k, habr 277k, note 133k,
    # smart-lab 100k, cnblogs 74k, velog 61k ky tu.
    # Bi chan: zhihu (403), csdn (SSL), uqer (chet).
    #
    # Tu khoa la cum NGUOI BAN DIA THUC SU DUNG, khong phai ban dich may.
    "qiita_nhat": {
        "kieu": "tu_khoa_lien_ket", "mau": "https://qiita.com/search?q={k}",
        "tu_khoa_rieng": ["システムトレード", "アルゴリズム取引", "バックテスト 株"],
        "loc_lien_ket": r"qiita\.com/[^/]+/items/[0-9a-f]{8,}",
        "hang": "B", "loai": "cong_dong", "chu_ky": 43200, "uu_tien": 2},
    # Trang TIM KIEM cua habr dung bang JS va tra ve body 535 ky tu, 0 link bai.
    # Trang CHUYEN MUC thi tra ve 23.631 ky tu va 108 link bai. Do that 30/08.
    "habr_nga": {
        "kieu": "trang",
        "trang": ["https://habr.com/ru/hubs/finance/articles/",
                  "https://habr.com/ru/hubs/algorithms/articles/",
                  "https://habr.com/ru/hubs/machine_learning/articles/"],
        "loc_lien_ket": r"habr\.com/ru/(articles|companies/[^/]+/articles)/\d+",
        "hang": "B", "loai": "cong_dong", "chu_ky": 43200, "uu_tien": 2},
    "smartlab_nga": {
        "kieu": "tu_khoa_lien_ket",
        "mau": "https://smart-lab.ru/search/?q={k}",
        "tu_khoa_rieng": ["алгоритмический трейдинг", "торговая стратегия тест"],
        "loc_lien_ket": r"smart-lab\.ru/(blog|company)/.+/\d+",
        "hang": "B", "loai": "cong_dong", "chu_ky": 43200, "uu_tien": 3},
    # Cung ly do voi habr: trang tim kiem zzk.cnblogs.com tra ve 227 ky tu,
    # trang chuyen muc tra ve 5.725 ky tu va 86 link bai.
    "cnblogs_trung": {
        "kieu": "trang",
        "trang": ["https://www.cnblogs.com/cate/python/",
                  "https://www.cnblogs.com/cate/ai/"],
        "loc_lien_ket": r"cnblogs\.com/[^/]+/p/\d+",
        "hang": "C", "loai": "cong_dong", "chu_ky": 43200, "uu_tien": 3},
    "velog_han": {
        "kieu": "tu_khoa_lien_ket", "mau": "https://velog.io/search?q={k}",
        "tu_khoa_rieng": ["퀀트 투자 전략", "알고리즘 트레이딩"],
        "loc_lien_ket": r"velog\.io/@[^/]+/",
        "hang": "C", "loai": "cong_dong", "chu_ky": 86400, "uu_tien": 3},
    "tradingview_ideas": {
        "kieu": "tu_khoa", "mau": "https://www.tradingview.com/ideas/?q={k}",
        "hang": "B", "loai": "cong_dong", "chu_ky": 43200, "uu_tien": 3},
}


def _chuan_hoa_lien_ket(url: str) -> str:
    """Bo tham so khong doi NOI DUNG, de khu trung cho dung.

    Do that 30/08/2026: mot vong quet YouTube ghi **75 "bai"**, nhung phan lon
    la link MOC THOI GIAN trong CUNG MOT video - `...watch?v=0rzXU-BlKCg&t=561s`,
    `&t=434s`, `&t=379s`, `&t=240s`, `&t=100s`, `&t=26s`. Do la muc luc chuong,
    khong phai 75 video. Khu trung theo URL THO nen chung deu lot.

    Mot so tai lieu bi thoi phong khong chi lam ban so lieu: no lam
    `doc_toan_van` tai cung mot trang chuc lan, va lam moi ty le "bai moi tren
    moi luot quet" tro nen vo nghia.
    """
    if "youtube.com/watch" in url:
        m = re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", url)
        return f"https://www.youtube.com/watch?v={m.group(1)}" if m else url
    if "youtu.be/" in url:
        m = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url)
        return f"https://www.youtube.com/watch?v={m.group(1)}" if m else url
    # X/Twitter: mot BAI co nhieu duong dan con - `/analytics`, `/photo/1`,
    # `/video/1`, `/likes`, `/retweets`. Cat het sau ma bai.
    #
    # Do that 30/08: sau khi sua bo loc tieu de, X thu ve 73 'bai' nhung mot
    # nua la trang `/analytics` cua chinh nhung bai kia. Day la bien the THU BA
    # cua cung mot loi trong ngay (YouTube moc thoi gian, YouTube tham so theo
    # doi, va gio la X duong dan con) - khu trung theo URL tho luon thoi phong.
    m = re.search(r"https?://(?:www\.)?(?:x|twitter)\.com/([^/]+)/status/(\d+)", url)
    if m:
        # twitter.com va x.com la CUNG mot bai - khong gop thi dem hai lan.
        return f"https://x.com/{m.group(1)}/status/{m.group(2)}"
    # Bo phan neo va cac tham so theo doi thuong gap.
    url = url.split("#")[0]
    url = re.sub(r"[?&](utm_[a-z]+|fbclid|igshid|pp|si|feature|t)=[^&]*", "", url)
    return url.rstrip("?&")


def _duyet_tai_lieu(d: dict, nguon: str, c: dict, tu_khoa: str = "") -> list[dict]:
    """Nhat ung vien (link+tieu de that) tu trang doc duoc qua trinh duyet.

    `kieu=tu_khoa`: giu nguyen text trang tim kiem lam mot bai (giogn doc_cdp ).
    `kieu=trang`: boc anchor; neu khong co anchor rao ra thi giu ca trang text."""
    if c.get("kieu") == "tu_khoa":
        # `tu_khoa` thuan: giu nguyen van ban TRANG TIM KIEM lam mot bai.
        #
        # DU NHUNG NGUON XA HOI KHONG DUNG DUOC KIEU NAY. Do that 30/08: mo
        # trang tim kiem cua facebook/tiktok/youtube roi luu lai chi duoc **900
        # ky tu van ban dieu huong**, khong phai bai viet. Ba nguon do sinh dung
        # 3 "bai" moi cai, va ca ba deu la trang tim kiem chu khong phai noi
        # dung. Nen chung chuyen sang `tu_khoa_lien_ket` ben duoi.
        ct = (d.get("text") or "").strip()
        if len(ct) < 40:
            return []
        return [{"tieu_de": f"[{nguon}] {tu_khoa or (d.get('title') or 'tim kiem')}",
                 "url": d.get("url") or "", "tom_tat": ct[:900],
                 "hang": c.get("hang", "B"), "loai": c.get("loai", "")}]
    if c.get("kieu") == "tu_khoa_lien_ket":
        # Mo trang TIM KIEM (nhu `tu_khoa`) roi BOC LIEN KET (nhu `trang`):
        # noi dung that nam sau khi bam vao tung bai, khong nam o trang ket qua.
        ra, da = [], set()
        loc = c.get("loc_lien_ket")
        for anch in (d.get("anchor") or []):
            try:
                tt, href = str(anch[0]).strip(), str(anch[1])
            except Exception:
                continue
            if not href.startswith("http"):
                continue
            if loc and not re.search(loc, href):
                continue
            # KHI DA CO `loc_lien_ket`, chinh duong dan la bo loc chat luong -
            # khong duoc siet them bang do dai CHU cua the <a>.
            #
            # Do that 30/08: trang tim kiem cua X co **65 link bai** hop le,
            # nhung link bai cua X thuong boc mot dau thoi gian ("2h", "1d")
            # nen `len(tt) < 12` giet sach. Ket qua: 3 bai thay vi 65.
            # Nguong phai la 1 chu khong phai 3: "2h" chi co hai ky tu.
            if len(tt) < (1 if loc else 12):
                continue
            if len(tt) < 12:
                # Chu qua ngan de lam tieu de -> lay dinh danh tu duong dan.
                tt = f"{tt} — {href.rstrip('/').rsplit('/', 2)[-2:][0]}/{href.rstrip('/').rsplit('/', 1)[-1]}"
            href = _chuan_hoa_lien_ket(href)
            if href in da:
                continue
            da.add(href)
            ra.append({"tieu_de": f"[{nguon}] {tt[:220]}", "url": href,
                       "tom_tat": "", "hang": c.get("hang", "B"),
                       "loai": c.get("loai", "")})
            if len(ra) >= 25:
                break
        return ra
    ra, da = [], set()
    for anch in (d.get("anchor") or []):
        try:
            tt, href = str(anch[0]), str(anch[1])
        except Exception:
            continue
        tt = tt.strip()
        if len(tt) < 8 or not href.startswith("http") or href in da:
            continue
        da.add(href)
        ra.append({"tieu_de": f"[{nguon}] {tt[:220]}", "url": href,
                   "tom_tat": "", "hang": c.get("hang", "B"), "loai": c.get("loai", "")})
        if len(ra) >= 30:
            break
    if not ra and len((d.get("text") or "").strip()) >= 200:
        ra.append({"tieu_de": f"[{nguon}] {d.get('title') or 'trang seed'}",
                   "url": d.get("url") or "", "tom_tat": (d.get("text") or "")[:900],
                   "hang": c.get("hang", "B"), "loai": c.get("loai", "")})
    return ra


def _trang_phan_trang(ma: str, c: dict) -> tuple[list[str], dict]:
    """Sinh danh sach URL cho mot nguon `kieu: trang` CO khai `mau_trang`.

    Nguon khong khai `mau_trang` -> tra dung `c["trang"]` nhu cu (khong doi hanh
    vi cua 20+ nguon con lai). Nguon co khai thi moi luot lay `trang_moi_luot`
    trang KE TIEP theo con tro bien gioi, xoay vong qua cac trang seed.
    """
    if not c.get("mau_trang"):
        return list(c["trang"]), {}
    ct = _con_tro(ma)
    trang = ct.setdefault("trang", {})
    bd = int(ct.get("seed_ke", 0)) % len(c["trang"])
    thu_tu = c["trang"][bd:] + c["trang"][:bd]
    ra, n_seed = [], int(c.get("trang_moi_luot", 2))
    for goc in thu_tu[:n_seed]:
        n = int(trang.get(goc, 1))
        ra.append(goc if n == 1 else c["mau_trang"].format(u=goc, n=n))
    ct["seed_ke"] = (bd + n_seed) % len(c["trang"])
    ct["_dang_lay"] = [[g, int(trang.get(g, 1))] for g in thu_tu[:n_seed]]
    return ra, ct


def _tien_con_tro_trang(ma: str, ct: dict, van_tay: dict) -> None:
    """Tien con tro sau mot luot doc, va phat hien BIEN bang van tay trang 1.

    TradingView khong 404 khi qua trang cuoi - no im lang tra lai trang 1. Neu
    chi tien con tro mu thi tu do tro di he doc lai trang 1 mai ma van tuong
    minh dang di sau. Nen: nho van tay trang 1 cua tung seed; trang N>1 nao
    trung van tay do la da CHAM BIEN -> ghi lai `trang_cuoi` va quay ve 1.
    """
    if not ct:
        return
    trang, vt1 = ct.setdefault("trang", {}), ct.setdefault("van_tay_1", {})
    cuoi = ct.setdefault("trang_cuoi", {})
    for goc, n in ct.pop("_dang_lay", []):
        v = van_tay.get(goc if n == 1 else f"{goc}#{n}")
        if v is None:
            continue                       # doc loi: giu nguyen con tro, thu lai sau
        if n == 1:
            vt1[goc] = v
            trang[goc] = 2
        elif vt1.get(goc) and v == vt1[goc]:
            cuoi[goc] = n - 1
            trang[goc] = 1
            ct["vong"] = int(ct.get("vong", 0)) + 1
        else:
            trang[goc] = n + 1
    ct["da_quet_trang"] = int(ct.get("da_quet_trang", 0)) + len(van_tay)
    _ghi_con_tro(ma, ct)


def quet_trinh_duyet(ngan_sach_giay: int = 90, t0: float | None = None) -> dict:
    """Doc cac nguon can-trinh-duyet qua CON CHROME CDP DANG MO (dang nhap san).

    Khong co CDP -> khong lam gi (nen mon no de EVO thay la day la ket noi thieu,
    khong phai loi). Co CDP -> quet tung nguon den han va luu tai lieu."""
    t0 = t0 or time.time()
    ra = {"port": None, "da_quet": 0, "tai_lieu_moi": 0}
    if not NGUON_TRINH_DUYET:
        return ra
    port = DT.cdp_dang_chay() if DT else None
    ra["port"] = port
    if not port:
        # be du lieu de khong gay ra nhieu han "moi khi khong co CDP" - EVO thay
        # nguyen nhan that: thieu k/.mo trinh duyet.
        SO.bao_van_de(
            "nguon_can_trinh_duyet", "VUA",
            f"CDP trinh duyet CHUA MO - {len(NGUON_TRINH_DUYET)} nguon cao gia tri "
            "chua quet duoc. Mo Chrome .browser_darwinex kem CDP (vd 9224).",
            {"nguon": sorted(NGUON_TRINH_DUYET)})
        return ra
    now = time.time()
    den_han = []
    # XEP THEO UU TIEN, roi theo lau chua quet nhat.
    #
    # Truoc 30/08 cau nay khong co ORDER BY nao ca - thu tu la thu tu rowid, tuc
    # NGAU NHIEN theo thu tu dang ky. Truong `uu_tien` duoc khai trong
    # NGUON_TRINH_DUYET va ghi vao bang `nguon`, nhung **khong ai doc no** o
    # duong nay (duong nguon API o `mot_luot` thi co `ORDER BY uu_tien`).
    #
    # Hau qua do duoc: ngan sach quet chi 90 giay/luot, bi nhung nguon dung dau
    # bang an het, va **x / tiktok / facebook / youtube (uu_tien 3) chua bao gio
    # toi luot** - so cai co 0 bai tu ca bon nguon do. Trieu chung nhin tu ngoai
    # la "mang xa hoi fetch khong duoc", trong khi ma da san sang tu lau.
    #
    # Them `lan_cuoi` lam khoa phu de trong cung mot muc uu tien thi nguon lau
    # chua quet nhat duoc di truoc - khong thi mot nguon o cuoi bang co the doi
    # mai.
    for r in SO.nhieu("SELECT * FROM nguon WHERE trang_thai='BAT' "
                      "ORDER BY COALESCE(uu_tien, 9), COALESCE(lan_cuoi, 0)"):
        if r["ma"] not in NGUON_TRINH_DUYET:
            continue
        he_so = 2 ** min(r["loi_lien_tuc"] or 0, 5)
        if now - (r["lan_cuoi"] or 0) >= (r["chu_ky_giay"] or 21600) * he_so:
            den_han.append(r["ma"])
    for ma in den_han:
        if time.time() - t0 > ngan_sach_giay * 0.6:
            break
        c = NGUON_TRINH_DUYET[ma]
        import urllib.parse as _ur
        # `tu_khoa` va `tu_khoa_lien_ket` deu dung MAU + tu khoa; chung chi khac
        # nhau o cach BOC trang ket qua (xem `_duyet_tai_lieu`).
        if str(c.get("kieu", "")).startswith("tu_khoa"):
            # `tu_khoa_rieng`: nguon ngoai tieng Anh phai dung tu khoa BAN DIA.
            # Cong dong quant Nhat khong tim bang "mean reversion" ma bang
            # "システムトレード"; ep tu khoa tieng Anh vao qiita.com thi ra rong,
            # va cai rong do se bi doc nham thanh "nguon nay khong co gi".
            tu = c.get("tu_khoa_rieng") or tu_khoa_dung(3)
            phieu = [_ur.quote(k) for k in tu[:_so_tu_khoa("mql5_code")]]
            phieu = [c["mau"].replace("{k}", q) for q in phieu]
            ct_trang = {}
        else:
            phieu, ct_trang = _trang_phan_trang(ma, c)
        tong_moi, loi_td = 0, []
        vt_trang = {}
        try:
            for u in phieu:
                d = DT.doc_gan(u, port=port)
                if d.get("loi"):
                    loi_td.append(str(d["loi"])[:60])
                    continue
                ds = _duyet_tai_lieu(d, ma, c, tu_khoa=u)
                # van tay = tap URL boc duoc, dung de biet trang nay co that su
                # moi khong (xem `_tien_con_tro_trang`).
                if ct_trang:
                    # khop bang TIEN TO: URL co phan trang la goc + "page-N/",
                    # nen `u.startswith(goc)` la dinh danh dung. Khop bang chuoi
                    # "page-N" thi hai seed cung o trang N se khop lan nhau.
                    goc = next((g for g, _ in ct_trang.get("_dang_lay", [])
                                if u.startswith(g)), u)
                    n_hien = next((n for g, n in ct_trang.get("_dang_lay", [])
                                   if g == goc), 1)
                    vt_trang[goc if n_hien == 1 else f"{goc}#{n_hien}"] = SO.van_tay(
                        "|".join(sorted(x.get("url", "") for x in ds)))
                if ds:
                    tong_moi += luu_tai_lieu(ma, ds)
            _tien_con_tro_trang(ma, ct_trang, vt_trang)
            SO.chay("UPDATE nguon SET lan_cuoi=?, so_lan=so_lan+1, loi_lien_tuc=0, "
                    "thu_hoach=thu_hoach+?, ghi_chu=? WHERE ma=?",
                    time.time(), tong_moi,
                    ("; ".join(loi_td)[:140] if (loi_td and tong_moi == 0) else ""), ma)
            ra["da_quet"] += 1
            ra["tai_lieu_moi"] += tong_moi
        except Exception as e:
            SO.chay("UPDATE nguon SET loi_lien_tuc=loi_lien_tuc+1, ghi_chu=? WHERE ma=?",
                    f"{type(e).__name__}: {str(e)[:100]}", ma)
    if ra["da_quet"]:
        SO.dong_van_de("nguon_can_trinh_duyet",
                       f"da quet {ra['da_quet']} nguon qua trinh duyet")
    else:
        SO.bao_van_de("nguon_can_trinh_duyet", "VUA",
                      "co CDP nhung khong co nguon den han - kiem tra lai trang seed",
                      {"nguon": sorted(NGUON_TRINH_DUYET)})
    return ra


# ------------------------------------------------------------ TELEGRAM (FOLLOW)
# TELEGRAM khong can CDP: dung session user that (config/telethon_thebrain.session)
# da dang nhap + telethon. THEO DOI (follow) bang cach doc tin moi tu cac kenh
# trading seed + quy/prop va nap vao thu vien tai lieu cua SEEKER.
def quet_telegram_follow(toi_da_kenh: int = 10, so_bai_moi_kenh: int = 6,
                         ngan_sach_giay: int = 60, t0: float | None = None) -> dict:
    t0 = t0 or time.time()
    if not TG:
        return {"loi": "khong co telethon"}
    import asyncio

    async def _lam():
        if not TG.SEED_KENH or not TG.QUY_KENH:
            return {"loi": "chua co danh sach kenh"}
        tong_moi, da, phieu = 0, set(), []
        for u in (TG.SEED_KENH + TG.QUY_KENH):
            if u in da:
                continue
            da.add(u)
            phieu.append(u)
            if len(phieu) >= toi_da_kenh:
                break
        async with TG._ket_noi() as cl:
            if not await cl.is_user_authorized():
                return {"loi": "session_het_han"}
            so_moi, loi, doc = 0, [], 0
            for u in phieu:
                if time.time() - t0 > ngan_sach_giay:
                    break
                try:
                    ent = await cl.get_entity(u)
                except Exception:
                    continue
                ten = getattr(ent, "title", None) or u
                un = getattr(ent, "username", "") or u
                dem = 0
                try:
                    async for msg in cl.iter_messages(ent, limit=so_bai_moi_kenh):
                        t = ("%s" % (getattr(msg, "message", "") or "")).strip()
                        if len(t) < 20:
                            continue
                        url = ("https://t.me/%s/%s" % (un, msg.id)) if un else ""
                        m = luu_tai_lieu("telegram", [{
                            "tieu_de": "[%s] %s" % (u, t[:200]), "url": url,
                            "tom_tat": t[:900], "hang": "B", "loai": "telegram"}])
                        so_moi += m
                        dem += 1
                except Exception:
                    loi.append(u)
                doc += 1
            return {"da_follow": doc, "loi_kenh": len(loi), "tin_moi": so_moi}

    try:
        return asyncio.run(_lam())
    except Exception as e:
        return {"loi": "%s: %s" % (type(e).__name__, str(e)[:100])}


# --------------------------------------------------------------- TU KHOA
DUNG_TU = set("""the a an and or of for with without on in to from by is are was were be been
this that these those we our their its it as at into than then there here how what which who
using use used based paper study we show results method approach model models new novel data""".split())


def _cum_tu(vb: str, n: int = 2) -> list[str]:
    tu = [w for w in re.findall(r"[a-z][a-z\-]{2,}", (vb or "").lower()) if w not in DUNG_TU]
    return [" ".join(tu[i:i + n]) for i in range(len(tu) - n + 1)]


def khoi_tao_tu_khoa() -> None:
    with SO.ket_noi() as cn:
        for t in TU_KHOA_GOC:
            cn.execute("INSERT OR IGNORE INTO tu_khoa(tu,linh_vuc,diem,sinh_tu,luc) "
                       "VALUES(?,'tai_chinh',2.0,'goc',?)", (t, SO.bay_gio()))


def tu_khoa_dung(n: int = 6) -> list[str]:
    """Chon tu khoa theo diem, uu tien cai it dung (kham pha) va cai nang suat cao."""
    rows = SO.nhieu(
        "SELECT tu, diem, so_lan_dung, so_ket_qua FROM tu_khoa WHERE linh_vuc='tai_chinh' "
        "ORDER BY (diem + 1.0*so_ket_qua/(so_lan_dung+1)) DESC, so_lan_dung ASC LIMIT ?", n * 3)
    if not rows:
        khoi_tao_tu_khoa()
        return TU_KHOA_GOC[:n]
    rows.sort(key=lambda r: (r["so_lan_dung"], -r["diem"]))
    return [r["tu"] for r in rows[:n]]


def mo_rong_tu_khoa(tai_lieu: list[dict], toi_da: int = 8) -> int:
    """Rut cum tu tu tai lieu HANG A/B lam tu khoa moi. Day la cach he tu di sau."""
    dem: dict[str, int] = {}
    for t in tai_lieu:
        if t.get("hang") not in ("A", "B"):
            continue
        for c in _cum_tu(t.get("tieu_de", "") + " " + t.get("tom_tat", "")[:400]):
            dem[c] = dem.get(c, 0) + 1
    ung = [c for c, n in sorted(dem.items(), key=lambda x: -x[1]) if n >= 3][:toi_da]
    them = 0
    with SO.ket_noi() as cn:
        for c in ung:
            cur = cn.execute(
                "INSERT OR IGNORE INTO tu_khoa(tu,linh_vuc,diem,sinh_tu,luc) "
                "VALUES(?,'tai_chinh',1.0,'tu_sinh',?)", (c, SO.bay_gio()))
            them += cur.rowcount
    return them


# ------------------------------------------------------------------ LUU + NOI
def luu_tai_lieu(nguon: str, ds: list[dict]) -> int:
    moi = 0
    with SO.ket_noi() as cn:
        for d in ds:
            if not d.get("tieu_de"):
                continue
            vt = SO.van_tay(d.get("url") or d["tieu_de"])
            diem = {"A": 3.0, "B": 2.0}.get(d.get("hang", "C"), 1.0) + d.get("diem_them", 0)
            cur = cn.execute(
                "INSERT OR IGNORE INTO tai_lieu(van_tay,nguon,loai,tieu_de,url,tom_tat,"
                "tu_khoa,diem,luc) VALUES(?,?,?,?,?,?,?,?,?)",
                (vt, nguon, d.get("loai", ""), d["tieu_de"][:400], d.get("url", ""),
                 d.get("tom_tat", "")[:2000], d.get("hang", "C"), diem, SO.bay_gio()))
            moi += cur.rowcount
    # Nguon nao DA cam ma trong tay (Pine tu suggest-json) thi ghi thang ban doc,
    # khong de `doc_toan_van` phai keo lai mot lan nua - trang /script/<slug>/
    # render bang JS nen keo lai cung khong ra ma.
    for d in ds:
        if d.get("_pine") and d.get("url"):
            try:
                _ghi_ban_doc(d["url"], d["_pine"], "ma_nguon")
            except Exception:
                pass
    return moi


# LEGACY V1: giu de tuong thich/doi chieu. V2 khong goi ham nay tu mot_luot().
BAN_DO_MAU = {
    "ibs_bat_day": ["internal bar strength", "ibs", "close location", "buy the dip",
                    "overnight reversal"],
    "momentum_ema": ["momentum", "moving average", "trend following", "time series momentum"],
    "sma_cheo": ["moving average crossover", "golden cross", "sma cross"],
    "donchian": ["breakout", "channel breakout", "donchian", "turtle"],
    "rsi_dao_chieu": ["rsi", "relative strength index", "oversold", "mean reversion"],
    "bollinger_ve": ["bollinger", "standard deviation band", "mean reversion"],
    "ichimoku_cheo": ["ichimoku", "tenkan", "kijun"],
    "cuoi_thang": ["turn of the month", "month end", "seasonality", "calendar effect"],
    "gio_trong_ngay": ["intraday seasonality", "time of day", "session", "opening range"],
    "bien_do_thu_hep": ["volatility squeeze", "low volatility", "range contraction", "atr"],
}


def noi_sang_quantlab(gioi_han: int = 5) -> dict:
    """LEGACY V1: map keyword sang mau va xep backtest; V2 khong goi mac dinh."""
    ds = SO.nhieu("SELECT * FROM tai_lieu WHERE da_khai_thac=0 AND tu_khoa IN('A','B') "
                  "ORDER BY diem DESC LIMIT ?", gioi_han * 4)
    xep, chua_co = 0, []
    for t in ds:
        vb = (t["tieu_de"] + " " + (t["tom_tat"] or "")).lower()
        khop = [m for m, tu in BAN_DO_MAU.items() if any(k in vb for k in tu)]
        if khop:
            for m in khop[:2]:
                if SO.them_viec("QUANTLAB", "kham_pha_theo_mau",
                                {"mau": m, "nguon_tai_lieu": t["url"] or t["tieu_de"][:80]},
                                uu_tien=4):
                    xep += 1
        elif t["tu_khoa"] == "A":
            chua_co.append(t["tieu_de"][:120])
        SO.chay("UPDATE tai_lieu SET da_khai_thac=1 WHERE id=?", t["id"])
        if xep >= gioi_han:
            break
    if chua_co:
        SO.bao_van_de(
            "can_mau_moi", "VUA",
            f"{len(chua_co)} tai lieu HANG A mo ta co che CHUA CO trong nhan/mau.py - "
            "can them template moi thi QUANTLAB moi kiem dinh duoc",
            {"vi_du": chua_co[:5]})
    return {"xep_viec": xep, "co_che_chua_co_mau": len(chua_co)}


# ======================================================================
# TANG 2: DOC. Lay NOI DUNG THAT ve, khong dung o dong tieu de.
# ======================================================================
_ARTIFACT_CURSOR_METRIC = "seeker_document_artifact_cursor"


def _artifact_timestamp(value: str | None) -> str:
    """Doi timestamp SQLite cu (gio local, khong timezone) sang UTC ISO-8601."""
    try:
        parsed = datetime.fromisoformat(str(value or ""))
    except ValueError:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.astimezone()
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _document_artifact(row: dict) -> HD.DocumentArtifact:
    """Chuyen mot noi_dung da luu thanh contract bat bien, khong suy luan co che."""
    content = str(row.get("van_ban") or "")
    if not content:
        raise HD.ContractError("noi_dung khong co van_ban de tao DocumentArtifact")
    original_url = str(row.get("url") or "").strip()
    source_url = original_url
    if not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", source_url):
        source_url = "urn:the-brain:document:" + str(
            row.get("noi_dung_van_tay") or SO.van_tay("nd", original_url, content))

    metadata = {
        "acquisition_method": str(row.get("cach") or "unknown"),
        "characters_original": int(row.get("so_ky_tu_goc") or len(content)),
        "characters_stored": int(row.get("so_ky_tu") or len(content)),
        "content_kind": str(row.get("kieu") or "text"),
        "legacy_content_fingerprint": str(row.get("noi_dung_van_tay") or ""),
        "source_tier_at_capture": str(row.get("tu_khoa") or ""),
    }
    if source_url != original_url:
        metadata["original_url"] = original_url

    return HD.DocumentArtifact(
        source_id=str(row.get("nguon") or "unknown"),
        source_url=source_url,
        title=str(row.get("tieu_de") or original_url or "Untitled document"),
        retrieved_at=_artifact_timestamp(row.get("luc")),
        content=content,
        media_type="text/plain; charset=utf-8",
        metadata=metadata,
    )


def _ghi_document_artifact(row: dict) -> tuple[int, bool]:
    return SO.them_artifact(_document_artifact(row))


def _noi_dung_artifact(van_tay_noi_dung: str) -> tuple[int, bool]:
    row = SO.mot(
        "SELECT n.id noi_dung_id,n.van_tay noi_dung_van_tay,n.url,n.kieu,n.cach,"
        "n.so_ky_tu,n.so_ky_tu_goc,n.van_ban,n.luc,t.nguon,t.tieu_de,t.tu_khoa "
        "FROM noi_dung n LEFT JOIN tai_lieu t ON t.id=n.tai_lieu_id "
        "WHERE n.van_tay=?", van_tay_noi_dung)
    if not row:
        raise HD.ContractError("khong tim thay noi_dung vua luu")
    return _ghi_document_artifact(row)


def backfill_document_artifacts(gioi_han: int = 250) -> dict:
    """Backfill noi_dung cu theo cursor ben vung; an toan khi goi lai.

    Cursor chi tien qua dong da ghi artifact thanh cong hoac dong that bai/khong co
    noi dung. Neu ghi artifact loi, ham dung truoc dong do de luot sau thu lai.
    """
    if isinstance(gioi_han, bool) or not isinstance(gioi_han, int) or not 1 <= gioi_han <= 5000:
        raise ValueError("gioi_han phai la so nguyen 1..5000")
    state = SO.mot(
        "SELECT CAST(gia_tri AS INTEGER) cursor FROM chi_so_vh "
        "WHERE ten=? ORDER BY id DESC LIMIT 1", _ARTIFACT_CURSOR_METRIC)
    cursor_cu = int(state["cursor"] or 0) if state else 0
    rows = SO.nhieu(
        "SELECT n.id noi_dung_id,n.van_tay noi_dung_van_tay,n.url,n.kieu,n.cach,"
        "n.so_ky_tu,n.so_ky_tu_goc,n.van_ban,n.luc,t.nguon,t.tieu_de,t.tu_khoa "
        "FROM noi_dung n LEFT JOIN tai_lieu t ON t.id=n.tai_lieu_id "
        "WHERE n.id>? ORDER BY n.id LIMIT ?", cursor_cu, gioi_han)
    cursor = cursor_cu
    da_xem, moi, da_co, bo_qua, loi = 0, 0, 0, 0, None
    for row in rows:
        thanh_cong = (row.get("kieu") != "khong_doc_duoc"
                      and int(row.get("so_ky_tu") or 0) > 0
                      and bool(row.get("van_ban")))
        if thanh_cong:
            try:
                _, created = _ghi_document_artifact(row)
                moi += int(created)
                da_co += int(not created)
            except Exception as exc:
                loi = f"{type(exc).__name__}: {str(exc)[:180]}"
                SO.ghi_chi_so("seeker_artifact_loi", 1,
                              {"noi_dung_id": row["noi_dung_id"], "loi": loi})
                break
        else:
            bo_qua += 1
        cursor = int(row["noi_dung_id"])
        da_xem += 1

    if cursor > cursor_cu:
        SO.ghi_chi_so(_ARTIFACT_CURSOR_METRIC, cursor,
                      {"artifact_moi": moi, "artifact_da_co": da_co,
                       "bo_qua": bo_qua, "loi": loi})
    con_lai = SO.mot("SELECT COUNT(*) n FROM noi_dung WHERE id>?", cursor)["n"]
    return {"da_xem": da_xem, "artifact_moi": moi,
            "artifact_da_co": da_co, "bo_qua": bo_qua, "loi": loi,
            "cursor": cursor, "con_lai": con_lai}


def _diem_nang_suat() -> dict:
    """Nguon -> gia thuyet duoc dang ky tren moi bai da boc (Laplace).

    Day la THUOC DO cua SEEKER tu 01/09 (xem `evolution.do_van_hanh`), va day la
    cho no doi hanh vi chu khong chi doi bao cao: no xep hang doi doc.
    """
    doc = {r["ng"]: r["n"] for r in SO.nhieu(
        "SELECT t.nguon ng, COUNT(*) n FROM noi_dung nd "
        "JOIN tai_lieu t ON t.id = nd.tai_lieu_id WHERE nd.da_boc=1 GROUP BY t.nguon")}
    # Tu so lay tu `gia_thuyet` chu KHONG tu `de_xuat`: bang `de_xuat` chi duoc
    # ghi boi `boc_co_che`, va ham do la LEGACY V1 ma `mot_luot()` khong goi.
    # Doc no thi moi nguon deu ra 0 va thu tu nay tro thanh vo nghia.
    nhan = {r["ng"]: r["n"] for r in SO.nhieu(
        "SELECT t.nguon ng, COUNT(*) n FROM gia_thuyet g "
        "JOIN tai_lieu t ON t.url = g.nguon GROUP BY t.nguon")}
    return {ng: (nhan.get(ng, 0) + 1) / (n + 2) for ng, n in doc.items()}


def _nguyen_nhan(url: str, loi: str) -> str:
    u = (url or "").lower()
    l = (loi or "").lower()
    if "khong co ban mo" in l or "paywall" in l:
        return "paywall_khong_co_ban_mo"
    if "openalex http" in l:
        return "doi_khong_tra_cuu_duoc"
    if "khong_mo_cdp" in l:
        return "can_trinh_duyet_nhung_cdp_tat"
    if any(k in l for k in ("sslerror", "ssl")):
        return "sni_bi_loc"
    if "429" in l:
        return "bi_han_muc_429"
    if "403" in l:
        return "bi_tu_choi_403"
    if any(k in l for k in ("timeout", "connectionerror", "connection")):
        return "het_gio_hoac_mat_ket_noi"
    if "name_not_resolved" in l or "dns" in l:
        return "dns_bi_chan"
    if "t.me" in u or "telegram" in u:
        return "can_trinh_duyet_nhung_cdp_tat"
    return "khong_boc_duoc"


def thu_hoi_khong_doc_duoc(gioi_han: int = 12, ngan_sach_giay: int = 120) -> dict:
    """Thu lai cac ban `khong_doc_duoc`, ghi NGUYEN NHAN THAT cho ban con lai.

    Mot ban thu hoi duoc se duoc GHI DE tai cho (cung `van_tay`), nen no chay
    tiep vao tang artifact nhu moi ban doc khac - khong sinh ban trung.

    Ban khong thu hoi duoc KHONG bi xoa va KHONG bi khoa: `ket_boc` giu nguyen
    nhan do duoc, de lan sau con biet nen sua cai gi. Loi MOI TRUONG (CDP tat,
    mat mang) de nguyen cho lan sau, y het `doc_toan_van`.
    """
    t0 = time.time()
    ds = SO.nhieu(
        "SELECT n.id, n.van_tay, n.url, n.tai_lieu_id, t.tieu_de, t.nguon "
        "FROM noi_dung n LEFT JOIN tai_lieu t ON t.id=n.tai_lieu_id "
        "WHERE n.kieu='khong_doc_duoc' AND (n.ket_boc IS NULL OR n.ket_boc "
        "NOT LIKE 'nguyen_nhan:%') AND n.url LIKE 'http%' "
        "ORDER BY n.id LIMIT ?", max(int(gioi_han) * 3, 1))
    bao = {"da_thu": 0, "thu_hoi_duoc": 0, "ky_tu": 0, "nguyen_nhan": {},
           "artifact_moi": 0}
    for r in ds:
        if bao["da_thu"] >= gioi_han or time.time() - t0 > ngan_sach_giay:
            break
        bao["da_thu"] += 1
        try:
            kq = TV.doc(r["url"])
        except Exception as e:
            kq = None
            TV.LOI_CUOI.update({"url": r["url"], "loi": f"{type(e).__name__}: {e}"})
        if not kq:
            loi = str((TV.LOI_CUOI or {}).get("loi") or "")
            nn = _nguyen_nhan(r["url"], loi)
            bao["nguyen_nhan"][nn] = bao["nguyen_nhan"].get(nn, 0) + 1
            if TV.loi_tam_thoi():
                # MOI TRUONG, khong phai thuoc tinh cua dia chi: de nguyen cho
                # lan sau, khong dong dau nguyen nhan.
                continue
            SO.chay("UPDATE noi_dung SET ket_boc=? WHERE id=?",
                    f"nguyen_nhan:{nn} | {loi[:160]}", r["id"])
            continue
        # THU HOI DUOC: nang chinh ban ghi cu len thanh ban doc that.
        SO.chay(
            "UPDATE noi_dung SET kieu=?, cach=?, so_ky_tu=?, so_ky_tu_goc=?, "
            "van_ban=?, luc=?, da_boc=0, ket_boc=? WHERE id=?",
            kq["kieu"], kq["cach"], kq["so_ky_tu"],
            kq.get("so_ky_tu_goc", kq["so_ky_tu"]), kq["van_ban"], SO.bay_gio(),
            "thu_hoi_duoc", r["id"])
        bao["thu_hoi_duoc"] += 1
        bao["ky_tu"] += kq["so_ky_tu"]
        try:
            _, moi = _noi_dung_artifact(r["van_tay"])
            bao["artifact_moi"] += int(moi)
        except Exception as e:
            SO.ghi_chi_so("seeker_artifact_loi", 1,
                          {"url": str(r["url"])[:120], "loi": str(e)[:120]})
    con_lai = SO.mot("SELECT COUNT(*) n FROM noi_dung WHERE kieu='khong_doc_duoc'")
    bao["con_lai"] = con_lai["n"] if con_lai else None
    if bao["da_thu"]:
        SO.ghi_chi_so("seeker_thu_hoi", bao["thu_hoi_duoc"], bao)
    return bao


# ======================================================================
# TANG 3: BOC. Van ban -> KHANG DINH co so + CO CHE kiem dinh duoc.
# ======================================================================
HE_THONG_BOC = """Ban la tang BOC cua mot phong lab dinh luong. Ban duoc dua NOI DUNG
THAT cua mot tai lieu (toan van bai bao, ma nguon chien luoc, hoac bai dien dan).

Viec cua ban KHONG phai tom tat. Viec cua ban la rut ra thu KIEM DINH DUOC:
mot khang dinh co the SAI, va neu duoc thi mot co che dien dat bang ngu phap.

Ky luat bat buoc:
- CHI dung nhung gi CO TRONG VAN BAN. Moi khang dinh phai kem `trich_dan` la
  cau/doan NGUYEN VAN lay tu van ban. Khong co trich dan = bia dat.
- Con so cong bo trong tai lieu la CUA HO, khong phai cua ta. Ghi lai de sau
  doi chieu khi tai lap, khong duoc coi la bang chung.
- Neu tai lieu khong chua co che giao dich nao (vi du: mot thu vien backtest,
  mot bai ve ha tang) thi noi thang: `khang_dinh: []`. Do la cau tra loi tot.
- Neu co co che nhung NGU PHAP khong dien dat duoc, viet ro thieu toan hang gi
  vao `khong_dien_dat_duoc`. Do la cach ngu phap duoc mo rong."""



def _doc_dinh_tuyen(t: dict) -> dict | None:
    """Doc mot tai lieu, DINH TUYEN theo dia chi thay vi luon dung bo doc chung.

    Vi sao: do 01/09 tren 37 ban doc cua `mql5_code` cho thay ta dang luu THANH
    DIEU HUONG cua trang chu khong phai ma - "Forum | Market | Signals |
    Freelance | VPS | Quotes | ..." - va chi 2/37 ban co mot ky hieu MQL nao.
    Nguon dac nhat cua ca he (12.200 muc sau khi sua phan trang) dang duoc luu
    duoi dang khung trang.

    Ha tang de lam dung DA CO SAN va khong ai goi: `nhan/ma_nguon.tai_ma_nguon`
    doc trang bai, tim link `/en/code/download/<id>/<ten>.mq5` va tai FILE DON
    (co tran kich thuoc, co xu ly UTF-16 cua MetaEditor, khong dong den .zip).
    Day chi la mot dong noi day.
    """
    u = str(t.get("url") or "")
    if re.match(r"https?://(www\.)?mql5\.com/[a-z]{2}/code/\d+", u):
        from nhan import ma_nguon as MN
        r = MN.tai_ma_nguon({"url": u, "tieu_de": t.get("tieu_de") or ""})
        if r and r.get("noi_dung"):
            vb = r["noi_dung"]
            return {"van_ban": vb, "so_ky_tu": len(vb), "so_ky_tu_goc": len(vb),
                    "kieu": "ma_nguon", "cach": "mql5_download"}
        # Khong lay duoc file don -> ROT VE bo doc chung, khong tra None: tra
        # None o day se danh dau dia chi la "khong doc duoc" vinh vien.
    return TV.doc(u)


def doc_toan_van(gioi_han: int = 8, ngan_sach_giay: int = 240) -> dict:
    """Keo toan van / ma nguon cua tai lieu hang A-B chua co ban doc.

    Do 16/08 truoc khi co tang nay: ca kho tai lieu la 456 ban ghi / 202.760 ky
    tu = 51 trang A4, va do chi la tieu de + tom tat. Mot repo 22.851 sao nam
    trong so voi dung 49 ky tu mo ta. Khong the nghien cuu tu 49 ky tu.
    """
    t0 = time.time()
    # XEP HANG DOC THEO NANG SUAT DO DUOC, khong theo hang + id.
    #
    # Ban cu xep `hang A truoc, roi diem, roi id DESC`. Hau qua do duoc 01/09:
    # trong 237 bai da doc toan van co **195 la openalex** (82%) - dung cai nguon
    # ma chinh EVO da ha uu tien tu 30/08 vi suat ra artifact 6% - con `mql5_code`
    # (suat 70%) doc toan van duoc **0 bai**. Cai gi kem nhat lai an gan het ngan
    # sach doc.
    #
    # `_diem_nang_suat` la ty le LAPLACE (k+1)/(n+2) chu khong phai k/n. Ly do:
    # nguon chua doc bai nao phai duoc phan biet voi nguon doc roi ma khong ra gi.
    # Voi k/n thi ca hai deu bang 0 va nguon moi khong bao gio duoc thu. Voi
    # (k+1)/(n+2), nguon chua do duoc 0,5 (cao, se duoc thu ngay), openalex
    # 1/197 = 0,005 (thap, lui lai) - va thu tu tu dieu chinh khi so lieu ve.
    diem_ns = _diem_nang_suat()
    ds = SO.nhieu(
        "SELECT t.id, t.tieu_de, t.url, t.tu_khoa, t.nguon, t.diem FROM tai_lieu t "
        "LEFT JOIN noi_dung n ON n.tai_lieu_id = t.id "
        "WHERE n.id IS NULL AND t.url LIKE 'http%' AND t.tu_khoa IN('A','B') "
        "ORDER BY CASE t.tu_khoa WHEN 'A' THEN 0 ELSE 1 END, t.diem DESC, t.id DESC "
        "LIMIT ?", gioi_han * 30)
    ds.sort(key=lambda t: (-diem_ns.get(t["nguon"], 0.5),
                           0 if t["tu_khoa"] == "A" else 1,
                           -(t["diem"] or 0), -t["id"]))
    ds = ds[:gioi_han * 3]
    doc_duoc, that_bai, tong_ky_tu = 0, 0, 0
    cong_cu_moi = 0
    thanh_phan_moi = 0
    tam_thoi = 0
    artifact_moi, artifact_da_co, artifact_loi = 0, 0, 0
    for t in ds:
        if doc_duoc >= gioi_han or time.time() - t0 > ngan_sach_giay:
            break
        try:
            r = _doc_dinh_tuyen(t)
        except Exception as e:
            r = None
            SO.ghi_chi_so("seeker_doc_loi", 1, {"url": t["url"][:120],
                                                "loi": f"{type(e).__name__}: {str(e)[:80]}"})
        if not r:
            that_bai += 1
            # Loi MOI TRUONG (DNS chan, CDP tat, mang rot) KHONG duoc khoa vinh
            # vien mot dia chi: doi mang la doc duoc. Da sap that 30/08 - mot
            # dem danh dau 83 dia chi Reddit vi `ERR_NAME_NOT_RESOLVED`.
            if TV.loi_tam_thoi():
                tam_thoi += 1
                continue
            # Con lai: danh dau da thu de khong keo lai mai mot dia chi hong.
            with SO.ket_noi() as cn:
                cn.execute(
                    "INSERT OR IGNORE INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,"
                    "so_ky_tu,so_ky_tu_goc,van_ban,luc,da_boc,ket_boc) "
                    "VALUES(?,?,?,'khong_doc_duoc','',0,0,'',?,1,'khong doc duoc')",
                    (t["id"], SO.van_tay("nd", t["url"]), t["url"], SO.bay_gio()))
            continue
        noi_dung_van_tay = SO.van_tay("nd", t["url"])
        luc_doc = SO.bay_gio()
        with SO.ket_noi() as cn:
            cn.execute(
                "INSERT OR IGNORE INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,"
                "so_ky_tu,so_ky_tu_goc,van_ban,luc) VALUES(?,?,?,?,?,?,?,?,?)",
                (t["id"], noi_dung_van_tay, t["url"], r["kieu"], r["cach"],
                 r["so_ky_tu"], r.get("so_ky_tu_goc", r["so_ky_tu"]), r["van_ban"],
                 luc_doc))
        # NHAT DOC DUONG: van ban vua doc co the chua mot CONG CU nang cap
        # duoc, khong phai chien luoc. Truoc 30/08 thu do bi bo di - trong khi
        # 34/52 file .mq5 do duoc la tien_ich/chi_bao chu khong phai chien luoc.
        # Khong ton mot lan tai trang nao: van ban da nam trong tay.
        try:
            cong_cu_moi += SCC.nhat_tu_ban_doc(
                t["tieu_de"], r["van_ban"], t["url"], t["nguon"])
        except Exception:
            pass

        # THU HOI THANH PHAN (them 01/09, chu du an chot). Chay cho MOI ban doc,
        # khong doi ban doc do co tro thanh ung vien hay khong - va nhat la khi
        # no KHONG tro thanh ung vien. Mot he thong khong qua cong van co the co
        # duong dung duoc: Sonic R khong dung duoc don lap nhung EMA34 high/low,
        # EMA89, linreg 89, Hull 377, Donchian 55 thi mang ve lam tham so duoc.
        # Khong ton mot lan tai trang nao: van ban da nam trong tay.
        try:
            tp = THTP.thu_hoi(t["tieu_de"], r["van_ban"], t["url"], t["nguon"])
            thanh_phan_moi += tp["moi"]
        except Exception:
            pass

        try:
            _, created = _noi_dung_artifact(noi_dung_van_tay)
            artifact_moi += int(created)
            artifact_da_co += int(not created)
        except Exception as exc:
            artifact_loi += 1
            SO.ghi_chi_so(
                "seeker_artifact_loi", 1,
                {"url": t["url"][:120], "loi": f"{type(exc).__name__}: {str(exc)[:120]}"})
        doc_duoc += 1
        tong_ky_tu += r["so_ky_tu"]
    tong = SO.mot("SELECT COUNT(*) n, COALESCE(SUM(so_ky_tu),0) k FROM noi_dung "
                  "WHERE kieu != 'khong_doc_duoc'")
    SO.ghi_chi_so("seeker_ky_tu_doc", tong_ky_tu, {"so_ban": doc_duoc})
    return {"doc_duoc": doc_duoc, "that_bai": that_bai, "ky_tu_luot_nay": tong_ky_tu,
            "artifact_moi": artifact_moi, "artifact_da_co": artifact_da_co,
            "artifact_loi": artifact_loi, "cong_cu_moi": cong_cu_moi,
            "thanh_phan_moi": thanh_phan_moi,
            "hoan_lai_loi_tam_thoi": tam_thoi,
            "thu_vien_ban_doc": tong["n"], "thu_vien_ky_tu": tong["k"],
            "thu_vien_trang_a4": round(tong["k"] / 4000)}


# ======================================================================
# TANG 3: BOC. Van ban -> KHANG DINH co so + CO CHE kiem dinh duoc.
# ======================================================================
HE_THONG_BOC = """Ban la tang BOC cua mot phong lab dinh luong. Ban duoc dua NOI DUNG
THAT cua mot tai lieu (toan van bai bao, ma nguon chien luoc, hoac bai dien dan).

Viec cua ban KHONG phai tom tat. Viec cua ban la rut ra thu KIEM DINH DUOC:
mot khang dinh co the SAI, va neu duoc thi mot co che dien dat bang ngu phap.

Ky luat bat buoc:
- CHI dung nhung gi CO TRONG VAN BAN. Moi khang dinh phai kem `trich_dan` la
  cau/doan NGUYEN VAN lay tu van ban. Khong co trich dan = bia dat.
- Con so cong bo trong tai lieu la CUA HO, khong phai cua ta. Ghi lai de sau
  doi chieu khi tai lap, khong duoc coi la bang chung.
- Neu tai lieu khong chua co che giao dich nao (vi du: mot thu vien backtest,
  mot bai ve ha tang) thi noi thang: `khang_dinh: []`. Do la cau tra loi tot.
- Neu co co che nhung NGU PHAP khong dien dat duoc, viet ro thieu toan hang gi
  vao `khong_dien_dat_duoc`. Do la cach ngu phap duoc mo rong."""


def boc_co_che(gioi_han: int = 2, ep: bool = False) -> dict:
    """LEGACY V1: BOC bang LLM; V2 khong goi ham nay tu mot_luot()."""
    ds = SO.nhieu(
        "SELECT n.*, t.tieu_de, t.nguon FROM noi_dung n "
        "LEFT JOIN tai_lieu t ON t.id = n.tai_lieu_id "
        "WHERE n.da_boc = 0 AND n.so_ky_tu > 800 "
        "ORDER BY CASE n.kieu WHEN 'ma_nguon' THEN 0 WHEN 'bai_bao' THEN 1 ELSE 2 END, "
        "n.so_ky_tu DESC LIMIT ?", gioi_han)
    if not ds:
        return {"khong_co_ban_doc_moi": True}

    df_kiem = None
    for ma in ("EURCAD", "AUDNZD", "US500CASH"):
        try:
            d = DL.nap(ma, "H4")
            if len(d) > 3000:
                df_kiem = d
                break
        except Exception:
            continue

    NP.nap_vao_mau()
    da_co = sorted(set(list(MAU.MAU) + [c.get("ten") for c in NP.doc_kho()]))
    da_co_txt = ", ".join(str(x) for x in da_co if x)

    ra = {"da_boc": 0, "khang_dinh": 0, "co_che_nhan": [], "co_che_tu_choi": [],
          "ngu_phap_thieu": []}
    for n in ds:
        nhac = (
            NP_TOM_TAT + "\n\n"
            "== CO CHE THU VIEN DA CO ==\n" + da_co_txt + "\n"
            "KHONG de xuat lai nhung cai tren, ke ca doi ten hay doi tham so. Mot bien\n"
            "the SMA/EMA cat nhau nua la lang phi mot suat ngan sach thong ke. Chi de\n"
            "xuat khi tai lieu cho mot co che THAT SU khac ve BAN CHAT.\n\n"
            "Tra ve JSON:\n"
            '{\n'
            '  "khang_dinh": [ {"cau": "<mot cau co the SAI>",\n'
            '                   "trich_dan": "<NGUYEN VAN tu van ban>",\n'
            '                   "tai_san": "<...>", "khung": "<...>",\n'
            '                   "giai_doan": "<...>",\n'
            '                   "so_cong_bo": {"sharpe": null, "loi_nam_pct": null},\n'
            '                   "dieu_kien_sai": "<quan sat gi thi khang dinh nay sai>"} ],\n'
            '  "co_che": [ <khai bao theo ngu phap tren, hoac de rong> ],\n'
            '  "khong_dien_dat_duoc": "<ngu phap thieu toan hang gi>"\n'
            '}\n\n'
            f"== TAI LIEU: {n['tieu_de'] or ''} ==\n"
            f"nguon: {n['nguon']} | kieu: {n['kieu']} | dia chi: {n['url']}\n\n"
            f"{n['van_ban'][:45000]}")
        kq = TT.hoi_json(nhac, HE_THONG_BOC, bo_qua_han_muc=ep, dung_cache=False)
        j = kq.get("json") or {}
        dong_thong_tin = json.dumps(
            {k: v for k, v in kq.items() if k in ("duong", "loi", "bo_qua")}
            | {"so_khang_dinh": len(j.get("khang_dinh") or []),
               "so_co_che": len(j.get("co_che") or [])}, ensure_ascii=False)[:2000]
        if kq.get("bo_qua"):
            # Han muc LLM: de nguyen tai lieu cho vong sau - KHONG danh dau da boc.
            ra["bo_qua"] = kq["bo_qua"]
            break
        if kq.get("loi"):
            # LOI GOI LLM (mat mang / timeout / chua dang nhap): KHONG an tai lieu.
            # Ghi loi de EVO thay nhung `da_boc` van = 0 de vong sau doc lai.
            SO.chay("UPDATE noi_dung SET ket_boc=? WHERE id=?", dong_thong_tin, n["id"])
            SO.ghi_chi_so("seeker_boc_loi", 1,
                          {"url": str(n["url"])[:120], "loi": str(kq.get("loi"))[:100]})
            continue
        # THANH CONG: LLM tra ve JSON hop le -> danh dau da boc.
        SO.chay("UPDATE noi_dung SET da_boc=1, ket_boc=? WHERE id=?", dong_thong_tin,
                n["id"])
        ra["da_boc"] += 1

        for k in (j.get("khang_dinh") or [])[:6]:
            if not str(k.get("trich_dan") or "").strip():
                continue          # khong trich dan = khong nhan
            SO.chay("INSERT INTO khang_dinh(gt_ma,hang,luc,dieu_kien_sai,trang_thai) "
                    "VALUES(?,?,?,?,'TU_TAI_LIEU')",
                    str(k.get("cau", ""))[:300], n["kieu"], SO.bay_gio(),
                    json.dumps({"trich_dan": str(k.get("trich_dan"))[:600],
                                "so_cong_bo": k.get("so_cong_bo"),
                                "tai_san": k.get("tai_san"), "khung": k.get("khung"),
                                "giai_doan": k.get("giai_doan"),
                                "dieu_kien_sai": k.get("dieu_kien_sai"),
                                "url": n["url"]}, ensure_ascii=False)[:1200])
            ra["khang_dinh"] += 1

        for spec in (j.get("co_che") or [])[:4]:
            if not isinstance(spec, dict):
                continue
            ten = str(spec.get("ten") or "").strip().lower().replace(" ", "_")
            if not ten:
                continue
            spec["ten"] = ten
            spec["nguon"] = n["url"]          # TRUY NGUYEN duoc ve dung tai lieu
            r = NP.them_co_che(spec, df_kiem)
            _ghi_de_xuat(spec, r, n["url"])
            if r["nhan"]:
                ra["co_che_nhan"].append(ten)
                SO.them_viec("QUANTLAB", "kham_pha_theo_mau",
                             {"mau": ten, "nguon_tai_lieu": n["url"]}, uu_tien=2)
            else:
                ra["co_che_tu_choi"].append({"ten": ten, "ly_do": r["ly_do"]})
        if j.get("khong_dien_dat_duoc"):
            ra["ngu_phap_thieu"].append(str(j["khong_dien_dat_duoc"])[:300])

    if ra["ngu_phap_thieu"]:
        SO.bao_van_de(
            "ngu_phap_thieu_toan_hang", "VUA",
            "Tang BOC gap co che ma ngu phap khong dien dat duoc - day la danh sach "
            "toan hang can them vao nhan/ngu_phap.py",
            {"vi_du": ra["ngu_phap_thieu"][:6]})
    if ra["co_che_nhan"]:
        SO.dong_van_de("can_mau_moi",
                       f"tang BOC da rut {len(ra['co_che_nhan'])} co che tu tai lieu that")
    SO.ghi_chi_so("seeker_co_che_tu_tai_lieu", len(ra["co_che_nhan"]),
                  {"da_boc": ra["da_boc"], "khang_dinh": ra["khang_dinh"]})
    return ra


def _ghi_de_xuat(spec: dict, r: dict, nguon: str) -> None:
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT OR IGNORE INTO de_xuat(luc,tru,ten,ho,co_che,dsl,nguon,nhan,"
            "ly_do_tu_choi,trang_thai) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (SO.bay_gio(), TRU, spec.get("ten"), spec.get("ho"),
             (spec.get("co_che") or "")[:600],
             json.dumps(spec, ensure_ascii=False)[:4000], nguon,
             int(bool(r.get("nhan"))), "; ".join(r.get("ly_do") or [])[:600],
             "DA_NHAN" if r.get("nhan") else "TU_CHOI"))


# Ban rut gon cua ngu phap, dat o day de nhac BOC tu chua du - tang BOC khong
# duoc phep phu thuoc vao viec tang NGHI co chay hay khong.
NP_TOM_TAT = """NGU PHAP KHAI BAO CO CHE (chi duoc dung dung nhung khoa nay):
  co_che = {"ten","co_che","ho","chieu":1|-1,"giu":<1..500>,"vao":[dk...],"ra":[dk...]}
  ho     = quay_ve_trung_binh|xu_huong|pha_vo|lich|phien|bien_dong|dong_tien|vi_mo|khac
  dk     = {"trai": th, "phep": "<|<=|>|>=|cheo_len|cheo_xuong", "phai": th}
  th     = {"hang":<so>} | {"chi_bao":"gia","cot":"open|high|low|close"}
         | {"chi_bao":"rsi|atr|ema|sma","n":<so>} | {"chi_bao":"ibs"}
         | {"chi_bao":"bien_do"|"than_nen"|"khoi_luong"}
         | {"chi_bao":"gio"|"ngay_trong_tuan"|"ngay_trong_thang"|"thang"}
         | {"chi_bao":"tb|do_lech|zscore|phan_vi|doi|doi_pct|tre|cao_nhat|thap_nhat|
                       tuyet_doi","cua": th, "n":<so>}
         | {"chi_bao":"tb_cua_cac|cao_nhat_cua_cac|thap_nhat_cua_cac|tong_cua_cac",
            "toan_hang":[th, th, ...]}        // gop mot DAI chi bao, vi du GMMA
  `n` LUON lui ve qua khu - khong co cach nao viet toan hang nhin tuong lai.
  `phan_vi` = thu hang trong N bar gan nhat (0..1); dung no thay cho nguong tuyet doi.
  Ty le kich hoat phai nam trong 0,5%..40% so bar.

VUNG (dung cho FVG / order block / vung cung cau / thanh khoan / ORB / khang cu
ho tro). Mot vung KHONG phai dieu kien tai mot nen: no la vat the SONG QUA
NHIEU NEN, co bien tren, bien duoi, va chet khi bi lap day. Dung `dk` thuong de
dien no la dien SAI.
  dk_vung = {"vung": {"tao":[dk...],        // nen nao SINH ra vung
                      "tren": th, "duoi": th,   // bien, tinh TAI NEN SINH
                      "song": <1..500>,     // song toi da bao nhieu nen
                      "huy": "cham|dong_ngoai|het_han"},
             "quan_he": "cham|trong|bat_len|bat_xuong|xuyen_len|xuyen_xuong"}
  quan_he: `cham` bien do nen phu len vung · `trong` gia dong cua nam trong vung
           `bat_len` cham roi dong cua TREN vung · `bat_xuong` cham roi dong DUOI
           `xuyen_len`/`xuyen_xuong` dong cua vuot han qua sau khi nen truoc con o
  huy:     `cham` lap day mot lan la het (chuan cua FVG/order block)
           `dong_ngoai` chi chet khi gia dong cua ra ngoai · `het_han` het `song` nen

  VI DU - FVG tang (`low[i] > high[i-2]`), vao khi gia quay lai bat len khoi gap:
  {"vung": {"tao": [{"trai": {"chi_bao":"gia","cot":"low"}, "phep": ">",
                     "phai": {"chi_bao":"tre","cua":{"chi_bao":"gia","cot":"high"},"n":2}}],
            "tren": {"chi_bao":"gia","cot":"low"},
            "duoi": {"chi_bao":"tre","cua":{"chi_bao":"gia","cot":"high"},"n":2},
            "song": 20, "huy": "cham"},
   "quan_he": "bat_len"}

  `tao` KHONG duoc de rong: vung se sinh o moi nen va quan he thanh gan nhu luon
  dung. Bien vung tinh bang chinh `th` nen cung khong nhin duoc tuong lai."""


# ----------------------------------------------------------------- MOT LUOT
#: Tien to cua nhung nguon do MODULE KHAC so huu. `dang_ky_nguon` tat moi dong
#: khong nam trong bo cua no - dung cho nguon da go khoi `NGUON`, nhung se tat
#: nham nguon cua module khac.
#:
#: Da sap that 23/08: 27 feed cua `nhan/nguon_bai_viet.py` bi tat het ngay o
#: luot SEEKER ke tiep, va `thu_thap_tat_ca` chi doc dong `trang_thai='BAT'` -
#: nghia la ca tang bai viet van xuoi im lang sau MOT luot, khong bao loi, con
#: so "0 bai moi" nhin y het "chua den han".
TIEN_TO_NGUON_NGOAI = ("rss_", "trang_")


def dang_ky_nguon() -> None:
    tat_ca = set(NGUON) | set(NGUON_TRINH_DUYET) | {"telegram"}
    try:
        from nhan import nguon_bai_viet as NBV
        tat_ca |= {"rss_" + m for m in NBV.FEEDS}
        tat_ca |= {"trang_" + m for m in NBV.TRANG}
    except Exception:
        pass
    with SO.ket_noi() as cn:
        # Telegram (session that), khong can CDP
        cn.execute(
            "INSERT INTO nguon(ma,ten,loai,url,lay_gi,chu_ky_giay,uu_tien,trang_thai) "
            "VALUES('telegram','telegram','social','','',21600,2,'BAT') "
            "ON CONFLICT(ma) DO UPDATE SET chu_ky_giay=21600, uu_tien=2, trang_thai='BAT'")
        for ma, c in list(NGUON.items()) + [
                (m, {"loai": NGUON_TRINH_DUYET[m]["loai"],
                     "chu_ky": NGUON_TRINH_DUYET[m]["chu_ky"],
                     "uu_tien": NGUON_TRINH_DUYET[m]["uu_tien"]})
                for m in NGUON_TRINH_DUYET]:
            cn.execute(
                "INSERT INTO nguon(ma,ten,loai,url,lay_gi,chu_ky_giay,uu_tien,trang_thai) "
                "VALUES(?,?,?,?,?,?,?,'BAT') ON CONFLICT(ma) DO UPDATE SET "
                "chu_ky_giay=excluded.chu_ky_giay, uu_tien=excluded.uu_tien, "
                "trang_thai='BAT'",
                (ma, ma, c["loai"], "", "", c["chu_ky"], c["uu_tien"]))
        # Nguon da go khoi bo -> tat, khong xoa (giu lich su thu hoach).
        # Nhung KHONG dung toi nguon cua module khac: cai gi minh khong dang ky
        # thi minh cung khong duoc tat.
        cn.execute(
            "UPDATE nguon SET trang_thai='TAT' WHERE ma NOT IN (%s) AND %s"
            % (",".join("?" * len(tat_ca)),
               " AND ".join("ma NOT LIKE ?" for _ in TIEN_TO_NGUON_NGOAI)),
            tuple(sorted(tat_ca)) + tuple(t + "%" for t in TIEN_TO_NGUON_NGOAI))
    # Mon no cua nguon trinh duyet duoc danh gia DONG trong quet_trinh_duyet()


def nguon_den_han() -> list[str]:
    now = time.time()
    ra = []
    for r in SO.nhieu("SELECT * FROM nguon WHERE trang_thai='BAT' ORDER BY uu_tien"):
        if r["ma"] not in NGUON:
            continue
        # nguon loi lien tuc -> gian chu ky theo cap so nhan (cach ly, khong xoa)
        he_so = 2 ** min(r["loi_lien_tuc"] or 0, 5)
        if now - (r["lan_cuoi"] or 0) >= (r["chu_ky_giay"] or 21600) * he_so:
            ra.append(r["ma"])
    return ra


def mot_luot(ngan_sach_giay: int = 600) -> dict:
    t0 = time.time()
    SO.nhip_tim(TRU, "chay")
    khoi_tao_tu_khoa()
    dang_ky_nguon()

    # ---------------- TANG 1: THU (chi khi co nguon den han) ----------------
    den_han = nguon_den_han()
    tk = tu_khoa_dung(6)
    tong_moi, chi_tiet = 0, []
    for ma in den_han:
        if time.time() - t0 > ngan_sach_giay * 0.45:
            break
        c = NGUON[ma]
        try:
            ds = c["ham"](tk)
            moi = luu_tai_lieu(ma, ds)
            tong_moi += moi
            them_tk = mo_rong_tu_khoa(ds)
            SO.chay("UPDATE nguon SET lan_cuoi=?, so_lan=so_lan+1, loi_lien_tuc=0, "
                    "thu_hoach=thu_hoach+? WHERE ma=?", time.time(), moi, ma)
            chi_tiet.append({"nguon": ma, "lay_ve": len(ds), "moi": moi, "tu_khoa_moi": them_tk})
        except Exception as e:
            SO.chay("UPDATE nguon SET lan_cuoi=?, so_loi=so_loi+1, "
                    "loi_lien_tuc=loi_lien_tuc+1, ghi_chu=? WHERE ma=?",
                    time.time(), f"{type(e).__name__}: {str(e)[:100]}", ma)
            chi_tiet.append({"nguon": ma, "loi": str(e)[:80]})

    if den_han:
        # cham diem tu khoa theo NANG SUAT
        with SO.ket_noi() as cn:
            for t in tk:
                cn.execute("UPDATE tu_khoa SET so_lan_dung=so_lan_dung+1, "
                           "so_ket_qua=so_ket_qua+? WHERE tu=?",
                           (tong_moi // max(len(tk), 1), t))

    # ---- TANG 1b: NGUON QUA TRINH DUYET (chi khi con Chrome CDP dang mo) ----
    trinh_duyet = quet_trinh_duyet(ngan_sach_giay=int(ngan_sach_giay * 0.2), t0=t0)

    # ---- TANG 1c: TELEGRAM follow (session that, khong can CDP) ----
    telegram = {}
    tr = SO.mot("SELECT * FROM nguon WHERE ma='telegram'")
    if tr and tr["trang_thai"] == "BAT":
        he_so_tg = 2 ** min(tr["loi_lien_tuc"] or 0, 5)
        if time.time() - (tr["lan_cuoi"] or 0) >= (tr["chu_ky_giay"] or 21600) * he_so_tg:
            telegram = quet_telegram_follow(
                toi_da_kenh=12, so_bai_moi_kenh=6,
                ngan_sach_giay=int(ngan_sach_giay * 0.25), t0=t0)
            if telegram.get("loi"):
                SO.chay("UPDATE nguon SET loi_lien_tuc=loi_lien_tuc+1, "
                        "ghi_chu=? WHERE ma='telegram'", str(telegram["loi"])[:100])
            else:
                SO.chay("UPDATE nguon SET lan_cuoi=?, so_lan=so_lan+1, "
                        "loi_lien_tuc=0, thu_hoach=thu_hoach+? WHERE ma='telegram'",
                        time.time(), telegram.get("tin_moi", 0))

    # ---- TANG 2 chay BAT KE co nguon den han hay khong ---------------------
    # Truoc 16/08, khong co nguon den han la SEEKER thoat ngay (`khong_co_nguon_
    # den_han`) du trong so co 396 tai lieu chua ai doc va KHONG MOT ban toan van
    # nao. Do la ly do no chay 1,4 giay mot luot va nhin nhu mot vong lap rong -
    # ma thuc ra la mot phong doc chua bao gio mo sach.
    ban_doc = doc_toan_van(gioi_han=10,
                           ngan_sach_giay=max(60, int(ngan_sach_giay * 0.35)))
    backfill = backfill_document_artifacts(gioi_han=500)

    # ---- TANG 1d: MA NGUON EA/CHI BAO -> CodeArtifact ---------------------
    # Van xuoi mo ta co che bang tieng nguoi, va tieng nguoi mo ho o dung cho
    # quan trong nhat: "mua khi RSI thap" khong noi nguong bao nhieu, khung nao,
    # giu bao lau. Mot file `.mq5` thi noi het, va no la thu DA CHAY THAT.
    # KHONG BAO GIO chay ma tai ve - xem `nhan/ma_nguon.py`.
    ma_nguon = {}
    mn = SO.mot("SELECT * FROM nguon WHERE ma='mql5_ma_nguon'")
    can_ma = (mn is None) or (
        (mn["trang_thai"] or "BAT") == "BAT"
        and time.time() - (mn["lan_cuoi"] or 0) >= (mn["chu_ky_giay"] or 43200))
    if can_ma and time.time() - t0 < ngan_sach_giay * 0.9:
        try:
            from nhan import ma_nguon as MANG
            ma_nguon = MANG.thu_thap(so_bai=8)
            SO.chay("INSERT INTO nguon(ma,ten,chu_ky_giay,lan_cuoi,so_lan,thu_hoach) "
                    "VALUES('mql5_ma_nguon','MQL5 Code Base (.mq5)',43200,?,1,?) "
                    "ON CONFLICT(ma) DO UPDATE SET lan_cuoi=excluded.lan_cuoi, "
                    "so_lan=so_lan+1, loi_lien_tuc=0, "
                    "thu_hoach=thu_hoach+excluded.thu_hoach",
                    time.time(), ma_nguon.get("ghi_moi", 0))
        except Exception as e:
            ma_nguon = {"loi": f"{type(e).__name__}: {str(e)[:100]}"}

    # ---- TANG 1e: HAI LAN DAU VAO, chia gio theo SUAT DO DUOC ------------
    # Lan 1 `hoc_thuat`: feed/API - noi nguoi ta VIET LUAT.
    # Lan 2 `xa_hoi`: dien dan/mang xa hoi qua con browser - noi nguoi ta KE.
    #
    # Khong chia cung 50/50 va cung khong bo han lan nao: `nhan/vuon_nguon.py`
    # do suat that (ung vien tren 100 bai) roi chia gio theo do, nhung moi lan
    # luon duoc it nhat 15% de con co co hoi chung minh nguoc lai. Do 23/08:
    # hoc_thuat 18,7 ung vien/100 bai, xa_hoi 0.
    bai_viet, browser, vuon = {}, {}, {}
    con_lai = ngan_sach_giay - (time.time() - t0)
    if con_lai > 30:
        try:
            from nhan import vuon_nguon as VN
            chia = VN.chia_ngan_sach(min(con_lai * 0.55, ngan_sach_giay * 0.45))
        except Exception as e:
            chia = {"hoc_thuat": con_lai * 0.25, "xa_hoi": con_lai * 0.05}
            vuon = {"loi": f"{type(e).__name__}: {str(e)[:80]}"}

        # --- LAN 1: bai viet van xuoi qua RSS/Atom ---
        try:
            from nhan import nguon_bai_viet as NBV
            bai_viet = NBV.thu_thap_tat_ca(
                gioi_han_nguon=4, so_bai=12,
                ngan_sach_giay=max(30, int(chia.get("hoc_thuat", 60))))
        except Exception as e:
            bai_viet = {"loi": f"{type(e).__name__}: {str(e)[:100]}"}

        # --- LAN 2: kho cua con browser, qua CONG chat luong ---
        # Cong o `nhan/cau_browser.py`, khong o day: SEEKER khong duoc tu dinh
        # nghia the nao la mot bai dung doc.
        try:
            from nhan import cau_browser as CB
            browser = CB.mot_luot(gioi_han=200)
        except Exception as e:
            browser = {"loi": f"{type(e).__name__}: {str(e)[:100]}"}

        # --- TU MO RONG: tim nguon moi + soat lai nguon dang tham do ---
        try:
            from nhan import vuon_nguon as VN
            vuon = {"soat_lai": VN.soat_lai()}
            if time.time() - t0 < ngan_sach_giay * 0.75:
                vuon["tim"] = VN.mot_luot_tim(
                    so_mien=4, so_ten_thu_muc=6,
                    ngan_sach_giay=max(30, int(chia.get("hoc_thuat", 60) * 0.5)))
            vuon["suat"] = VN.suat_lan()
            vuon["chia_giay"] = chia
        except Exception as e:
            vuon = {"loi": f"{type(e).__name__}: {str(e)[:100]}"}

    # Tai lieu moi phai thanh artifact NGAY trong luot nay, neu khong bo bien
    # dich ben duoi doc kho cu va con so "bai moi" nhin nhu khong dan toi gi.
    if bai_viet.get("ban_doc_moi") or browser.get("nhan"):
        backfill = backfill_document_artifacts(gioi_han=500)

    # V2: SEEKER dung tai artifact. BOC/LLM, suy luan co che va xep backtest la
    # viec cua NGHI/QUANTLAB. Giu gia tri tuong thich trong output, khong goi legacy.
    boc = {"legacy_disabled": True}

    # CAU NOI SANG QUANTLAB. Truoc day cho nay la mot cho trong ghi cung
    # "xep_viec": 0, nen 156 DocumentArtifact nam mai o SEEKER va
    # `candidate_queue` dung im o 0 dong - day chuyen dut o dung day.
    #
    # Bo bien dich CHI duoc chon mot mau da co trong thu vien, khong duoc sinh
    # bieu thuc hay ma. Xem `nhan/bien_dich_ung_vien.py`.
    try:
        from nhan import bien_dich_ung_vien as BDUV
        cau_noi = BDUV.mot_luot()
    except Exception as e:
        cau_noi = {"loi": f"{type(e).__name__}: {str(e)[:120]}"}
    cau_noi["che_do"] = "artifact_contract"
    # BAT BIEN: SEEKER xep UNG VIEN, tuyet doi khong xep VIEC backtest. Viec la
    # do QUANTLAB tu rut hang doi ma tao. Giu con so nay bang 0 de mot lan sua
    # sai kien truc lo ra ngay o bao cao thay vi chim trong log.
    cau_noi["xep_viec"] = 0

    tong = SO.mot("SELECT COUNT(*) n FROM tai_lieu")["n"]
    hang = {r["tu_khoa"]: r["n"] for r in SO.nhieu(
        "SELECT tu_khoa, COUNT(*) n FROM tai_lieu GROUP BY tu_khoa")}
    SO.ghi_chi_so("seeker_tai_lieu_moi", tong_moi)

    # Con viec o tang DOC/artifact thi khong duoc ngu dai - hen lai som.
    con_doc = SO.mot(
        "SELECT COUNT(*) n FROM tai_lieu t LEFT JOIN noi_dung nd ON nd.tai_lieu_id=t.id "
        "WHERE nd.id IS NULL AND t.url LIKE 'http%' AND t.tu_khoa IN('A','B')")["n"]
    con_boc = 0
    con_artifact = int(backfill.get("con_lai") or 0)
    ke = SO.mot("SELECT MIN(lan_cuoi + chu_ky_giay) t FROM nguon WHERE trang_thai='BAT'")
    cho_nguon = max(60, int((ke["t"] or 0) - time.time())) if ke and ke["t"] else 900
    cho = 120 if (con_doc or con_artifact) else min(cho_nguon, 3600)
    SO.nhip_tim(TRU, "nghi", {"moi": tong_moi, "tong": tong, "cho_giay": cho,
                              "con_doc": con_doc, "con_artifact": con_artifact})

    # nguon chet lau -> bao EVO
    chet = SO.nhieu("SELECT ma, loi_lien_tuc, ghi_chu FROM nguon WHERE loi_lien_tuc>=3")
    if chet:
        SO.bao_van_de("nguon_chet", "VUA",
                      f"{len(chet)} nguon loi lien tuc >= 3 lan, dang bi gian chu ky",
                      {"nguon": [dict(c) for c in chet]})
    else:
        SO.dong_van_de("nguon_chet", "cac nguon da tra ve binh thuong")

    viet_bao_cao(den_han, tong_moi, tong, hang, ban_doc, backfill, con_doc)
    return {"nguon_da_quet": den_han, "tai_lieu_moi": tong_moi, "tong_tai_lieu": tong,
            "theo_hang": hang, "tu_khoa_dung": tk, "cau_noi_quantlab": cau_noi,
            "DOC": ban_doc, "BOC": boc, "trinh_duyet": trinh_duyet,
            "telegram": telegram, "artifact_backfill": backfill,
            "ma_nguon": ma_nguon, "bai_viet": bai_viet,
            "browser": browser, "vuon_nguon": vuon,
            "con_doc": con_doc, "con_boc": con_boc,
            "cho_giay": cho, "chi_tiet": chi_tiet}


def viet_bao_cao(den_han, tong_moi, tong, hang, ban_doc, backfill, con_doc) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    artifacts = {r["artifact_type"]: r["n"] for r in SO.nhieu(
        "SELECT artifact_type,COUNT(*) n FROM artifact GROUP BY artifact_type")}
    queued = SO.mot("SELECT COUNT(*) n FROM candidate_queue")["n"]
    kieu = SO.nhieu("SELECT kieu, COUNT(*) n, COALESCE(SUM(so_ky_tu),0) k "
                    "FROM noi_dung GROUP BY kieu ORDER BY k DESC")
    d = ["# SEEKER V2 - funnel thu thap va truy nguyen", f"*{SO.bay_gio()}*", "",
         "## 1. Thu vien THAT SU co gi", "",
         "| Kieu ban doc | So ban | Ky tu | ~trang A4 |", "|---|---|---|---|"]
    for k in kieu:
        d.append(f"| {k['kieu']} | {k['n']} | {k['k']:,} | {round(k['k']/4000)} |")
    tongk = sum(k["k"] for k in kieu)
    d += [f"| **TONG** | **{sum(k['n'] for k in kieu)}** | **{tongk:,}** | "
          f"**{round(tongk/4000)}** |", "",
          f"- Muc luc: {tong} tai lieu ({json.dumps(hang, ensure_ascii=False)})",
          f"- DocumentArtifact bat bien: **{artifacts.get('document', 0)}**",
          f"- Con cho DOC: **{con_doc}** | con cho artifact backfill: "
          f"**{backfill.get('con_lai', 0)}**", "",
          "> Truoc 16/08 cot 'ky tu' nay la **0**: he chi luu tieu de va tom tat "
          "(456 ban ghi = 51 trang A4), va mot repo 22.851 sao nam trong so voi "
          "dung 49 ky tu mo ta.", "",
          "## 2. Luot nay",
          f"- Nguon da quet: {den_han or 'khong co nguon den han (van DOC/backfill)'}",
          f"- Tai lieu moi: {tong_moi}",
          f"- Ban doc keo ve: {ban_doc.get('doc_duoc', 0)} "
          f"({ban_doc.get('ky_tu_luot_nay', 0):,} ky tu), that bai {ban_doc.get('that_bai', 0)}",
          f"- Artifact tu DOC: moi {ban_doc.get('artifact_moi', 0)}, "
          f"da co {ban_doc.get('artifact_da_co', 0)}, loi {ban_doc.get('artifact_loi', 0)}",
          f"- Backfill: xem {backfill.get('da_xem', 0)}, moi {backfill.get('artifact_moi', 0)}, "
          f"da co {backfill.get('artifact_da_co', 0)}, bo qua {backfill.get('bo_qua', 0)}",
          "", "## 3. Bien gioi V2",
          "- SEEKER khong goi LLM/BOC, khong sinh co che va khong xep backtest.",
          "- Dau ra cua SEEKER la artifact da chuan hoa, co fingerprint va provenance.",
          f"- Candidate dang cho Quantlab: **{queued}** (do tang phan tich tao, khong phai SEEKER)."]
    if backfill.get("loi"):
        d += ["", f"- **Loi backfill:** {backfill['loi']}"]
    (REPORTS / "SEEKER.md").write_text("\n".join(d), encoding="utf-8")


if __name__ == "__main__":
    SO.khoi_tao()
    print(json.dumps(mot_luot(), ensure_ascii=False, indent=1)[:5000])
