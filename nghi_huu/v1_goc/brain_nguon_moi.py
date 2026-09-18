# -*- coding: utf-8 -*-
"""
brain_nguon_moi.py - LOP NGUON MO RONG cho The Brain (chay duoi brain_vong_lap.py)
=====================================================================================
NGUYEN TAC XUYEN SUOT: bot KHONG TU DANG KY tai khoan o dau, KHONG scrape noi nao cam.
Chu du an tao tai khoan bang tay mot lan, roi giao lai KHOA CHI-DOC. Bot chi DOC.

Ly do khong phai "than trong" ma la "duong nao ben hon":
  - Tu dong dang ky vi pham dieu khoan gan nhu moi nen tang, va ket o xac minh SDT/KYC
  - VPS nam trong dai IP datacenter -> bi gan co tu tai khoan dau tien
  - API chinh thuc thi on dinh, khong bi khoa, khong phai nuoi

=====================================================================================
FACEBOOK - LAT NGUOC CHIEU (day la mieng ghep quan trong nhat file nay)
=====================================================================================
Sai lam thuong gap: co KEO du lieu tu Facebook ve. Meta da dong gan het cua, va
CrowdTangle da khai tu 08/2024.

Cach dung: BAT FACEBOOK DAY SANG MINH.
  Facebook tu gui email cho ban: thong bao nhom, bai moi cua Page ban theo doi,
  ban tin hang tuan. Do la noi dung Facebook CHU DONG gui vao hop thu CUA BAN.
  Doc hop thu cua chinh minh thi khong vi pham gi, khong bi chan, khong phai nuoi tk.

  Chu du an lam 1 lan (~15 phut):
    1. Tao 1 email chuyen dung, vd  brain.nguon@...
    2. Dang nhap Facebook bang tai khoan THAT, vao tung nhom/Page trading quan tam
       -> bat "Thong bao qua email" (Settings > Notifications > Email)
    3. Doi email nhan thong bao ve email chuyen dung o buoc 1
    4. Dang ky them: Substack, newsletter, YouTube channel notify, dien dan
    5. Bat IMAP cho hop thu do, tao MAT KHAU UNG DUNG (khong dung mat khau chinh)
    6. Dien vao file  nguon_config.json  (xem MAU_CONFIG ben duoi)

  Mot cong IMAP thay the ca chuc cong scrape, va gom Facebook + Substack + YouTube
  + dien dan ve mot cho.

=====================================================================================
CAC NGUON KHAC
=====================================================================================
  Hugging Face   - API MO HOAN TOAN, khong can dang nhap. Noi cong nghe moi xuat hien
                   TRUOC GitHub. Models / Datasets / Papers.
  GitHub         - da co trong brain_sources.py, o day them nhanh "cong nghe moi"
  YouTube        - Data API v3 (khoa mien phi, co han ngach) + phu de.
                   Tai lieu THAT cua bot DongDongTV nam trong clip, khong nam trong .rar
  Darwinex       - track record DARWIN cong bo mo
  Myfxbook       - API, xem duoc he thong cong khai
  SEC EDGAR      - 13F, KHONG can tai khoan, du lieu thuoc pham vi cong cong
  SSI/VNDirect/TCBS - API cong khai thi truong Viet Nam

Tat ca deu do vao THU VIEN hoac CONG NGHE. **Khong cai nao cham so FDR.**
"""
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
CONFIG = HERE / "nguon_config.json"
UA = {"User-Agent": "Mozilla/5.0 (The Brain research bot; local use)"}

MAU_CONFIG = {
    "imap": {
        "may_chu": "imap.gmail.com",
        "cong": 993,
        "email": "brain.nguon@example.com",
        "mat_khau_ung_dung": "xxxx xxxx xxxx xxxx",
        "_ghi_chu": "Gmail: bat 2FA roi tao App Password. KHONG dung mat khau chinh.",
        "hop_thu": ["INBOX"],
        "so_ngay_lui": 3
    },
    "youtube": {"api_key": "", "_ghi_chu": "console.cloud.google.com -> YouTube Data API v3"},
    "myfxbook": {"email": "", "mat_khau": ""},
    "_an_toan": "KHONG bao gio dat o day khoa co quyen DAT LENH. Chi-doc thoi."
}


def _cfg(muc=None):
    if not CONFIG.exists():
        CONFIG.write_text(json.dumps(MAU_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [da tao mau config] {CONFIG} - dien vao roi chay lai")
        return {}
    try:
        d = json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return d.get(muc, {}) if muc else d


def _ctx():
    """Python cai qua Windows Store thieu bo chung chi goc -> dung certifi neu co.
    KHONG tat kiem tra chung chi."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _get(url, timeout=30, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as r:
        return r.read().decode("utf-8", errors="replace")


def _dong(nguon, khoa, ten, tac_gia="", ngay="", tom_tat="", link="", loai="", them=None):
    """Mot dong chuan cho THU VIEN / CONG NGHE. `khoa` dung de khu trung lap."""
    return {"nguon": nguon, "khoa": str(khoa)[:200], "ten": str(ten)[:300],
            "tac_gia": str(tac_gia)[:150], "ngay": ngay or datetime.now().date().isoformat(),
            "tom_tat": str(tom_tat)[:800], "link": str(link)[:400], "loai": loai,
            "nap_luc": datetime.now().isoformat(timespec="seconds"), **(them or {})}


# ---------------------------------------------------------------------------
# 1. HOP THU IMAP  <- Facebook, Substack, YouTube, dien dan deu do ve day
# ---------------------------------------------------------------------------

def doc_hop_thu():
    """Doc hop thu chuyen dung. Day la cong 'mang xa hoi' cua The Brain.

    Khong scrape gi ca: Facebook/Substack/YouTube TU GUI vao hop thu nay vi chu du an
    da bat thong bao. Doc hop thu cua chinh minh la viec hoan toan binh thuong.
    """
    import email
    import imaplib
    from email.header import decode_header, make_header

    c = _cfg("imap")
    if not c or not c.get("email") or "example.com" in str(c.get("email")):
        return []

    ra = []
    lui = int(c.get("so_ngay_lui", 3))
    tu_ngay = (datetime.now() - __import__("datetime").timedelta(days=lui)).strftime("%d-%b-%Y")

    try:
        M = imaplib.IMAP4_SSL(c["may_chu"], int(c.get("cong", 993)), ssl_context=_ctx())
        M.login(c["email"], c["mat_khau_ung_dung"])
    except Exception as e:
        print(f"  [IMAP] khong dang nhap duoc: {str(e)[:100]}")
        return []

    try:
        for hop in c.get("hop_thu", ["INBOX"]):
            try:
                M.select(hop, readonly=True)          # readonly: khong danh dau da doc
                ok, du_lieu = M.search(None, f'(SINCE "{tu_ngay}")')
                if ok != "OK":
                    continue
                for uid in du_lieu[0].split():
                    ok, raw = M.fetch(uid, "(RFC822)")
                    if ok != "OK" or not raw or not raw[0]:
                        continue
                    msg = email.message_from_bytes(raw[0][1])
                    try:
                        tieu_de = str(make_header(decode_header(msg.get("Subject", ""))))
                    except Exception:
                        tieu_de = msg.get("Subject", "")
                    nguoi_gui = msg.get("From", "")
                    than = _rut_than(msg)
                    ra.append(_dong(
                        nguon="hop_thu", khoa=msg.get("Message-ID", str(uid)),
                        ten=tieu_de, tac_gia=nguoi_gui,
                        ngay=_ngay_thu(msg), tom_tat=than[:800],
                        loai=_phan_loai_thu(nguoi_gui, tieu_de),
                        them={"do_dai_than": len(than)}))
            except Exception as e:
                print(f"  [IMAP] loi hop '{hop}': {str(e)[:80]}")
    finally:
        try:
            M.logout()
        except Exception:
            pass

    print(f"  [IMAP] doc {len(ra)} thu tu {lui} ngay gan nhat")
    return ra


def _rut_than(msg):
    """Lay phan chu cua email, bo the HTML."""
    phan = []
    if msg.is_multipart():
        for p in msg.walk():
            if p.get_content_type() in ("text/plain", "text/html"):
                try:
                    phan.append(p.get_payload(decode=True).decode(
                        p.get_content_charset() or "utf-8", errors="replace"))
                except Exception:
                    continue
    else:
        try:
            phan.append(msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="replace"))
        except Exception:
            pass
    t = "\n".join(phan)
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _ngay_thu(msg):
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(msg.get("Date")).date().isoformat()
    except Exception:
        return datetime.now().date().isoformat()


def _phan_loai_thu(nguoi_gui, tieu_de):
    g = f"{nguoi_gui} {tieu_de}".lower()
    for ten, dau in [("facebook", ["facebook", "@facebookmail"]),
                     ("youtube", ["youtube", "@youtube.com"]),
                     ("substack", ["substack"]),
                     ("dien_dan", ["forexfactory", "elitetrader", "reddit", "quantconnect"]),
                     ("san", ["myfxbook", "darwinex", "mql5", "tradingview"])]:
        if any(d in g for d in dau):
            return ten
    return "khac"


# ---------------------------------------------------------------------------
# 2. HUGGING FACE  - noi cong nghe moi xuat hien TRUOC GitHub. API mo, khong can khoa.
# ---------------------------------------------------------------------------

# Mo hinh nen chuoi thoi gian - day la lop cong nghe co the doi cach do luong.
# KHONG phai gia thuyet giao dich, nen KHONG ton slot FDR.
TU_KHOA_CN = ["time series forecasting", "financial time series", "market regime",
              "volatility forecasting", "portfolio optimization", "quantitative finance"]


def quet_cong_nghe(muc_tieu, tham_so=None):
    """Quet cong nghe moi -> so CONG NGHE. Sinh NANG LUC chu khong sinh gia thuyet."""
    if muc_tieu == "huggingface_models":
        return _hf("models", TU_KHOA_CN)
    if muc_tieu == "huggingface_datasets":
        return _hf("datasets", TU_KHOA_CN)
    if muc_tieu == "huggingface_papers":
        return _hf_papers()
    if muc_tieu == "github_trending":
        return _github_cn((tham_so or {}).get("tu_khoa", "time series forecasting"))
    return []


def _hf(kho, tu_khoa):
    """https://huggingface.co/api/{models,datasets} - cong khai, khong can dang nhap."""
    ra = []
    for tk in tu_khoa:
        url = (f"https://huggingface.co/api/{kho}?search={urllib.parse.quote(tk)}"
               f"&sort=downloads&direction=-1&limit=20")
        try:
            js = json.loads(_get(url))
        except Exception as e:
            print(f"  [HF {kho}] {tk}: {str(e)[:60]}")
            continue
        for it in js:
            mid = it.get("id") or it.get("modelId") or ""
            ra.append(_dong(
                nguon=f"HuggingFace/{kho}", khoa=mid, ten=mid,
                tac_gia=(mid.split("/")[0] if "/" in mid else ""),
                ngay=(it.get("lastModified") or "")[:10],
                tom_tat=f"tai ve {it.get('downloads', 0)} | thich {it.get('likes', 0)} | "
                        f"the: {','.join(it.get('tags', [])[:8])}",
                link=f"https://huggingface.co/{'datasets/' if kho=='datasets' else ''}{mid}",
                loai="cong_nghe", them={"tu_khoa": tk, "tai_ve": it.get("downloads", 0)}))
        time.sleep(1)
    print(f"  [HF {kho}] {len(ra)} muc")
    return ra


def _hf_papers():
    """HF Papers - ban tuyen chon hang ngay tu arXiv, loc san theo do quan tam."""
    try:
        html = _get("https://huggingface.co/papers")
    except Exception as e:
        print(f"  [HF papers] {str(e)[:60]}")
        return []
    ra = []
    for m in re.finditer(r'href="(/papers/(\d+\.\d+))"[^>]*>\s*([^<]{10,200})', html):
        ra.append(_dong(nguon="HuggingFace/papers", khoa=m.group(2),
                        ten=m.group(3).strip(), link="https://huggingface.co" + m.group(1),
                        loai="cong_nghe"))
    print(f"  [HF papers] {len(ra)} bai")
    return ra


def _github_cn(tu_khoa):
    """GitHub search, nhung nhanh CONG NGHE: chi lay repo moi cap nhat gan day."""
    url = ("https://api.github.com/search/repositories?q="
           + urllib.parse.quote(f"{tu_khoa} pushed:>{_lui_ngay(90)}")
           + "&sort=stars&order=desc&per_page=20")
    try:
        js = json.loads(_get(url))
    except Exception as e:
        print(f"  [GitHub CN] {str(e)[:60]}")
        return []
    ra = []
    for it in js.get("items", []):
        gp = (it.get("license") or {}).get("spdx_id")
        if not gp or gp == "NOASSERTION":
            continue
        ra.append(_dong(nguon="GitHub/cong_nghe", khoa=it["full_name"], ten=it["full_name"],
                        tac_gia=it["owner"]["login"], ngay=it["pushed_at"][:10],
                        tom_tat=(it.get("description") or "")[:400], link=it["html_url"],
                        loai="cong_nghe", them={"sao": it.get("stargazers_count"),
                                                "giay_phep": gp}))
    print(f"  [GitHub CN] {len(ra)} repo")
    return ra


def _lui_ngay(n):
    import datetime as dt
    return (dt.date.today() - dt.timedelta(days=n)).isoformat()


# ---------------------------------------------------------------------------
# 3. YOUTUBE  - tai lieu THAT cua bot thuong nam trong clip, khong nam trong .rar
# ---------------------------------------------------------------------------

KENH_QUAN_TAM = []          # dien channelId vao nguon_config.json neu muon co dinh


def youtube_phu_de(tu_khoa=None):
    """Tim clip theo tu khoa qua Data API v3. Phu de tai bang yt-dlp neu co."""
    c = _cfg("youtube")
    key = c.get("api_key", "")
    if not key:
        print("  [YouTube] chua co api_key trong nguon_config.json")
        return []
    tu_khoa = tu_khoa or ["expert advisor mql5", "bot forex huong dan", "setting bot trading"]
    ra = []
    for tk in tu_khoa:
        url = ("https://www.googleapis.com/youtube/v3/search?part=snippet&type=video"
               f"&maxResults=15&order=date&q={urllib.parse.quote(tk)}&key={key}")
        try:
            js = json.loads(_get(url))
        except Exception as e:
            print(f"  [YouTube] {tk}: {str(e)[:70]}")
            continue
        for it in js.get("items", []):
            vid = it["id"].get("videoId")
            if not vid:
                continue
            sn = it["snippet"]
            ra.append(_dong(nguon="YouTube", khoa=vid, ten=sn["title"],
                            tac_gia=sn["channelTitle"], ngay=sn["publishedAt"][:10],
                            tom_tat=sn.get("description", "")[:500],
                            link=f"https://youtu.be/{vid}", loai="clip",
                            them={"tu_khoa": tk, "co_phu_de": False}))
        time.sleep(1)
    print(f"  [YouTube] {len(ra)} clip (phu de tai rieng bang yt-dlp)")
    return ra


# ---------------------------------------------------------------------------
# 4. QUAN THE NGUOI THANG  - cau hoi khong phai "ai thang" ma "ai thang DAI"
# ---------------------------------------------------------------------------

def track_record_darwinex():
    """DARWIN track record cong bo mo. Ghi lai THEO THOI GIAN de sau nay tra loi duoc:
    nguoi thang DAI khac nguoi thang MAY o chi so nao?"""
    try:
        js = json.loads(_get("https://api.darwinex.com/darwininfo/2.0/darwins"
                             "?sort=return&order=DESC&perPage=50"))
    except Exception as e:
        print(f"  [Darwinex] {str(e)[:80]} - kiem lai endpoint tren tai lieu chinh thuc")
        return []
    ra = []
    for d in (js if isinstance(js, list) else js.get("content", [])):
        ten = d.get("productName") or d.get("name", "")
        ra.append(_dong(nguon="Darwinex", khoa=f"{ten}@{datetime.now():%Y-%m}", ten=ten,
                        tom_tat=json.dumps({k: d.get(k) for k in
                                            ("return", "drawdown", "sharpe", "trades")},
                                           ensure_ascii=False),
                        loai="track_record", them={"anh_chup_thang": f"{datetime.now():%Y-%m}"}))
    print(f"  [Darwinex] {len(ra)} DARWIN")
    return ra


def track_record_myfxbook():
    """Myfxbook API: dang nhap lay session roi doc he thong cong khai.
    Tai khoan do chu du an tu tao. Chi-doc."""
    c = _cfg("myfxbook")
    if not c.get("email"):
        print("  [Myfxbook] chua co tai khoan trong nguon_config.json")
        return []
    try:
        js = json.loads(_get("https://www.myfxbook.com/api/login.json"
                             f"?email={urllib.parse.quote(c['email'])}"
                             f"&password={urllib.parse.quote(c['mat_khau'])}"))
        if js.get("error"):
            print(f"  [Myfxbook] {js.get('message')}")
            return []
        phien = js["session"]
        js2 = json.loads(_get(f"https://www.myfxbook.com/api/get-my-accounts.json?session={phien}"))
    except Exception as e:
        print(f"  [Myfxbook] {str(e)[:80]}")
        return []
    ra = []
    for a in js2.get("accounts", []):
        ra.append(_dong(nguon="Myfxbook", khoa=f"{a.get('id')}@{datetime.now():%Y-%m}",
                        ten=a.get("name", ""), loai="track_record",
                        tom_tat=json.dumps({k: a.get(k) for k in
                                            ("gain", "drawdown", "profit", "balance")},
                                           ensure_ascii=False)))
    print(f"  [Myfxbook] {len(ra)} tai khoan")
    return ra


# ---------------------------------------------------------------------------
# 5. THI TRUONG VIET NAM  - cua co hao sau nhat
# ---------------------------------------------------------------------------

def api_SSI():
    return _vn_khao_sat("SSI", "https://iboard-api.ssi.com.vn/statistics/charts/history")


def api_VNDirect():
    return _vn_khao_sat("VNDirect", "https://finfo-api.vndirect.com.vn/v4/stocks")


def api_TCBS():
    return _vn_khao_sat("TCBS", "https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars")


def _vn_khao_sat(ten, url):
    """Buoc 1 chi la KHAO SAT: endpoint con song khong, tra ve dang gi, can khoa khong.
    Chua keo du lieu that - viec do de vong sau khi da biet dinh dang."""
    try:
        raw = _get(url, timeout=20)
        ok, mo_ta = True, f"song, tra ve {len(raw)} ky tu, dau: {raw[:160]}"
    except Exception as e:
        ok, mo_ta = False, f"loi: {str(e)[:160]}"
    print(f"  [VN {ten}] {'OK' if ok else 'LOI'} {mo_ta[:90]}")
    return [_dong(nguon=f"VN/{ten}", khoa=f"khao_sat_{ten}_{datetime.now():%Y%m}",
                  ten=f"khao sat endpoint {ten}", link=url, tom_tat=mo_ta,
                  loai="mo_thi_truong", them={"con_song": ok})]


# ---------------------------------------------------------------------------
# 6. SEC EDGAR 13F  - khong can tai khoan, du lieu pham vi cong cong
# ---------------------------------------------------------------------------

QUY_THEO_DOI = {"Renaissance Technologies": "0001037389",
                "Two Sigma": "0001179392",
                "D E Shaw": "0001009207",
                "Bridgewater": "0001350694"}


def sec_13f():
    """SEC khuyen khich truy cap tu dong, chi doi khai User-Agent that."""
    hdr = {"User-Agent": "The Brain research (local; contact via project owner)"}
    ra = []
    for ten, cik in QUY_THEO_DOI.items():
        try:
            js = json.loads(_get(
                f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json", headers=hdr))
        except Exception as e:
            print(f"  [SEC] {ten}: {str(e)[:70]}")
            continue
        gan = js.get("filings", {}).get("recent", {})
        for i, dang in enumerate(gan.get("form", [])[:40]):
            if not str(dang).startswith("13F"):
                continue
            ra.append(_dong(nguon="SEC/13F", khoa=f"{cik}:{gan['accessionNumber'][i]}",
                            ten=f"{ten} {dang}", tac_gia=ten,
                            ngay=gan["filingDate"][i], loai="vi_the_quy",
                            link=f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                                 f"{gan['accessionNumber'][i].replace('-', '')}/"))
        time.sleep(0.5)          # SEC gioi han 10 request/giay
    print(f"  [SEC] {len(ra)} ho so 13F (tre ~45 ngay - khong phai vi the hien tai)")
    return ra


if __name__ == "__main__":
    lenh = sys.argv[1] if len(sys.argv) > 1 else "help"
    bang = {"hop-thu": doc_hop_thu, "hf-models": lambda: quet_cong_nghe("huggingface_models"),
            "hf-papers": lambda: quet_cong_nghe("huggingface_papers"),
            "youtube": youtube_phu_de, "darwinex": track_record_darwinex,
            "myfxbook": track_record_myfxbook, "sec": sec_13f,
            "vn": lambda: api_SSI() + api_VNDirect() + api_TCBS()}
    if lenh in bang:
        kq = bang[lenh]()
        print(f"\n-> {len(kq)} dong (chay qua brain_vong_lap.py de ghi vao so)")
    else:
        print("Dung: python brain_nguon_moi.py [" + "|".join(bang) + "]")
        print(f"Config: {CONFIG}")
