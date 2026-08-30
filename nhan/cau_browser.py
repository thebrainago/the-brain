# -*- coding: utf-8 -*-
"""cau_browser.py - CAU NOI: "The Eye of Seeker" (browser/) -> The Brain.

LAN DAU VAO THU HAI. Lan mot la feed/API (`nhan/nguon_bai_viet.py`) - noi
nguoi ta VIET LUAT. Lan hai la dien dan va mang xa hoi - noi nguoi ta KE.
Hai lan co gia tri khac han nhau va phai duoc do rieng, khong duoc tron.

VI SAO TRUOC DAY KHONG NOI (do that 21, 22 va 23/08, ba lan cung mot ket qua):
  `C:/Users/SV STORE/seeker.py` + `browser/` ghi vao `thu_vien.db` - **439
  scout_tasks**, khong doi mot dong suot ba ngay - va grep toan bo ma cua no
  khong co mot tham chieu nao toi `nao.db`, `candidate_queue` hay
  `CandidateArtifact`. Tuc 864 bai no gom duoc chua tung vao day chuyen.

VI SAO KHONG BAC CAU THANG:
  Do noi dung that ngay 23/08 tren 864 bai: **trung vi 151 ky tu**, 62 bai
  RONG, va noi dung la tin hieu le + quang cao ("XAUHQ | WEEKEND OFFER 100%
  FREE VIP $0 CHANNEL"). Tha thang vao `candidate_queue` la dot ngan sach FDR
  bang rac. Nen cua nay co MOT CAI CONG, va cong do duoc hieu chuan HAI CHIEU
  nhu moi cong khac trong he: rac phai bi chan, va mot bai luat that tren dien
  dan phai lot qua.

CAI CONG DO GI:
  1. Do dai toi thieu - duoi `TOI_THIEU_KY_TU` thi khong the chua mot luat day du.
  2. Khong phai TIN HIEU LE. "BUY 4478, SL 4475, TP 4490" la mot lenh cua mot
     nguoi trong mot ngay, khong phai mot luat tai lap duoc. Chung khac nhau o
     cho: luat noi DIEU KIEN, tin hieu noi GIA.
  3. Khong phai QUANG CAO.
  4. Phai co it nhat `TOI_THIEU_TU_NGANH` tu nganh KHAC NHAU.
Qua duoc cong thi vao `tai_lieu`/`noi_dung` nhu moi tai lieu khac, roi di dung
duong cu: artifact -> ung vien -> QUANTLAB. Khong co duong tat nao.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from nhan import so as SO
else:
    from . import so as SO

#: Noi con browser do ghi. Khong doi vi tri - no la du an rieng cua nguoi dung.
GOC_BROWSER = Path.home() / "browser"
THU_MUC_DATA = GOC_BROWSER / "scraped_data"

TOI_THIEU_KY_TU = 400
TOI_THIEU_TU_NGANH = 2

#: Tu nganh. Dem so tu KHAC NHAU, khong dem so lan - mot bai quang cao lap chu
#: "trading" 20 lan van chi duoc 1 diem.
TU_NGANH = re.compile(
    r"\b(?:strategy|strategies|backtest\w*|indicator|momentum|mean[- ]revers\w*"
    r"|volatility|drawdown|sharpe|equity curve|position siz\w*|risk manag\w*"
    r"|moving average|rsi|atr|bollinger|breakout|timeframe|expectancy"
    r"|win rate|portfolio|correlation|hedge|arbitrage|liquidity|order flow"
    r"|chien luoc|kiem dinh|quan ly von|khung thoi gian)\b", re.I)

#: TIN HIEU LE: mot lenh cu the cua mot ngay. Dau hieu la GIA di kem nhan
#: entry/sl/tp. Do that 23/08: day la dang chiem gan het cac kenh Telegram.
TIN_HIEU_LE = re.compile(
    r"\b(?:entry|entries|sl|stop\s*loss|tp\d?|take\s*profit)\b\s*[:=@]?\s*[\d.,/\-\s]{3,}",
    re.I)

#: QUANG CAO / moi chao.
QUANG_CAO = re.compile(
    r"\bvip\b|\bfree channel\b|\bdm me\b|\bdm us\b|\bsign\s*up\b|\bjoin now\b"
    r"|\bt\.me/|\bwhatsapp\b|\bsubscribe now\b|\bpromo\b|\bdiscount\b"
    r"|\bcopy trade\b|\bmanaged account\b|\bguaranteed profit\b"
    r"|\bmien phi\b|\bdang ky ngay\b|\bcam ket loi nhuan\b", re.I)


#: Chuoi giao dien cua MOT TRANG WEB, khong phai cua mot bai viet. Con browser
#: luu ca trang danh sach thanh mot "bai": bai duy nhat lot qua cong o lan chay
#: dau la mot ban do nguyen trang tim kiem TradingView, mo dau bang "Skip to
#: main content Search EN Get started All ideas...".
#:
#: Do MAT DO CAU khong phan biet duoc (ban do 10,83 cau/1000 ky tu so voi bai
#: that 12,47 - trung nhau), vi trang danh sach cung day mo ta co cham cau.
#: Thu phan biet duoc la CHUOI DIEU HUONG.
UI_TRANG = re.compile(
    r"skip to (?:main )?content|sign in\b|log ?in\b|get started\b|create account"
    r"|accept (?:all )?cookies|cookie (?:policy|settings)|load more\b"
    r"|most recent\b|most popular\b|all ideas\b|subscribe to our newsletter"
    r"|terms of (?:use|service)|privacy policy|©\s*\d{4}", re.I)


def la_dump_trang(vb: str) -> bool:
    """Ban do nguyen mot trang web, khong phai mot bai viet.

    Hai dau hieu doc lap: chuoi dieu huong nam ngay DAU (300 ky tu dau), hoac
    tu ba chuoi giao dien KHAC NHAU tro len o bat cu dau. Mot bai viet that co
    the nhac 'privacy policy' mot lan; no khong co ba thu cung luc.
    """
    if not vb:
        return False
    if UI_TRANG.search(vb[:300]):
        return True
    return len({m.lower() for m in UI_TRANG.findall(vb)}) >= 3


def _sach(vb: str) -> str:
    from nhan import doc_hieu as DH
    return DH._chuan(vb or "")


def xet_bai(van_ban: str) -> dict:
    """Mot bai dien dan -> {nhan: bool, ly_do, diem_nganh, ky_tu}.

    Ham nay la CAI CONG. No khong doc hieu gi ca - viec do la cua
    `nhan/doc_hieu.py` o buoc sau. No chi tra loi: bai nay co dang de doc khong.
    """
    vb = _sach(van_ban)
    n = len(vb)
    if n < TOI_THIEU_KY_TU:
        return {"nhan": False, "ly_do": f"chi {n} ky tu, duoi {TOI_THIEU_KY_TU}",
                "ky_tu": n, "diem_nganh": 0}
    if la_dump_trang(vb):
        return {"nhan": False, "ly_do": "ban do nguyen trang web, khong phai bai viet",
                "ky_tu": n, "diem_nganh": 0}
    diem = len({m.lower() for m in TU_NGANH.findall(vb)})
    if QUANG_CAO.search(vb) and diem < 4:
        return {"nhan": False, "ly_do": "quang cao/moi chao, khong du chat nganh",
                "ky_tu": n, "diem_nganh": diem}
    if diem < TOI_THIEU_TU_NGANH:
        return {"nhan": False, "ly_do": f"chi {diem} tu nganh khac nhau",
                "ky_tu": n, "diem_nganh": diem}
    # TIN HIEU LE: nhieu nhan entry/sl/tp ma bai lai ngan -> mot lenh, khong
    # phai mot luat. Bai dai co the la bai PHAN TICH mot he thong co vao/ra,
    # nen do dai la thu phan biet.
    so_nhan = len(TIN_HIEU_LE.findall(vb))
    if so_nhan >= 2 and n < 1200:
        return {"nhan": False,
                "ly_do": f"tin hieu le ({so_nhan} nhan gia/{n} ky tu) - mot lenh, "
                         "khong phai mot luat",
                "ky_tu": n, "diem_nganh": diem}
    return {"nhan": True, "ly_do": "", "ky_tu": n, "diem_nganh": diem}


# ------------------------------------------------------------------ DOC KHO
def _cac_bai(thu_muc: Path | None = None) -> list[dict]:
    """Gom bai tu cac file JSON cua browser/. Chap nhan nhieu hinh dang."""
    d = thu_muc or THU_MUC_DATA
    if not d.exists():
        return []
    ra, thay = [], set()
    for f in sorted(d.glob("*.json")):
        try:
            noi = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        posts = noi.get("posts") if isinstance(noi, dict) else noi
        if not isinstance(posts, list):
            continue
        for p in posts:
            if not isinstance(p, dict):
                continue
            vb = str(p.get("content") or p.get("text") or p.get("message") or "")
            if not vb.strip():
                continue
            url = str(p.get("url") or p.get("link") or "").strip()
            # Chong trung theo TOAN BO noi dung. Lay 160 ky tu dau lam khoa thi
            # sai nang: cac bai cua cung mot kenh dung chung mot phan dau (ten
            # kenh + ngay), nen 116 bai khac nhau bi gop con 22. Kho cua browser
            # co ty le lap 7,4 lan (864 ban ghi / 116 noi dung) nen buoc chong
            # trung nay la bat buoc, chi la phai chong dung cho.
            # Khoa la HASH NOI DUNG, khong phai url: tren Telegram moi bai cua
            # mot kenh deu mang cung mot url kenh, nen chong trung theo url gop
            # 116 bai khac nhau con 23.
            khoa = hashlib.md5(vb.encode("utf-8", "replace")).hexdigest()
            if khoa in thay:
                continue
            thay.add(khoa)
            ra.append({
                "van_ban": vb,
                "url": url,
                "tieu_de": str(p.get("title") or p.get("subject") or "").strip(),
                "nguon": str(p.get("source") or p.get("platform")
                             or p.get("channel") or "khong_ro"),
                "file": f.name,
            })
    return ra


def mot_luot(gioi_han: int = 200, thu_muc: Path | None = None) -> dict:
    """Doc kho cua browser, cho qua cong, ghi cai dat vao `tai_lieu`/`noi_dung`."""
    bai = _cac_bai(thu_muc)
    bao = {"doc_duoc": len(bai), "nhan": 0, "chan": 0, "trung": 0,
           "ky_tu": 0, "ly_do": {}, "theo_nguon": {}}
    for b in bai[:gioi_han]:
        xet = xet_bai(b["van_ban"])
        if not xet["nhan"]:
            bao["chan"] += 1
            k = xet["ly_do"].split("(")[0].split(",")[0][:44]
            bao["ly_do"][k] = bao["ly_do"].get(k, 0) + 1
            continue
        vb = _sach(b["van_ban"])
        ma_nguon = "browser_" + re.sub(r"[^a-z0-9_]+", "_", b["nguon"].lower())[:24]
        tieu_de = (b["tieu_de"] or " ".join(vb.split())[:120]) or "(khong tieu de)"
        vt = SO.van_tay(b["url"] or vb[:200])
        with SO.ket_noi() as cn:
            cur = cn.execute(
                "INSERT OR IGNORE INTO tai_lieu(van_tay,nguon,loai,tieu_de,url,"
                "tom_tat,tu_khoa,diem,luc) VALUES(?,?,?,?,?,?,?,?,?)",
                (vt, ma_nguon, "dien_dan", tieu_de[:400], b["url"],
                 vb[:2000], "C", 1.0, SO.bay_gio()))
            moi = cur.rowcount
            row = cn.execute("SELECT id FROM tai_lieu WHERE van_tay=?", (vt,)).fetchone()
            if not row:
                continue
            cur2 = cn.execute(
                "INSERT OR IGNORE INTO noi_dung(tai_lieu_id,van_tay,url,kieu,cach,"
                "so_ky_tu,so_ky_tu_goc,van_ban,luc,da_boc) "
                "VALUES(?,?,?,'dien_dan','cau_browser',?,?,?,?,0)",
                (row[0], SO.van_tay("nd", b["url"] or vb[:200]), b["url"],
                 len(vb), len(b["van_ban"]), vb, SO.bay_gio()))
        if cur2.rowcount:
            bao["nhan"] += 1
            bao["ky_tu"] += len(vb)
            bao["theo_nguon"][ma_nguon] = bao["theo_nguon"].get(ma_nguon, 0) + 1
        else:
            bao["trung"] += 1
    SO.ghi_chi_so("cau_browser_nhan", bao["nhan"], bao)
    return bao


if __name__ == "__main__":
    import pprint
    pprint.pprint(mot_luot())
