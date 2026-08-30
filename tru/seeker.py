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
                  san_cong_cu as SCC, so as SO, toan_van as TV, tri_tue as TT)

TRU = "SEEKER"
REPORTS = Path(__file__).resolve().parent.parent / "reports"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

TU_KHOA_GOC = [
    "trading strategy backtest", "momentum factor", "mean reversion equity",
    "statistical arbitrage", "market microstructure", "volatility risk premium",
    "trend following managed futures", "pairs trading cointegration",
    "intraday seasonality", "order flow imbalance", "expert advisor mql5",
    "algorithmic trading python", "portfolio optimization robust",
    "overfitting backtest deflated sharpe", "regime switching model",
]


def _lay(url: str, timeout: int = 25) -> str | None:
    try:
        import requests
        r = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None


def _sach(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


# ------------------------------------------------------------------- NGUON
def n_arxiv(tu_khoa: list[str]) -> list[dict]:
    """arXiv q-fin. HANG B: cong trinh co phuong phap viet ra."""
    ra = []
    truy_van = ["cat:q-fin.ST", "cat:q-fin.PM", "cat:q-fin.TR", "cat:q-fin.CP"]
    truy_van += [f'all:"{t}"' for t in tu_khoa[:3]]
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


def n_github(tu_khoa: list[str]) -> list[dict]:
    """GitHub. HANG A khi repo co CODE CHAY DUOC - ta backtest lai duoc ngay."""
    ra = []
    for t in tu_khoa[:3]:
        u = ("https://api.github.com/search/repositories?q=" +
             t.replace(" ", "+") + "+language:python&sort=stars&order=desc&per_page=20")
        txt = _lay(u)
        if not txt:
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
    return ra


def n_openalex(tu_khoa: list[str]) -> list[dict]:
    """OpenAlex - kho cong trinh mo, khong can khoa. Thay cho SSRN (bi SSL chan)."""
    ra = []
    for t in tu_khoa[:3]:
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
    for t in tu_khoa[:2]:
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
    for t in tu_khoa[:2]:
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


def n_mql5_code(tu_khoa: list[str]) -> list[dict]:
    """Kho ma MQL5 - EA/chi bao that dang chay tren MT5.

    Ghi chu cu bao "mql5 render bang JS" la noi ve trang SIGNALS. Trang
    /en/code tra HTML tho co link (do that 16/08: 200, 20.942 ky tu van ban).
    """
    ra, da = [], set()
    for muc in ("experts", "indicators"):
        txt = _lay(f"https://www.mql5.com/en/code/mt5/{muc}", timeout=30)
        if not txt:
            continue
        # HREF TUONG DOI. Ban truoc doi `href="https://www.mql5.com/en/code/123"`
        # nhung trang that dung `href="/en/code/76331"`, nen regex khop 0/40 va
        # ham tra ve rong SUOT - khong loi, khong canh bao. Doi chieu 22/08:
        # trang 82.894 ky tu, 40 link tuong doi, 0 link tuyet doi.
        for m in re.finditer(
                r'href="(?:https://www\.mql5\.com)?(/en/code/\d+)"[^>]*>(.*?)</a>',
                txt, re.S | re.I):
            u, tt = "https://www.mql5.com" + m.group(1), _sach(m.group(2))
            if len(tt) < 10 or u in da:
                continue
            da.add(u)
            ra.append({"tieu_de": f"[MQL5 {muc}] {tt[:200]}", "url": u,
                       "tom_tat": "", "hang": "B", "loai": "ma_nguon"})
        time.sleep(1.5)
    return ra[:30]


def n_crossref(tu_khoa: list[str]) -> list[dict]:
    """Crossref - muc luc cong trinh co DOI. Dung de bat bai KHONG co tren arXiv."""
    ra = []
    for t in tu_khoa[:2]:
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
    for t in tu_khoa[:2]:
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
    "arxiv":         {"ham": n_arxiv, "chu_ky": 21600, "uu_tien": 2, "loai": "hoc_thuat"},
    "github":        {"ham": n_github, "chu_ky": 43200, "uu_tien": 1, "loai": "ma_nguon"},
    "openalex":      {"ham": n_openalex, "chu_ky": 43200, "uu_tien": 2, "loai": "hoc_thuat"},
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
    "x":            {"kieu": "tu_khoa", "mau": "https://x.com/search?q={k}&f=live",
                     "hang": "B", "loai": "social", "chu_ky": 21600, "uu_tien": 3},
    "tiktok":       {"kieu": "tu_khoa", "mau": "https://www.tiktok.com/search/video?q={k}",
                     "hang": "B", "loai": "social", "chu_ky": 21600, "uu_tien": 3},
    "facebook":     {"kieu": "tu_khoa", "mau": "https://www.facebook.com/search/posts?q={k}",
                     "hang": "B", "loai": "social", "chu_ky": 21600, "uu_tien": 3},
    "youtube":      {"kieu": "tu_khoa", "mau": "https://www.youtube.com/results?search_query={k}",
                     "hang": "B", "loai": "video", "chu_ky": 43200, "uu_tien": 3},
}


def _duyet_tai_lieu(d: dict, nguon: str, c: dict, tu_khoa: str = "") -> list[dict]:
    """Nhat ung vien (link+tieu de that) tu trang doc duoc qua trinh duyet.

    `kieu=tu_khoa`: giu nguyen text trang tim kiem lam mot bai (giogn doc_cdp ).
    `kieu=trang`: boc anchor; neu khong co anchor rao ra thi giu ca trang text."""
    if c.get("kieu") == "tu_khoa":
        ct = (d.get("text") or "").strip()
        if len(ct) < 40:
            return []
        return [{"tieu_de": f"[{nguon}] {tu_khoa or (d.get('title') or 'tim kiem')}",
                 "url": d.get("url") or "", "tom_tat": ct[:900],
                 "hang": c.get("hang", "B"), "loai": c.get("loai", "")}]
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
    for r in SO.nhieu("SELECT * FROM nguon WHERE trang_thai='BAT'"):
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
        if c.get("kieu") == "tu_khoa":
            phieu = [_ur.quote(k) for k in tu_khoa_dung(3)]
            phieu = [c["mau"].replace("{k}", q) for q in phieu]
        else:
            phieu = c["trang"]
        tong_moi, loi_td = 0, []
        try:
            for u in phieu:
                d = DT.doc_gan(u, port=port)
                if d.get("loi"):
                    loi_td.append(str(d["loi"])[:60])
                    continue
                ds = _duyet_tai_lieu(d, ma, c, tu_khoa=u)
                if ds:
                    tong_moi += luu_tai_lieu(ma, ds)
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


def doc_toan_van(gioi_han: int = 8, ngan_sach_giay: int = 240) -> dict:
    """Keo toan van / ma nguon cua tai lieu hang A-B chua co ban doc.

    Do 16/08 truoc khi co tang nay: ca kho tai lieu la 456 ban ghi / 202.760 ky
    tu = 51 trang A4, va do chi la tieu de + tom tat. Mot repo 22.851 sao nam
    trong so voi dung 49 ky tu mo ta. Khong the nghien cuu tu 49 ky tu.
    """
    t0 = time.time()
    ds = SO.nhieu(
        "SELECT t.id, t.tieu_de, t.url, t.tu_khoa, t.nguon, t.diem FROM tai_lieu t "
        "LEFT JOIN noi_dung n ON n.tai_lieu_id = t.id "
        "WHERE n.id IS NULL AND t.url LIKE 'http%' AND t.tu_khoa IN('A','B') "
        "ORDER BY CASE t.tu_khoa WHEN 'A' THEN 0 ELSE 1 END, t.diem DESC, t.id DESC "
        "LIMIT ?", gioi_han * 3)
    doc_duoc, that_bai, tong_ky_tu = 0, 0, 0
    cong_cu_moi = 0
    tam_thoi = 0
    artifact_moi, artifact_da_co, artifact_loi = 0, 0, 0
    for t in ds:
        if doc_duoc >= gioi_han or time.time() - t0 > ngan_sach_giay:
            break
        try:
            r = TV.doc(t["url"])
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
  Ty le kich hoat phai nam trong 0,5%..40% so bar."""


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
