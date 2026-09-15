# -*- coding: utf-8 -*-
"""toan_van.py - TANG DOC. Lay NOI DUNG THAT chu khong phai dong tieu de.

VAN DE NO GIAI (do tren so cai 16/08):

    Toan bo "thu vien" cua The Brain = 456 ban ghi, 202.760 ky tu = ~51 trang A4.
    Va do chi la tieu de + tom tat. Vi du mot tai lieu HANG A diem cao nhat:

        [github 5.0] [22851*] mementum/backtrader
        noi dung (49 ky tu): "Python Backtesting library for trading strategies"

    49 ky tu. Khong mot dong ma nao. SEEKER khong DOC - no LIET KE. No la mot bo
    suu tam ket qua tim kiem, khong phai mot phong doc. Va vi vay moi co che ma
    tang NGHI de xuat that ra den tu kien thuc san co cua LLM chu khong tu kho
    tai lieu (`de_xuat.nguon` rong o ca 18 ban ghi dau tien).

DO THAT NGAY 16/08 - dung cai duong nay co mo:
    arXiv PDF          886.446 byte -> 841.439 ky tu van ban  (so voi 886 ky tu tom tat)
    GitHub raw 1 file   24.586 byte ->  24.585 ky tu MA THAT  (so voi 49 ky tu mo ta)
    Lean Algorithm.Python                511.157 ky tu ma chien luoc that
    QuantConnect forum                   107.506 ky tu thao luan
    MQL5 code base                        20.942 ky tu

Nguyen tac:
  1. Moi kieu nguon co bo boc RIENG. Boc HTML tho cho mot file PDF ra rac.
  2. Cat theo NGAN SACH KY TU, khong nap vo han - mot bai 841k ky tu nhet ca
     vao nhac LLM la vua dot tien vua lam loang cai can doc.
  3. Ma nguon uu tien file CO KHA NANG chua chien luoc, khong lay ca repo.
  4. Luon giu `url` va `kieu` de sau nay truy nguoc duoc mot khang dinh ve dung
     doan van sinh ra no.
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from pathlib import Path

UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
      "Accept": "text/html,application/xhtml+xml,application/json,*/*"}

NGAN_SACH_KY_TU = {"bai_bao": 60_000, "ma_nguon": 90_000, "dien_dan": 40_000,
                   "blog": 25_000, "video": 45_000, "khac": 25_000}

# Ten file co kha nang chua LOGIC CHIEN LUOC. Lay ca repo la nap ca test,
# setup.py, docs - ton ngan sach ma khong mang thong tin co che nao.
UU_TIEN_MA = re.compile(
    r"(strateg|signal|indicator|alpha|factor|momentum|revers|breakout|pairs|"
    r"arbitrag|backtest|algo|model|entry|exit|rule)", re.I)
DUOI_MA = (".py", ".mq5", ".mq4", ".pine", ".ipynb", ".r", ".jl")
BO_QUA_MA = re.compile(r"(test|__init__|setup|conftest|/docs?/|example.*plot|_plotting)", re.I)


def _lay(url: str, timeout: int = 30, nhi_phan: bool = False):
    import requests
    h = dict(UA)
    # TOKEN GITHUB nang han muc API tu 60 luot/GIO len 5.000. `tu_github` an
    # mot luot API moi repo de liet ke file, nen khong token thi 1.013 repo
    # lien quan trong kho = 17 gio.
    if "github.com" in url or "githubusercontent.com" in url:
        try:
            from nhan import bi_mat as _BM
            h.update(_BM.dau_github())
        except Exception:
            pass
    try:
        r = requests.get(url, timeout=timeout, headers=h)
        if r.status_code != 200:
            return None
        return r.content if nhi_phan else r.text
    except Exception:
        return None


def _sach(vb: str) -> str:
    vb = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", vb or "", flags=re.S | re.I)
    vb = re.sub(r"<[^>]+>", " ", vb)
    from html import unescape
    return re.sub(r"[ \t\r\f\v]+", " ", unescape(vb)).strip()


# ------------------------------------------------------------------ ARXIV
_ID_ARXIV = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})", re.I)


def tu_arxiv(url: str) -> dict | None:
    """Toan van bai arXiv. PDF truoc (luon co), ar5iv sau (chi co khi co LaTeX).

    Ban tom tat hien nay la 886 ky tu; ban nay ra ~40-60k ky tu, trong do co
    phan PHUONG PHAP va BANG KET QUA - dung hai thu quyet dinh viec co tai lap
    duoc hay khong.
    """
    m = _ID_ARXIV.search(url or "")
    if not m:
        return None
    ma = m.group(1)
    b = _lay(f"https://arxiv.org/pdf/{ma}", timeout=45, nhi_phan=True)
    if b and b[:5] == b"%PDF-":
        try:
            import logging
            import pypdf
            # pypdf keu "Ignoring wrong pointing object ..." hang chuc dong cho
            # moi PDF. Chay 24/7 thi do la rac lam ngap log dieu phoi.
            logging.getLogger("pypdf").setLevel(logging.ERROR)
            doc = pypdf.PdfReader(io.BytesIO(b), strict=False)
            phan = []
            for tr in doc.pages[:40]:
                try:
                    phan.append(tr.extract_text() or "")
                except Exception:
                    continue
            vb = re.sub(r"[ \t]+", " ", "\n".join(phan)).strip()
            if len(vb) > 800:
                return {"van_ban": vb, "kieu": "bai_bao", "cach": f"arxiv_pdf:{ma}",
                        "so_trang": len(doc.pages)}
        except Exception:
            pass
    h = _lay(f"https://ar5iv.labs.arxiv.org/html/{ma}", timeout=45)
    if h:
        vb = _sach(h)
        if len(vb) > 800:
            return {"van_ban": vb, "kieu": "bai_bao", "cach": f"ar5iv:{ma}"}
    return None


# ----------------------------------------------------------------- GITHUB
_REPO = re.compile(r"github\.com/([^/\s]+)/([^/\s#?]+)", re.I)


def tu_github(url: str, so_file: int = 6) -> dict | None:
    """MA CHIEN LUOC THAT tu mot repo.

    Lay cay thu muc roi chon file CO KHA NANG chua logic chien luoc. Day la thu
    du an van thieu: memory `quet-rong-tham-khao-nguoi-khac` ghi ro "khong co
    code ngoai lam nguon logic thi khong tao duoc he thong" - ma cho toi 16/08
    kho tai lieu chi co MO TA repo (trung binh 164 ky tu), khong co dong ma nao.
    """
    m = _REPO.search(url or "")
    if not m:
        return None
    chu, repo = m.group(1), m.group(2).replace(".git", "")

    # Dia chi tro thang vao MOT FILE (`/blob/<nhanh>/<duong dan>`) - lay dung file
    # do. Khong co nhanh nay thi mot link file cua Lean se keo ve ca cay thu muc
    # 2.700 muc cua repo Lean, moi lan mot lan.
    mb = re.search(r"github\.com/[^/]+/[^/]+/blob/([^/]+)/(.+)$", url, re.I)
    if mb:
        nhanh, duong = mb.group(1), mb.group(2).split("#")[0].split("?")[0]
        ma = _lay(f"https://raw.githubusercontent.com/{chu}/{repo}/{nhanh}/{duong}")
        if ma and len(ma) > 300:
            return {"van_ban": f"########## {duong}\n{ma}", "kieu": "ma_nguon",
                    "cach": f"github_file:{chu}/{repo}/{duong}", "file": [duong]}
        return None
    cay = None
    for nhanh in ("HEAD", "main", "master"):
        t = _lay(f"https://api.github.com/repos/{chu}/{repo}/git/trees/{nhanh}?recursive=1")
        if t:
            try:
                d = json.loads(t)
                if d.get("tree"):
                    cay = d["tree"]
                    break
            except Exception:
                continue
        time.sleep(0.6)
    if not cay:
        return None

    ung = [x for x in cay
           if x.get("type") == "blob"
           and str(x.get("path", "")).lower().endswith(DUOI_MA)
           and 400 < int(x.get("size") or 0) < 250_000
           and not BO_QUA_MA.search(x["path"])]
    # file co ten goi y chien luoc len truoc, roi den file to nhat (thuong la loi)
    ung.sort(key=lambda x: (0 if UU_TIEN_MA.search(x["path"]) else 1, -int(x.get("size") or 0)))
    if not ung:
        return None

    phan, lay_duoc = [], []
    for x in ung[:so_file]:
        for nhanh in ("HEAD", "main", "master"):
            ma = _lay(f"https://raw.githubusercontent.com/{chu}/{repo}/{nhanh}/{x['path']}")
            if ma:
                phan.append(f"\n########## {x['path']} ({x.get('size')} byte)\n{ma}")
                lay_duoc.append(x["path"])
                break
        time.sleep(0.4)
        if sum(len(p) for p in phan) > NGAN_SACH_KY_TU["ma_nguon"]:
            break
    if not phan:
        return None
    return {"van_ban": "".join(phan), "kieu": "ma_nguon",
            "cach": f"github:{chu}/{repo}", "file": lay_duoc,
            "tong_file_ma": len(ung)}


# -------------------------------------------------------- DIEN DAN / BLOG
def tu_html(url: str, kieu: str = "khac") -> dict | None:
    h = _lay(url, timeout=35)
    if not h:
        return None
    # trang dien dan/blog thuong co phan noi dung trong <article>/<div class=post>
    khoi = re.findall(r"<(?:article|main)\b[^>]*>(.*?)</(?:article|main)>", h, re.S | re.I)
    vb = _sach(" ".join(khoi)) if khoi else ""
    # VO <main> RONG KHONG DUOC NUOT CA TRANG (sua 12/09/2026).
    #
    # Truoc hom nay cau tren la `" ".join(khoi) if khoi else h`: he chon khoi
    # <article>/<main> NEU CO, va khong bao gio hoi lai xem khoi do co chu hay
    # khong. Voi trang dung khung React/Next thi the <main> thuong la mot vo
    # rong, noi dung duoc dung vao cho khac.
    #
    # Do that 12/09/2026 tren `fxblue.com/tools-for-download/fx-blue-trading-
    # simulator/user-guide/metaTrader4`: trang 501.856 byte, **1 khoi <main>
    # dai 503 byte va boc ra DUNG 0 ky tu chu**, trong khi ca trang boc ra
    # **32.594 ky tu**. Nguong `len(vb) < 400` ben duoi bien 32.594 ky tu do
    # thanh mot chu "khong doc duoc" - va `doc_toan_van` ghi nhan ay VINH VIEN.
    #
    # Nen: khoi chi duoc dung khi no THAT SU co chu; khong thi lui ve ca trang.
    # Day khong phai loi rieng cua fxblue - moi trang dung SPA shell deu roi
    # vao day.
    if len(vb) < 400:
        vb = _sach(h)
    vb = re.sub(r"\n{3,}", "\n\n", vb)
    if len(vb) < 400:
        return None
    return {"van_ban": vb, "kieu": kieu, "cach": "html"}


#: Loi cua lan `doc()` gan nhat. Nguoi goi phai doc no TRUOC khi ket luan mot
#: dia chi la "khong doc duoc".
#:
#: BAY DA SAP THAT 30/08/2026. `seeker.doc_toan_van` ghi mot ban ghi
#: `khong_doc_duoc` VINH VIEN moi lan `doc()` tra None, de khoi keo lai mai mot
#: dia chi hong. Nhung dem do no danh dau **83 dia chi Reddit** — va Reddit
#: hong vi `ERR_NAME_NOT_RESOLVED`, tuc **DNS bi chan tren may nay**, mot dieu
#: kien MOI TRUONG chu khong phai thuoc tinh cua dia chi. Doi mang hay bat VPN
#: thi 83 bai do van khong bao gio duoc thu lai.
#:
#: Hai thu phai tach bach: "trang nay khong co gi de doc" va "hom nay ta khong
#: voi toi duoc no".
LOI_CUOI: dict = {}

#: Dau hieu cua loi MOI TRUONG - khong duoc dung de khoa vinh vien mot dia chi.
_TAM_THOI_RE = re.compile(
    r"(ERR_NAME_NOT_RESOLVED|ERR_INTERNET_DISCONNECTED|ERR_CONNECTION|"
    r"ERR_PROXY|ERR_TIMED_OUT|ERR_NETWORK|khong_mo_cdp|"
    r"ConnectionError|ConnectTimeout|ReadTimeout|Timeout|"
    r"TooManyRedirects|SSLError|ProxyError|\b(?:429|502|503|504)\b)", re.I)


def _ghi_loi(url: str, loi: str) -> None:
    LOI_CUOI.clear()
    LOI_CUOI.update({"url": url, "loi": (loi or "")[:200],
                     "tam_thoi": bool(_TAM_THOI_RE.search(loi or ""))})


def loi_tam_thoi() -> bool:
    """Lan `doc()` gan nhat that bai vi MOI TRUONG chu khong vi dia chi?"""
    return bool(LOI_CUOI.get("tam_thoi"))


def tu_youtube(url: str) -> dict | None:
    """Video -> CHU, bang phu de tu dong cua YouTube.

    Claude khong xem duoc video va khong nghe duoc tieng. Nhung gan nhu moi
    video YouTube deu co phu de tu dong, va do la van ban that su - do 30/08 tren
    5 video dau tien lay duoc: 6.485 / 8.015 / 8.180 / 8.229 / 43.092 ky tu, noi
    dung that ve mean reversion va dao chieu gia.

    Duong nay KHONG can dang nhap va khong ton mot lan mo trinh duyet nao.

    Neu video khong co phu de thi con mot duong nua chua lam: `yt-dlp` tai TIENG
    roi cho qua mot bo nhan dang giong noi (Whisper). Do la cach chuan tren cac
    dien dan. `yt_dlp` DA CO tren may; Whisper thi chua cai.

    TikTok khong di duong nay duoc: clip ngan, phan lon khong co phu de, va
    khong co API phu de cong khai. Muon doc TikTok phai qua tieng.
    """
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{6,})", url or "")
    if not m:
        return None
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except Exception:
        return None
    try:
        muc = YouTubeTranscriptApi().fetch(m.group(1))
    except Exception:
        return None
    van = " ".join(getattr(x, "text", "") for x in muc).strip()
    if len(van) < 400:
        return None
    return {"van_ban": van, "kieu": "video", "cach": f"youtube_phu_de:{m.group(1)}"}


# --------------------------------------------------- DUONG QUA TRINH DUYET
#: Mien BAT BUOC di qua trinh duyet, khong phi thoi gian thu `requests` truoc.
#:
#: Do that tren so cai 30/08/2026: trong 675 tai lieu chua co ban toan van,
#: **~230 ban thuoc dung cac mien nay** (reddit 83, mql5 57, myfxbook 37,
#: darwinex 29, t.me 22, x.com 3) va CHUA MOT BAN NAO doc duoc. Ly do khong
#: phai nguon chan: `doc()` chi co ba duong (arxiv / github / html tho) va
#: **khong duong nao di qua con Chrome da dang nhap** cua du an, du ha tang do
#: da co san tu 21/08 (`nhan/doc_trinh_duyet.py`, CDP 9224, ho so
#: `lab/.browser_darwinex` 1,5 GB co phien dang nhap that).
#:
#: Day la day noi con thieu, khong phai mot tinh nang moi.
#: `fxblue.com` BI GO khoi danh sach nay ngay 12/09/2026. Do that cung ngay
#: bang `requests` + UA that: trang chu tra **200 / 525.989 ky tu**, trang
#: huong dan `/tools-for-download/fx-blue-trading-simulator/user-guide/
#: metaTrader4` tra **33.223 ky tu CHU** - khong Cloudflare, khong doi dang
#: nhap, khong render bang JS. Giu ten no o day nghia la moi lan doc mot dia
#: chi fxblue he phai thu con Chrome TRUOC (va CDP thuong TAT, tuc mot vong
#: hong roi moi lui ve `tu_html`) cho mot trang von doc thang duoc.
CAN_TRINH_DUYET = (
    "reddit.com", "mql5.com", "myfxbook.com", "darwinex.com", "t.me",
    "x.com", "twitter.com", "facebook.com", "discord.com", "tiktok.com",
    "collective2.com", "tradingview.com", "quantconnect.com",
)


def can_trinh_duyet(url: str) -> bool:
    u = (url or "").lower()
    return any(m in u for m in CAN_TRINH_DUYET)


def tu_trinh_duyet(url: str, kieu: str = "khac") -> dict | None:
    """Doc qua con Chrome CDP dang mo (ho so co phien dang nhap that).

    Tra None khi CDP khong chay - va do la mot trang thai TAM THOI, khong phai
    thuoc tinh cua dia chi. Nguoi goi phai phan biet hai thu do: danh dau mot
    URL la "khong doc duoc" trong luc trinh duyet dang tat se khoa no vinh vien.
    Xem `seeker.doc_toan_van`.
    """
    try:
        if __package__ in (None, ""):
            import doc_trinh_duyet as DTD          # type: ignore
        else:
            from . import doc_trinh_duyet as DTD
    except Exception:
        return None
    if not DTD.cdp_dang_chay():
        _ghi_loi(url, "khong_mo_cdp")
        return None
    try:
        r = DTD.doc_gan(url, toi_da_text=NGAN_SACH_KY_TU.get(kieu, 25_000))
    except Exception as e:
        _ghi_loi(url, f"{type(e).__name__}: {e}")
        return None
    if not r or r.get("loi"):
        _ghi_loi(url, (r or {}).get("loi") or "khong ro")
        return None
    if len((r.get("text") or "").strip()) < 400:
        _ghi_loi(url, "trang rong hoac qua ngan")
        return None
    return {"van_ban": r["text"], "kieu": kieu, "cach": "trinh_duyet"}


# ------------------------------------------------------------------- CUA RA
#: Duoi file phai boc bang bo doc rieng chu khong phai bo boc HTML.
DUOI_PDF = (".pdf",)
DUOI_ANH = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")


def _la_file_boc_rieng(u: str) -> bool:
    goc = u.split("?")[0].split("#")[0]
    return goc.endswith(DUOI_PDF + DUOI_ANH)


def tu_file_tai_ve(url: str) -> dict | None:
    """Tai file ve thu muc tam roi boc bang `doc_pdf` / `doc_anh`.

    PDF cua Telegram phan lon la ANH QUET - `doc_pdf` co duong OCR rieng cho
    truong hop do [[pdf-telegram-la-anh-can-ocr]]. Neu chi lay lop van ban thi
    ~6 lan so trang tra ve rong ma khong bao loi.
    """
    import tempfile
    b = _lay(url, timeout=60, nhi_phan=True)
    if not b:
        return None
    goc = url.lower().split("?")[0].split("#")[0]
    duoi = ".pdf" if goc.endswith(DUOI_PDF) else Path(goc).suffix or ".bin"
    tam = Path(tempfile.gettempdir()) / ("toan_van_tam" + duoi)
    try:
        tam.write_bytes(b)
    except OSError:
        return None
    try:
        if duoi == ".pdf":
            from nhan import doc_pdf as DP
            kq = DP.doc_file(tam, ocr=True)
            vb = _sach(str(kq.get("van_ban") or ""))
            cach = "pdf:" + str(kq.get("cach") or kq.get("duong") or "doc_pdf")
        else:
            from nhan import doc_anh as DA
            kq = DA.doc(tam)
            vb = _sach(str(kq.get("van_ban") or ""))
            cach = "anh:ocr"
    except Exception as e:
        _ghi_loi(url, "%s: %s" % (type(e).__name__, str(e)[:90]))
        return None
    finally:
        try:
            tam.unlink()
        except OSError:
            pass
    if len(vb) < 200:
        _ghi_loi(url, "boc ra chi %d ky tu - coi nhu khong doc duoc" % len(vb))
        return None
    return {"van_ban": vb, "kieu": "tai_lieu", "cach": cach,
            "so_ky_tu": len(vb)}


def doc(url: str, goi_y: str = "") -> dict | None:
    """Doc mot dia chi bat ky. Tu chon bo boc theo dang nguon.

    Tra {van_ban, kieu, cach, so_ky_tu} hoac None neu khong doc duoc.
    """
    if not url or not url.startswith("http"):
        return None
    LOI_CUOI.clear()
    u = url.lower()
    r = None
    # Mien can dang nhap / render bang JS: di THANG qua trinh duyet. Thu
    # `requests` truoc chi ton thoi gian va tra ve trang dang nhap.
    if can_trinh_duyet(u):
        r = tu_trinh_duyet(url, goi_y or ("dien_dan" if "reddit" in u or "t.me" in u
                                          else "khac"))
    # Video: lay PHU DE truoc, re hon va sach hon nhieu so voi boc trang.
    if r is None and ("youtube.com/watch" in u or "youtu.be/" in u):
        r = tu_youtube(url)
    # FILE TAI VE (PDF / anh) - phai boc bang bo doc rieng, khong phai `tu_html`.
    #
    # So do cua chu du an ghi ro: *"voi cac dang file tai lieu pdf bai viet
    # duoc phep search tu khoa => tim link co file tai tai lieu va tien hanh
    # tai ve"*. Va `nhan/doc_pdf.py` (co OCR cho trang la ANH) cung
    # `nhan/doc_anh.py` da ton tai tu truoc - ca hai deu MO COI den 15/09/2026.
    #
    # Truoc khi noi: mot URL `.pdf` bat ky (ngoai arxiv) roi xuong `tu_html`,
    # va `tu_html` doc mot file nhi phan ra chuoi rac roi ghi vao kho nhu mot
    # "ban doc". Khong ai bao loi - chi la mot ban doc vo nghia.
    if r is None and _la_file_boc_rieng(u):
        r = tu_file_tai_ve(url)
    if r is None and "arxiv.org" in u:
        r = tu_arxiv(url)
    elif r is None and "github.com" in u:
        r = tu_github(url)
    if r is None:
        kieu = goi_y or ("dien_dan" if any(k in u for k in
                                           ("forum", "stackexchange", "quantconnect",
                                            "forexfactory", "news.ycombinator"))
                         else "blog" if any(k in u for k in
                                            ("blog", "quantpedia", "alphaarchitect",
                                             "robotwealth"))
                         else "khac")
        r = tu_html(url, kieu)
        # Chot cuoi: HTML tho hong (403, render bang JS, tuong dang nhap) thi
        # van con con Chrome that. Truoc 30/08 khong co buoc nay nen moi dia chi
        # kieu do deu bi ghi la "khong doc duoc" VINH VIEN.
        if r is None:
            r = tu_trinh_duyet(url, kieu)
    if r is None:
        if not LOI_CUOI:
            _ghi_loi(url, "khong bo boc nao doc duoc")
        return None
    LOI_CUOI.clear()
    tran = NGAN_SACH_KY_TU.get(r["kieu"], NGAN_SACH_KY_TU["khac"])
    day_du = len(r["van_ban"])
    if day_du > tran:
        # Giu DAU va CUOI: dau la tom tat + phuong phap, cuoi la ket qua + ket luan.
        # Cat cut duoi la cach chac chan nhat de mat dung bang so.
        r["van_ban"] = (r["van_ban"][: int(tran * 0.65)] +
                        "\n\n[... cat bot phan giua ...]\n\n" +
                        r["van_ban"][-int(tran * 0.35):])
    r["so_ky_tu"] = len(r["van_ban"])
    r["so_ky_tu_goc"] = day_du
    r["url"] = url
    return r


if __name__ == "__main__":
    thu = sys.argv[1:] or [
        "http://arxiv.org/abs/2411.05790",
        "https://github.com/kernc/backtesting.py",
        "https://www.quantconnect.com/forum/discussions/1/latest",
        "https://alphaarchitect.com/feed/",
    ]
    for u in thu:
        t = time.time()
        r = doc(u)
        if not r:
            print(f"  [KHONG DOC DUOC] {u}")
            continue
        print(f"  [{r['kieu']:<9}] {u[:58]:<60} {r['so_ky_tu']:>7,} ky tu "
              f"(goc {r['so_ky_tu_goc']:,}) qua {r['cach']} - {time.time()-t:.1f}s")
        print(f"      {r['van_ban'][:180].strip()!r}")
