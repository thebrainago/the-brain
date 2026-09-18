# -*- coding: utf-8 -*-
"""tai_tro.py - CARRY cua mot vi the chi so giu qua dem.

Giu US500CASH qua dem co HAI dong tien ma phan con lai cua he chua he dem:

  1. LAI SUAT TAI TRO (tru). San tinh phi tren TOAN BO notional, khong chi
     phan vay. Cong thuc san: (lai suat co so + markup) * notional * ngay/365.
     `chi_phi.MoHinhChiPhi.phi_giu_mang` da nhan `lai_suat_nam` nhung truoc
     03/09/2026 chua ai cap chuoi that vao - moi cho goi deu de None, tuc dung
     mot hang so KHAI.

  2. DIEU CHINH CO TUC (cong). CFD chi so tra dieu chinh co tum cho lenh MUA
     (va thu cua lenh BAN). Chuoi gia ta backtest la CHI SO GIA, khong co co
     tuc. O don bay L, bo qua khoan nay la tu vut di L * ~1,8 %/nam.

CAI THU HAI la lo hong nang hon, vi no LON va vi no THIEN LECH mot chieu: moi
ket luan "he chon loc thua mua-giu" tinh tren chi so gia deu dang phat lenh
mua-giu mot khoan phat khong co that... va nguoc lai moi ket luan ve don bay
deu dang bo qua phan thuong that cua viec giu.

DO DUOC HAY KHAI. Ca hai chuoi deu phai DO:
  - lai suat: DFF (Fed Funds hieu luc, hang ngay) tu `nao.db` bang `vi_mo`,
    1954-07-01 tro di. Do la lai suat CO SO; markup rieng tung san nam trong
    `chi_phi` (da do lien san: FXCE 1,31 / XM 5,51 / Exness 6,83 %/nam).
  - co tuc: KHONG khai bao "1,8%". Do bang HIEU giua chi so tong loi suat
    (^SP500TR) va chi so gia (^GSPC) tren cung ngay. Co tu 1988-01-04, la khi
    ^SP500TR bat dau. Truoc do -> do_tin='KHAI', khong duoc lam dieu kien PASS.
"""
from __future__ import annotations

import json
import sqlite3
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent.parent
DATA = GOC / "data"          # 18/09: ve trong lab/ — goc du an chi con
                            # The Brain, Phase 1 nam trong sp500_phase1/
NAO = GOC / "nao.db"

CO_TUC_FILE = DATA / "sp500_co_tuc_do.parquet"
_UA = {"User-Agent": "Mozilla/5.0"}


# --------------------------------------------------------------- LAI SUAT
def _doc_dff() -> pd.Series:
    with sqlite3.connect(f"file:{NAO}?mode=ro", uri=True) as c:
        rows = c.execute(
            "select ngay, gia_tri from vi_mo where seri='DFF' order by ngay"
        ).fetchall()
    if not rows:
        raise RuntimeError("nao.db khong co seri DFF - chay BANKER truoc")
    s = pd.Series([float(v) for _, v in rows],
                  index=pd.to_datetime([d for d, _ in rows]), name="DFF")
    return s / 100.0          # % -> ti le


def lai_suat_nam(index: pd.DatetimeIndex) -> tuple[np.ndarray, str]:
    """Lai suat CO SO theo tung bar (ti le/nam). Tra (mang, do_tin).

    Ngay truoc 1954-07-01 khong co DFF -> giu gia tri dau tien va ha do_tin.
    """
    dff = _doc_dff()
    idx = pd.DatetimeIndex(index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    # bfill PHAI chay trUOC khi thu ve idx: neu ca doan nam truoc 1954 thi sau
    # `.reindex(idx)` khong con gia tri nao de lap nguoc. (Loi 03/09/2026:
    # doan 1928-1949 tra ve toan NaN -> nanmean canh bao -> vol = 0.)
    v = dff.reindex(dff.index.union(idx)).ffill().bfill().reindex(idx)
    ngoai = int(((idx < dff.index[0]) | (idx > dff.index[-1])).sum())
    return v.to_numpy(dtype=float), ("DO" if ngoai == 0 else "KHAI")


# ----------------------------------------------------------------- CO TUC
def _yahoo(ma: str) -> pd.Series:
    u = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ma}"
         f"?period1=0&period2=9999999999&interval=1d")
    d = json.loads(urllib.request.urlopen(
        urllib.request.Request(u, headers=_UA), timeout=60).read())
    k = d["chart"]["result"][0]
    t = pd.to_datetime(k["timestamp"], unit="s").normalize()
    c = k["indicators"]["quote"][0]["close"]
    s = pd.Series(c, index=t, name=ma).dropna()
    return s[~s.index.duplicated(keep="last")]


def do_co_tuc(lam_moi: bool = False) -> pd.DataFrame:
    """Do suat co tuc SP500 = loi suat ^SP500TR tru loi suat ^GSPC.

    Tra DataFrame [suat_ngay, suat_nam_365] theo ngay. Luu ra parquet.
    """
    if CO_TUC_FILE.exists() and not lam_moi:
        return pd.read_parquet(CO_TUC_FILE)
    gia = _yahoo("%5EGSPC")
    tong = _yahoo("%5ESP500TR")
    chung = gia.index.intersection(tong.index)
    gia, tong = gia.reindex(chung), tong.reindex(chung)
    rg = np.log(gia).diff()
    rt = np.log(tong).diff()
    d = (rt - rg).dropna()
    # KHONG cat tung ngay ve 0. Hai chuoi lech nhau vi lam tron va vi gio chot
    # khac nhau; nhieu do DOI XUNG, nen cat mot chieu la tu bom thien lech
    # DUONG. Do that 03/09/2026: cat ngay -> suat thap ky 2010 ra 2,84 %/nam
    # (that ~1,9). Cong don 252 phien roi moi doc thi nhieu tu triet.
    ra = pd.DataFrame({"suat_ngay": d,
                       "suat_nam_365": d.rolling(252).sum()})
    ra = ra.dropna()
    ra["suat_nam_365"] = ra["suat_nam_365"].clip(0.0, 0.12)
    DATA.mkdir(parents=True, exist_ok=True)
    ra.to_parquet(CO_TUC_FILE)
    return ra


def co_tuc_nam(index: pd.DatetimeIndex) -> tuple[np.ndarray, str]:
    """Suat co tuc (ti le/nam) theo tung bar. Tra (mang, do_tin).

    do_tin='DO' khi MOI bar nam trong khoang do duoc (1988+). Mot bar ngoai
    khoang la ha ca chuoi xuong 'KHAI' - khong duoc lam dieu kien PASS.
    """
    ct = do_co_tuc()["suat_nam_365"]
    idx = pd.DatetimeIndex(index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    idx = idx.normalize()
    v = ct.reindex(ct.index.union(idx)).ffill().bfill().reindex(idx)
    ngoai = int(((idx < ct.index[0]) | (idx > ct.index[-1])).sum())
    return v.to_numpy(dtype=float), ("DO" if ngoai == 0 else "KHAI")


def carry_rong_nam(index: pd.DatetimeIndex, markup_nam: float,
                   huong: float = 1.0) -> tuple[np.ndarray, str]:
    """Carry RONG cua vi the MUA 1 don vi notional (ti le/nam, DUONG = duoc an).

    = co tuc - (lai suat co so + markup).
    Day chinh la thu quyet dinh don bay co lai hay khong.
    """
    ls, t1 = lai_suat_nam(index)
    ct, t2 = co_tuc_nam(index)
    do_tin = "DO" if (t1 == "DO" and t2 == "DO") else "KHAI"
    return huong * (ct - ls - markup_nam), do_tin
