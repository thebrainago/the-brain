# -*- coding: utf-8 -*-
"""theo_doi.py - THEO KENH DA CHON, doc lai theo LICH do duoc.

## Vi sao

`hethong.txt`: *"Tu biet follow cac kenh, join cac nhom co nguon chat luong,
follow ca nhan co noi dung chat luong... biet doc lai cac bai cua nhung nguon da
follow mot luot de update file moi (tinh toan lich trinh khong can lam hang ngay)"*.

Do 11/09/2026: bang `theo_doi` DA TON TAI trong `thu_vien.db` voi 9 kenh da duyet
tay (Rob Carver, Quantified Strategies, Rational Reminder...). Nhung khong co bo
lap lich nao doc lai chung - `lan_quet_cuoi` dung yen tu 13/08.

## Vi sao cua nay dang gia HON quet chung chung

Do ngay 11/09 tren corpus video hien co: 27 ban phu de -> 3 spec -> **0 co che
moi**. Corpus do den tu tim kiem chung chung ("mean reversion", "trading bot")
nen phan lon la video nhap mon, noi ve khai niem chu khong doc ra nguong.

Kenh da duyet thi khac han. Tieu de 8 video moi nhat cua mot kenh trong danh sach:
"I Backtested Williams %R on QQQ: Here Are the Results", "This Simple RSI Strategy
Has Worked for Over 30 Years", "Supertrend Indicator (Backtested)". Do la cho co
nguong.

Nen module nay khong phai "them mot nguon nua" - no la duong DUY NHAT hien co de
kiem chinh gia thuyet vua ghi trong so bai hoc.

## Lich: theo SUAT do duoc, khong theo lich cung

Mot kenh ra bai moi moi thang ma quet moi ngay la 29 lan goi mang cho mot cau tra
loi da biet. Chu ky khoi diem 7 ngay, roi tu gian ra / co lai theo so bai MOI thu
duoc lan truoc - cung nguyen tac `vuon_nguon` dung cho ngan sach nguon.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(GOC))
    from nhan import so as SO
else:
    from . import so as SO

THU_VIEN = GOC / "thu_vien.db"

CHU_KY_KHOI_DIEM = 7 * 86400.0
CHU_KY_MIN = 2 * 86400.0
CHU_KY_MAX = 45 * 86400.0

#: Nghi giua hai video. Mo dau khong co cho nay: me 111 video dau tien chay lien
#: tuc va YouTube bat dau tra "Sign in to confirm you're not a bot" cho MOI lan
#: goi tiep theo. Mot con so nho o day re hon mot dot bi chan.
NGHI_GIUA_VIDEO = 1.5


def _LA_CHAN(ly_do: str) -> bool:
    """Phan biet BI CHAN voi KHONG CO GI - hai thu nay cho cung `bai_moi = 0`.

    Khong phan biet thi bo lap lich se GIAN chu ky len 45 ngay vi mot lan bi
    chan, tuc tu trung phat chinh no cho mot loi khong phai cua nguon. Day la
    dung cai bay `khau do hong doc y het ket qua am`, o tang lap lich.
    """
    t = (ly_do or "").lower()
    return any(k in t for k in ("not a bot", "sign in", "cookies", "429",
                                "rate", "captcha", "too many"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS theo_doi(
  ma          TEXT PRIMARY KEY,
  loai        TEXT,
  ten         TEXT,
  url         TEXT NOT NULL,
  nen_tang    TEXT,
  chu_ky_giay REAL DEFAULT 604800,
  lan_quet    REAL DEFAULT 0,
  so_lan      INTEGER DEFAULT 0,
  bai_moi     INTEGER DEFAULT 0,
  thu_hoach   INTEGER DEFAULT 0,
  trang_thai  TEXT DEFAULT 'BAT',
  ghi_chu     TEXT
);
"""


def _khoi_tao() -> None:
    with SO.ket_noi() as cn:
        cn.executescript(_SCHEMA)


def nhap_tu_thu_vien() -> dict:
    """Chuyen danh sach da duyet tay tu `thu_vien.db` sang so chinh.

    `thu_vien.db` la kho cua he TRUOC 15/08. Giu danh sach o do nghia la
    `evolution` khong bao gio thay, va bo lap lich phai mo hai co so du lieu.
    """
    _khoi_tao()
    if not THU_VIEN.exists():
        return {"nhap": 0, "ly_do": "khong thay thu_vien.db"}
    c = sqlite3.connect(THU_VIEN)
    c.row_factory = sqlite3.Row
    try:
        dong = c.execute("SELECT * FROM theo_doi").fetchall()
    except Exception:
        return {"nhap": 0, "ly_do": "thu_vien.db khong co bang theo_doi"}
    finally:
        c.close()
    n = 0
    with SO.ket_noi() as cn:
        for r in dong:
            ma = f"{r['truy_cap']}::{(r['ten'] or r['url'])[:60]}"
            cn.execute(
                "INSERT INTO theo_doi(ma,loai,ten,url,nen_tang,chu_ky_giay,"
                "lan_quet,trang_thai,ghi_chu) VALUES(?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(ma) DO NOTHING",
                (ma, r["loai"], r["ten"], r["url"], r["truy_cap"],
                 CHU_KY_KHOI_DIEM, float(r["lan_quet_cuoi"] or 0),
                 # CHUAN HOA trang thai. `thu_vien.db` dung 'THEO_DOI', bang nay
                 # dung 'BAT'. Nhap nguyen si thi `den_han()` loc theo 'BAT' tra
                 # ve RONG - 9 kenh qua han 28 ngay ma bo lap lich bao "khong co
                 # gi den han", khong mot loi bao. Da sap that luc 21:2x 11/09.
                 ("TAT" if str(r["trang_thai"] or "").upper() in ("TAT", "DUNG",
                                                                 "NGUNG")
                  else "BAT"),
                 r["ghi_chu"]))
            n += 1
    return {"nhap": n}


def them(ma: str, url: str, nen_tang: str, ten: str = "", loai: str = "",
         ghi_chu: str = "") -> dict:
    _khoi_tao()
    with SO.ket_noi() as cn:
        cn.execute(
            "INSERT INTO theo_doi(ma,loai,ten,url,nen_tang,chu_ky_giay,ghi_chu) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(ma) DO UPDATE SET url=excluded.url",
            (ma, loai, ten or ma, url, nen_tang, CHU_KY_KHOI_DIEM, ghi_chu))
    return {"nhan": True}


def den_han() -> list[dict]:
    _khoi_tao()
    bay_gio = time.time()
    return [dict(r) for r in SO.nhieu(
        "SELECT * FROM theo_doi WHERE trang_thai='BAT' ORDER BY lan_quet")
        if bay_gio - float(r["lan_quet"] or 0) >= float(r["chu_ky_giay"] or CHU_KY_KHOI_DIEM)]


def _chu_ky_moi(cu: float, bai_moi: int) -> float:
    """Co bai moi -> quet day hon; khong co -> gian ra. Cung nguyen tac
    `vuon_nguon`: thoi luong di theo SUAT do duoc, khong theo lich cung."""
    moi = cu * (0.6 if bai_moi >= 2 else 0.85 if bai_moi == 1 else 1.6)
    return max(CHU_KY_MIN, min(CHU_KY_MAX, moi))


def quet_youtube(url: str, so_muc: int = 15) -> dict:
    """Liet ke video moi cua mot kenh roi lay phu de cho cai CHUA co."""
    from . import doc_video as DV
    import yt_dlp
    u = url.rstrip("/")
    if "/@" in u and not u.endswith(("/videos", "/streams")):
        u += "/videos"
    opt = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist",
           "playlistend": so_muc, "socket_timeout": 25, "retries": 2}
    try:
        with yt_dlp.YoutubeDL(opt) as y:
            info = y.extract_info(u, download=False)
    except Exception as e:
        return {"nhan": False, "ly_do": f"{type(e).__name__}: {str(e)[:120]}"}

    moi, da_co, hong, chan = 0, 0, 0, 0
    for x in (info.get("entries") or []):
        vid = x.get("id")
        if not vid:
            continue
        v = f"https://www.youtube.com/watch?v={vid}"
        if SO.mot("SELECT id FROM noi_dung WHERE url LIKE ? AND kieu = ?",
                  f"%{vid}%", DV.KIEU):
            da_co += 1
            continue
        kq = DV.phu_de(v)
        if kq["nhan"] and DV.ghi(v, kq):
            moi += 1
        elif _LA_CHAN(kq.get("ly_do") or ""):
            chan += 1
        else:
            hong += 1
        time.sleep(NGHI_GIUA_VIDEO)
    return {"nhan": True, "kenh": info.get("title"), "bai_moi": moi,
            "da_co": da_co, "khong_lay_duoc": hong, "bi_chan": chan}


def quet_mot(r: dict, so_muc: int = 15) -> dict:
    nt = (r.get("nen_tang") or "").lower()
    if nt in ("youtube", "yt"):
        kq = quet_youtube(r["url"], so_muc)
    else:
        # RSS / blog da co duong rieng (`nguon_bai_viet`); telegram co `telegram.py`.
        kq = {"nhan": False, "ly_do": f"nen tang {nt!r} chua co duong quet o day"}
    bai_moi = int(kq.get("bai_moi") or 0)
    bi_chan = int(kq.get("bi_chan") or 0)
    # BI CHAN thi GIU NGUYEN chu ky va KHONG ghi `lan_quet` moi: lan quet nay
    # khong noi duoc gi ve nguon, nen no khong duoc quyen doi lich cua nguon.
    if bi_chan and not bai_moi:
        with SO.ket_noi() as cn:
            cn.execute("UPDATE theo_doi SET so_lan=so_lan+1, "
                       "ghi_chu=? WHERE ma=?",
                       (f"CHUA_DO_DUOC {time.strftime('%Y-%m-%d %H:%M')}: bi chan "
                        f"{bi_chan} video", r["ma"]))
        return {**kq, "ma": r["ma"], "trang_thai": "CHUA_DO_DUOC"}
    with SO.ket_noi() as cn:
        cn.execute(
            "UPDATE theo_doi SET lan_quet=?, so_lan=so_lan+1, bai_moi=?, "
            "thu_hoach=thu_hoach+?, chu_ky_giay=? WHERE ma=?",
            (time.time(), bai_moi, bai_moi,
             _chu_ky_moi(float(r.get("chu_ky_giay") or CHU_KY_KHOI_DIEM), bai_moi),
             r["ma"]))
    return {**kq, "ma": r["ma"], "trang_thai": "DO_DUOC"}


def mot_luot(toi_da: int = 5, so_muc: int = 15) -> dict:
    ds = den_han()[:toi_da]
    ket = [quet_mot(r, so_muc) for r in ds]
    return {"den_han": len(den_han()), "da_quet": len(ket),
            "bai_moi": sum(int(k.get("bai_moi") or 0) for k in ket),
            "chi_tiet": ket}


def bang() -> list[dict]:
    _khoi_tao()
    return [dict(r) for r in SO.nhieu(
        "SELECT ma,ten,nen_tang,chu_ky_giay,lan_quet,so_lan,thu_hoach,trang_thai "
        "FROM theo_doi ORDER BY thu_hoach DESC, ma")]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "nhap":
        print(json.dumps(nhap_tu_thu_vien(), ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "quet":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        print(json.dumps(mot_luot(n), ensure_ascii=False, indent=1))
    else:
        for r in bang():
            cho = (time.time() - float(r["lan_quet"] or 0)) / 86400
            print(f"  {r['ten'][:38]:40s} {r['nen_tang'][:9]:10s} "
                  f"chu ky {float(r['chu_ky_giay'])/86400:4.1f}d · "
                  f"cach {cho:5.1f}d · thu {r['thu_hoach']}")
