# -*- coding: utf-8 -*-
"""day_chuyen.py - NOI CA DAY CHUYEN 03/09/2026 THANH MOT CHO GOI.

Hom nay du an chay hon 10 tieng tren MOT muc tieu cu the (US500CASH, 20-30
%/nam) va lo ra rat nhieu van de. Cac manh sua roi nam rai o ~10 module. File
nay noi chung lai theo dung QUY TRINH chu du an dat ra, de lan sau khong phai
nho tung ten ham.

    Chu du an dua MOT muc tieu
      |
      +-- LUONG 1  SAN     `muc_tieu.san` + `san_he_pho_thong` + `ma_nguon`
      |   (theo TAI SAN va theo TEN HE THONG; MQL5/GitHub/TradingView)
      |
      +-- LUONG 2  DOC+BOC `doc_song_song.doc` -> `boc_llm.boc`
      |   (doc 0,31 s/ban; boc 3-5 s/ban voi suat 19-37 co che/100 ban)
      |
      +-- LUONG 3  NOI SINH `noi_sinh.sinh` / `sinh_cap` / `sinh_xu_huong`
      |
      +-- NGOAI SINH  `ngoai_sinh.chuyen` (he DA PASS -> tai san moi)
      |
      +-- DO       `bien_don_bay.do_bien` + `cong` + `do_on_dinh`

DIEU KIEN MANG (bai hoc dat nhat hom nay): nhieu nguon bi chan o tang DNS chu
khong phai bi "chan bot". `kiem_mang()` do truoc va noi ro phai bat gi.
"""
from __future__ import annotations

import time


# --------------------------------------------------------------- MANG
def kiem_mang(in_ra=print) -> dict:
    """Do duong ra cho cac nguon chinh. Tra {nguon: 'OK'|ly_do}.

    Bai hoc 03/09: `www.mql5.com` bi DNS dau doc -> ba trieu chung khac nhau
    (RemoteDisconnected / ERR_HTTP2_PROTOCOL_ERROR / HTTP 000) tung bi doan
    thanh ba nguyen nhan rieng. Bat Cloudflare WARP la thong.
    """
    import requests
    from nhan import duyet_nguoi as DN
    dia_chi = {
        "mql5": "https://www.mql5.com/en/code/mt5/experts",
        "tradingview": "https://www.tradingview.com/",
        "github": "https://api.github.com/",
    }
    ra = {}
    for ten, u in dia_chi.items():
        try:
            r = requests.get(u, timeout=20, headers={"User-Agent": DN.UA})
            ra[ten] = "OK" if r.status_code == 200 else f"HTTP {r.status_code}"
        except Exception as e:
            ra[ten] = f"{type(e).__name__}"
        in_ra(f"  {ten:<14}{ra[ten]}")
    if ra.get("mql5") != "OK":
        in_ra("  -> mql5 hong. Thu: warp-cli --accept-tos connect  "
              "(hoac `nhan/dns_vuot.bat()`)")
    return ra


def bat_warp(in_ra=print) -> bool:
    """Bat Cloudflare WARP neu co. Tra True khi da ket noi."""
    import subprocess
    exe = r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"
    try:
        subprocess.run([exe, "--accept-tos", "connect"], timeout=60,
                       capture_output=True)
        r = subprocess.run([exe, "--accept-tos", "status"], timeout=30,
                           capture_output=True, text=True)
        ok = "Connected" in (r.stdout or "")
        in_ra(f"  WARP: {(r.stdout or '').strip()[:60]}")
        return ok
    except Exception as e:
        in_ra(f"  WARP khong bat duoc: {type(e).__name__}")
        return False


# ------------------------------------------------------------- LUONG 1
def san(ma: str = "US500CASH", toan_luc: int = 40, mql5_vong: int = 3,
        in_ra=print) -> dict:
    """LUONG 1 - san theo TAI SAN, theo TEN HE THONG, va cao MQL5."""
    from nhan import ma_nguon as MN
    from nhan import muc_tieu as MT

    t0 = time.time()
    ra = {}
    in_ra("-- 1a. theo TAI SAN --")
    ra["tai_san"] = MT.san(ma, ngan_sach_giay=600, toan_luc=toan_luc, in_ra=in_ra)
    in_ra("-- 1b. theo TEN HE THONG --")
    with MT.NoiTran(toan_luc):
        ra["he_pho_thong"] = MT.san_he_pho_thong(ngan_sach_giay=600, in_ra=in_ra)
    in_ra("-- 1c. MQL5 Code Base (file .mq5 that) --")
    mql5 = {"tai_duoc": 0, "ghi_moi": 0}
    for v in range(mql5_vong):
        r = MN.thu_thap(muc_can=("experts", "indicators"), so_bai=30)
        mql5["tai_duoc"] += int(r.get("tai_duoc", 0) or 0)
        mql5["ghi_moi"] += int(r.get("ghi_moi", 0) or 0)
        in_ra(f"  vong {v+1}: tai {r.get('tai_duoc')} | moi {r.get('ghi_moi')} "
              f"| trang {r.get('trang_da_lay')}")
        if not r.get("nhin_thay"):
            break
    ra["mql5"] = mql5
    ra["giay"] = round(time.time() - t0, 1)
    return ra


# ------------------------------------------------------------- LUONG 2
def boc(so_doc: int = 500, so_boc: int = 200, ma_kiem: str = "US500CASH",
        in_ra=print) -> dict:
    """LUONG 2 - doc toan van SONG SONG roi boc co che."""
    from nhan import boc_llm as BL
    from nhan import doc_song_song as DS
    from nhan import du_lieu as DU
    from nhan import ngu_phap as NP

    t0 = time.time()
    truoc = len(NP.doc_kho())
    in_ra("-- 2a. doc song song --")
    d = DS.doc(gioi_han=so_doc, luong=12, in_ra=in_ra)
    in_ra(f"   doc duoc {d.get('doc_duoc')}/{d.get('tai_lieu')} "
          f"({d.get('giay_moi_ban')} s/ban)")
    in_ra("-- 2b. boc co che --")
    df = DU.nap(ma_kiem, "H4")
    b = BL.boc(gioi_han=so_boc, luong=8, ghi_kho=True, df_kiem=df, in_ra=in_ra)
    sau = len(NP.doc_kho())
    in_ra(f"   kho co che: {truoc} -> {sau} (+{sau - truoc})")
    return {"doc": d, "boc": b, "co_che_truoc": truoc, "co_che_sau": sau,
            "giay": round(time.time() - t0, 1)}


# --------------------------------------------------------- CA DAY CHUYEN
def mot_luot(ma: str = "US500CASH", in_ra=print) -> dict:
    """San -> doc -> boc, mot lenh. Khong dang ky gia thuyet, khong cham FDR."""
    t0 = time.time()
    in_ra(f"=== DAY CHUYEN: {ma} ===")
    in_ra("-- 0. kiem mang --")
    m = kiem_mang(in_ra)
    if m.get("mql5") != "OK":
        in_ra("-- 0b. bat WARP --")
        bat_warp(in_ra)
        m = kiem_mang(in_ra)
    s = san(ma, in_ra=in_ra)
    b = boc(ma_kiem=ma, in_ra=in_ra)
    in_ra(f"\n=== XONG {time.time() - t0:.0f}s ===")
    return {"mang": m, "san": s, "boc": b, "giay": round(time.time() - t0, 1)}
