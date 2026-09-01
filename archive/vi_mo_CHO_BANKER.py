# -*- coding: utf-8 -*-
"""vi_mo.py - LOP BIAS: bien du lieu vi mo cua BANKER thanh mot chuoi diem so.

VI SAO CO FILE NAY (01/09/2026). BANKER thu 27 seri vi mo tu 1954 vao `nao.db`
va **khong module nao trong duong kiem dinh doc chung**. Cung luc do, van de
`hieu_chuan_v6` mo tu 15/08 vi cong PASS chua bao gio duoc thu bang V6 THAT -
ma dieu kien dau tien cua V6 la lop "bias > 0". Hai su that do la mot: khong
noi day duoc thi khong thu duoc.

DINH NGHIA - lay dung `system_final.build_signals` cua Phase 1, khong sang tac:

    bias = (0,25*vi_mo + 0,10*vix_nghich + 0,25*mua_vu) / 0,60

Ban goc con thanh phan thu tu, `flow_inv_score` (trong so 0,10), tinh tu khoi
luong ETF. Kho vi mo cua lab chi co 2 nam ETF (tu 2024-08) nen thanh phan do
KHONG tai tao duoc tren 15 nam. Ta bo no va noi ro la da bo - chinh ban goc
cung co san cau hinh nay duoi ten `combined_fixed`. Cai khong duoc lam la lang
le chia cho 0,70 nhu the van con du bon thanh phan.

BA CHO DE NHIN TRUOC, da chan het o day:
  1. **Do tre cong bo.** Moi seri co `LAG` rieng theo lich cong bo that (CPI ra
     sau ~2 tuan). Gia tri ngay t chi duoc dung tu t+lag.
  2. **Chuan hoa.** z-score la ROLLING 252 phien, khong phai toan mau. z toan
     mau dung trung binh cua ca tuong lai de cham diem qua khu.
  3. **Diem mua vu.** Ban `gan_cung` (bang thang cua Phase 1) duoc rut ra tu
     CHINH giai doan backtest -> in-sample, da do that: IC +0,057 thoi len tu
     +0,029. Ban `pit` tinh lai moi nam chi bang cac nam TRUOC do. Mac dinh la
     `pit`; ban `gan_cung` giu lai de doi chieu, khong de ket luan.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhan import so as SO

#: Do tre cong bo (so ngay lich) cua tung seri. Gia tri mang nhan ngay t chi
#: duoc phep dung tu ngay t + LAG. Lay tu `moneyflow_backtest.FRED_SERIES`.
LAG_NGAY = {"DGS2": 1, "DGS10": 1, "T10YIE": 1, "VIXCLS": 1, "DFF": 1,
            "T10Y2Y": 1, "CPIAUCSL": 15, "UNRATE": 15, "NFCI": 5, "WALCL": 5}

#: Trong so bias. Ban Phase 1 con `flow_inv_score: 0,10` - xem docstring.
TRONG_SO = {"vi_mo": 0.25, "vix_nghich": 0.10, "mua_vu": 0.25}

#: Thanh phan cua ban goc KHONG tai tao duoc o day, de bao cao noi ra duoc.
THIEU = {"dong_tien": 0.10}

#: Cua so z-score. 252 phien = mot nam giao dich.
CUA_SO_Z = 252
#: So mau toi thieu truoc khi z-score co nghia.
MAU_TOI_THIEU_Z = 60

#: Bang diem thang GAN CUNG cua Phase 1. IN-SAMPLE - chi dung de doi chieu.
DIEM_THANG = {1: 0.4, 2: -0.1, 3: 0.0, 4: 0.5, 5: -0.5, 6: -0.4,
              7: 1.0, 8: -0.3, 9: -1.0, 10: 0.1, 11: 0.6, 12: 0.8}
DIEM_NHIEM_KY = {1: 0.3, 2: -0.5, 3: 0.5, 4: 0.0}
THANG_HALLOWEEN = (11, 12, 1, 2, 3, 4)
#: Nam bau cu tong thong My gan nhat, dung lam moc chu ky 4 nam.
NAM_MOC_BAU_CU = 2024


# ---------------------------------------------------------------- DOC SO CAI
def seri(ma: str) -> pd.Series:
    """Mot seri vi mo tu `nao.db`, index la ngay (naive, da chuan hoa)."""
    dong = SO.nhieu("SELECT ngay, gia_tri FROM vi_mo WHERE seri=? ORDER BY ngay", ma)
    if not dong:
        return pd.Series(dtype="float64")
    s = pd.Series([float(d["gia_tri"]) for d in dong],
                  index=pd.to_datetime([d["ngay"] for d in dong], errors="coerce"))
    return s[s.index.notna()].sort_index()


def co_seri(cac_ma) -> dict:
    """So diem cua tung seri - de bao cao phan biet 'khong co' voi 'bang 0'."""
    return {m: len(seri(m)) for m in cac_ma}


def _gong(s: pd.Series, index: pd.DatetimeIndex, lag_ngay: int) -> pd.Series:
    """Dua mot seri vi mo len luoi thoi gian cua bang gia, DA tre cong bo.

    Ba buoc, thu tu khong doi cho nhau duoc:
      1. day ngay len `lag_ngay` (gia tri cua t chi biet tu t+lag),
      2. ffill sang cac ngay khong cong bo (cuoi tuan, ngay le),
      3. lay dung cac moc cua bang gia.

    Bang gia co the tz-aware (kho lab co ca hai loai) con seri vi mo luon la
    ngay lich naive; so sanh truc tiep hai loai do nem TypeError.
    """
    if s.empty:
        return pd.Series(np.nan, index=index)
    s = s.copy()
    s.index = s.index + pd.Timedelta(days=int(lag_ngay))
    s = s[~s.index.duplicated(keep="last")]
    moc = pd.DatetimeIndex(index)
    if moc.tz is not None:
        moc_ngay = moc.tz_convert("UTC").tz_localize(None).normalize()
    else:
        moc_ngay = moc.normalize()
    hop = s.reindex(s.index.union(pd.DatetimeIndex(moc_ngay).unique())).sort_index().ffill()
    ra = pd.Series(hop.reindex(moc_ngay).to_numpy(), index=index)
    return ra


def _z(s: pd.Series) -> pd.Series:
    """z-score ROLLING. Khong duoc dung z toan mau: no cham diem nam 2011 bang
    trung binh co ca nam 2025 trong do."""
    tb = s.rolling(CUA_SO_Z, min_periods=MAU_TOI_THIEU_Z).mean()
    sd = s.rolling(CUA_SO_Z, min_periods=MAU_TOI_THIEU_Z).std()
    return (s - tb) / (sd + 1e-9)


# ------------------------------------------------------------ CAC THANH PHAN
def diem_vi_mo(index: pd.DatetimeIndex) -> pd.Series:
    """Loi suat THUC thap + duong cong doc = thuan co phieu.

    Cong thuc cua `moneyflow_backtest.compute_scores`, giu nguyen trong so
    0,45 / 0,25 / 0,30 va phep chia 2 de ve [-1, 1].
    """
    y10 = _gong(seri("DGS10"), index, LAG_NGAY["DGS10"])
    y2 = _gong(seri("DGS2"), index, LAG_NGAY["DGS2"])
    be = _gong(seri("T10YIE"), index, LAG_NGAY["T10YIE"])
    thuc = y10 - be
    cong = y10 - y2
    diem = ((-_z(thuc)).clip(-2, 2) * 0.45
            + (-np.sign(thuc.diff(20))) * 0.25
            + _z(cong).clip(-2, 2) * 0.30)
    return (diem / 2.0).clip(-1, 1)


def diem_vix_nghich(index: pd.DatetimeIndex) -> pd.Series:
    """VIX cao/tang = MUA (da dao dau).

    Chieu nay la chieu DA SUA. Ban predictor goc doc nguoc (VIX cao = ban) va
    khoi do am tinh; memory `moneyflow-bias-edge` ghi ca hai khoi VIX va dong
    tien deu bi doc nguoc truoc ban 7.2.
    """
    vix = _gong(seri("VIXCLS"), index, LAG_NGAY["VIXCLS"])
    tb = vix.rolling(20, min_periods=10).mean()
    diem = (-np.sign(vix - tb) * (_z(vix).abs().clip(0, 2) / 2)).clip(-1, 1)
    return -diem


def diem_mua_vu_gan_cung(index: pd.DatetimeIndex) -> pd.Series:
    """Bang diem thang GAN CUNG cua Phase 1. IN-SAMPLE - chi de doi chieu."""
    thang = pd.Index(index).month.to_numpy()
    nam = pd.Index(index).year.to_numpy()
    ky = ((nam - NAM_MOC_BAU_CU) % 4) + 1
    diem = np.array([DIEM_THANG[int(m)] + DIEM_NHIEM_KY[int(k)]
                     + (0.2 if int(m) in THANG_HALLOWEEN else -0.15)
                     for m, k in zip(thang, ky)])
    return pd.Series(np.clip(diem, -1, 1), index=index)


def diem_mua_vu_pit(close: pd.Series, so_nam_toi_thieu: int = 10) -> pd.Series:
    """Diem mua vu TU SUY RA, point-in-time.

    Diem cua nam Y = loi nhuan trung binh tung thang tinh CHI TREN cac nam
    < Y, chuan hoa ve [-1, 1]. Truoc khi du `so_nam_toi_thieu` nam thi tra 0 -
    "khong co y kien" chu khong phai "trung tinh vi mo hinh noi the".
    """
    r = close.pct_change()
    b = pd.DataFrame({"r": r.to_numpy(),
                      "nam": pd.Index(close.index).year.to_numpy(),
                      "thang": pd.Index(close.index).month.to_numpy()}).dropna()
    if b.empty:
        return pd.Series(0.0, index=close.index)
    theo_thang = (b.groupby(["nam", "thang"])["r"]
                  .apply(lambda x: float((1 + x).prod() - 1)).reset_index())
    diem = pd.Series(0.0, index=close.index)
    nam_co = sorted(theo_thang["nam"].unique())
    nam_index = pd.Index(close.index).year.to_numpy()
    thang_index = pd.Index(close.index).month.to_numpy()
    for i, nam in enumerate(nam_co):
        if i < so_nam_toi_thieu:
            continue
        qua_khu = theo_thang[theo_thang["nam"] < nam]
        tb = qua_khu.groupby("thang")["r"].mean()
        sd = tb.std()
        if not np.isfinite(sd) or sd == 0:
            continue
        z = (tb / (sd * 2)).clip(-1, 1)
        mask = nam_index == nam
        if mask.any():
            diem.iloc[np.flatnonzero(mask)] = pd.Index(thang_index[mask]).map(z).to_numpy()
    return diem.fillna(0.0)


# ---------------------------------------------------------------------- BIAS
def bias(df: pd.DataFrame, mua_vu: str = "pit") -> pd.Series:
    """Diem bias tong hop tren luoi thoi gian cua `df`. Duong = thuan mua.

    `mua_vu`: "pit" (mac dinh, khong nhin truoc) hoac "gan_cung" (ban Phase 1).
    """
    index = df.index
    tp = {"vi_mo": diem_vi_mo(index), "vix_nghich": diem_vix_nghich(index)}
    if mua_vu == "gan_cung":
        tp["mua_vu"] = diem_mua_vu_gan_cung(index)
    elif mua_vu == "pit":
        tp["mua_vu"] = diem_mua_vu_pit(df["close"])
    else:
        raise ValueError(f"mua_vu phai la 'pit' hoac 'gan_cung', nhan {mua_vu!r}")
    tong_ts = sum(TRONG_SO.values())
    ra = sum(tp[k].fillna(0.0) * v for k, v in TRONG_SO.items()) / tong_ts
    return ra.clip(-1, 1)


def chan_doan(df: pd.DataFrame) -> dict:
    """Lop bias nay dung duoc den dau tren `df`? Bao cao truoc khi ket luan."""
    dem = co_seri(["DGS10", "DGS2", "T10YIE", "VIXCLS"])
    b_vm = diem_vi_mo(df.index)
    b_vx = diem_vix_nghich(df.index)
    return {
        "seri_diem": dem,
        "seri_thieu": [k for k, v in dem.items() if v == 0],
        "thanh_phan_bo": THIEU,
        "phu_vi_mo": float(b_vm.notna().mean()),
        "phu_vix": float(b_vx.notna().mean()),
        "bar": len(df),
    }
