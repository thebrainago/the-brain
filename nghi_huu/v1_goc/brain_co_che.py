# -*- coding: utf-8 -*-
"""
brain_co_che.py - DONG CO TANG KHAM PHA (TAP SANG)
=====================================================================================
Day la manh con thieu cua vong lap 24/7: `brain_vong_lap.chay_sang()` goi
`brain_co_che.do_ic(muc_tieu, tham_so)` va truoc file nay thi khong co ai tra loi.

VAI TRO: tra loi cac KHANG DINH NGUYEN TU trong `BRAIN_khang_dinh.parquet`.
Moi khang dinh = 1 ham o day. Tra loi 1 khang dinh = tra loi CA CHUM phuong phap
dung no (Elliott/Harmonic/ICT/Wyckoff/Gann/VSA...).

KY LUAT BAT BUOC (vi pham la hong ca kien truc):
  1. CHI chay tren TAP SANG. Tap xac nhan (chi so My + du lieu MT5) bi CAM cham vao.
     Ham `nap()` tu chan; khong co duong vong.
  2. Ket qua o day KHONG BAO GIO duoc goi la edge. No chi de xep hang uu tien.
  3. Moi thong ke phai NHAN QUA: chi dung thong tin co tai thoi diem do. Chan song
     duoc "xac nhan tai" bar nao thi tu bar do moi duoc dung.
  4. Moi khang dinh phai co PLACEBO rieng va phai noi ro null la gi.

Bay da sap tren du an nay, da ma hoa san o day:
  - Bar rac truoc 2006: open=high=low=close (chi so cu tren Yahoo). Loc o `nap()`.
  - Rau nen hong: low < min(open,close)*0,90 ma close ve cho cu -> cat (quy tac 48).
  - IC duong on dinh KHONG DU (co che VIX: IC +0,106 nhung placebo 10,2%).
  - Placebo sat nguong = truot. Chay nhieu hat.
  - Tuong quan cheo thi truong lam Stouffer thoi phong -> luon bao kem PHEP THU DAU.

CLI:
  python brain_co_che.py --liet-ke
  python brain_co_che.py --chay elliott_luan_phien
  python brain_co_che.py --tat-ca            # chay het, ghi reports/BRAIN_CO_CHE.md
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
DATA = HERE / "data"
REPORTS = HERE / "reports"
REPORTS.mkdir(exist_ok=True)
RA_MD = REPORTS / "BRAIN_CO_CHE.md"

HAT = [11, 13, 17, 29, 41]          # nhieu hat - vi verdict tung doi theo hat (95,8 vs 94,8)
SO_LAN_HOAN_VI = 2000


# ---------------------------------------------------------------------------
# TAP SANG vs TAP XAC NHAN
# ---------------------------------------------------------------------------
# Ranh gioi chon theo NOI DU AN SE GIAO DICH: V6 chay tren chi so My, va moi so
# lieu MT5 la so lieu cua cong cu that -> de danh cho tang xac nhan, khong duoc
# nhin trong luc sang. Chau Au / chau A / hang hoa / FX major thi thoai mai.
TAP_SANG = [
    # chi so ngoai My
    "dax", "ftse100", "cac40", "eustoxx50", "aex", "ibex35", "smi",
    "nikkei", "hangseng", "asx200", "kospi", "taiwan", "sensex", "tsx", "bovespa",
    # hang hoa
    "vang", "bac", "dong", "dauwti", "khidot", "ngo", "dautuong",
    # FX
    "eurusd", "gbpusd", "usdjpy", "audusd", "usdcad", "usdchf",
]
TAP_XAC_NHAN = ["sp500", "dowjones", "nasdaq", "russell2000", "us500cash", "us500m"]

# Thi truong co khoi luong THAT (Yahoo tra volume=0 cho chi so tong hop va FX)
CO_KHOI_LUONG = ["dax", "nikkei", "hangseng", "asx200", "kospi", "taiwan",
                 "tsx", "bovespa", "ftse100", "cac40", "aex", "ibex35", "smi",
                 "vang", "bac", "dong", "dauwti", "khidot", "ngo", "dautuong"]


class ViPhamTapXacNhan(Exception):
    """Nem ra khi co ai do co doc tap xac nhan tu tang kham pha."""


def nap(khoa, tap="sang"):
    """Nap 1 thi truong cua TAP SANG. Tu chan neu goi vao tap xac nhan.

    Tra ve DataFrame index=time, cot open/high/low/close/volume, DA LOC bar rac.
    """
    if khoa in TAP_XAC_NHAN:
        raise ViPhamTapXacNhan(
            f"'{khoa}' thuoc TAP XAC NHAN. Tang kham pha khong duoc nhin. "
            f"Muon dung no thi phai lap ho so trinh ky va tra ngan sach FDR.")
    if tap != "sang":
        raise ViPhamTapXacNhan("brain_co_che chi phuc vu tap='sang'.")

    f = DATA / f"yh_{khoa}_daily.parquet"
    if not f.exists():
        return None
    df = pd.read_parquet(f)
    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    df = df[df["close"] > 0].sort_index()

    # Bay 1: bar rac cua chi so cu tren Yahoo - OHLC bang nhau het (khong co bien do
    # trong ngay). Giu lai thi moi thong ke ve HINH DANG nen deu vo nghia.
    bar_det = (df["high"] <= df["low"] * (1 + 1e-9))
    # cat tu diem ma du lieu bat dau co bien do that (250 bar lien tuc >=90% co bien do)
    tot = (~bar_det).rolling(250).mean()
    if (tot >= 0.90).any():
        df = df.loc[tot[tot >= 0.90].index[0]:]
    df = df[~(df["high"] <= df["low"] * (1 + 1e-9))]

    # Bay 2 (quy tac 48): rau nen hong trong lich su. Rau hong = gia dong cua ve
    # nguyen cho cu ngay trong bar do. Nguong 10% giu duoc SNB 2015 / Brexit / 2008.
    than_duoi = np.minimum(df["open"], df["close"])
    than_tren = np.maximum(df["open"], df["close"])
    hong = (df["low"] < than_duoi * 0.90) | (df["high"] > than_tren * 1.10)
    df = df[~hong]

    return df if len(df) >= 750 else None


def nap_tap_sang(chi_co_khoi_luong=False):
    ds = CO_KHOI_LUONG if chi_co_khoi_luong else TAP_SANG
    ra = {}
    for k in ds:
        if k not in TAP_SANG:
            continue
        d = nap(k)
        if d is None:
            continue
        if chi_co_khoi_luong and (d["volume"] > 0).mean() < 0.80:
            continue
        ra[k] = d
    return ra


# ---------------------------------------------------------------------------
# CHAN SONG NHAN QUA - nen mong cua moi khang dinh ve "song"
# ---------------------------------------------------------------------------

def atr(df, n=14):
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"] - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def chan_song(df, he_so=3.0, n_atr=14):
    """Zigzag NHAN QUA: chan chi duoc XAC NHAN khi gia dao nguoc he_so*ATR.

    Khac zigzag thong thuong o mot diem song con: moi chan ghi CA HAI moc thoi gian
      vi_tri     - bar ma dinh/day that su nam
      xac_nhan   - bar ma ta MOI BIET no la dinh/day
    Moi thong ke phia sau chi duoc dung thong tin tai `xac_nhan`. Zigzag thuong
    khong co cot thu hai, va do la ly do moi backtest Elliott/Harmonic la hu cau.

    Tra ve DataFrame: vi_tri, xac_nhan, gia, loai (+1 dinh / -1 day)
    """
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    a = atr(df, n_atr).to_numpy()
    n = len(df)

    chan = []
    huong = 0            # +1 dang tim dinh, -1 dang tim day
    cuc_tri_i, cuc_tri_g = None, None

    for i in range(n_atr + 1, n):
        nguong = he_so * a[i]
        if not np.isfinite(nguong) or nguong <= 0:
            continue

        if huong == 0:
            if cuc_tri_i is None:
                cuc_tri_i, cuc_tri_g = i, c[i]
                dinh_i, dinh_g, day_i, day_g = i, h[i], i, l[i]
                continue
            if h[i] > dinh_g:
                dinh_i, dinh_g = i, h[i]
            if l[i] < day_g:
                day_i, day_g = i, l[i]
            if c[i] < dinh_g - nguong:
                chan.append((dinh_i, i, dinh_g, +1)); huong = -1
                cuc_tri_i, cuc_tri_g = i, l[i]
            elif c[i] > day_g + nguong:
                chan.append((day_i, i, day_g, -1)); huong = +1
                cuc_tri_i, cuc_tri_g = i, h[i]
            continue

        if huong == +1:                       # dang tim DINH
            if h[i] > cuc_tri_g:
                cuc_tri_i, cuc_tri_g = i, h[i]
            elif c[i] < cuc_tri_g - nguong:
                chan.append((cuc_tri_i, i, cuc_tri_g, +1))
                huong = -1
                cuc_tri_i, cuc_tri_g = i, l[i]
        else:                                  # dang tim DAY
            if l[i] < cuc_tri_g:
                cuc_tri_i, cuc_tri_g = i, l[i]
            elif c[i] > cuc_tri_g + nguong:
                chan.append((cuc_tri_i, i, cuc_tri_g, -1))
                huong = +1
                cuc_tri_i, cuc_tri_g = i, h[i]

    if not chan:
        return pd.DataFrame(columns=["vi_tri", "xac_nhan", "gia", "loai"])
    return pd.DataFrame(chan, columns=["vi_tri", "xac_nhan", "gia", "loai"])


def cac_doan(df, ch):
    """Doan = tu chan i toi chan i+1. Do dai theo log gia, thoi luong theo bar.

    `biet_tai` = bar ma doan nay duoc xac nhan xong (= xac_nhan cua chan cuoi doan).
    """
    if len(ch) < 2:
        return pd.DataFrame()
    g = ch["gia"].to_numpy()
    v = ch["vi_tri"].to_numpy()
    x = ch["xac_nhan"].to_numpy()
    lo = ch["loai"].to_numpy()

    d = pd.DataFrame({
        "tu": v[:-1], "den": v[1:], "biet_tai": x[1:],
        "gia_tu": g[:-1], "gia_den": g[1:],
        "huong": -lo[:-1],                       # tu day -> len, tu dinh -> xuong
        "thoi_luong": (v[1:] - v[:-1]).astype(float),
    })
    d["do_dai"] = np.abs(np.log(d["gia_den"] / d["gia_tu"]))
    d = d[(d["thoi_luong"] > 0) & np.isfinite(d["do_dai"])]
    d["do_doc"] = d["do_dai"] / d["thoi_luong"]
    return d.reset_index(drop=True)


# ---------------------------------------------------------------------------
# THONG KE + PLACEBO
# ---------------------------------------------------------------------------

def spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 20:
        return np.nan
    ra = pd.Series(a[m]).rank().to_numpy()
    rb = pd.Series(b[m]).rank().to_numpy()
    if ra.std() == 0 or rb.std() == 0:
        return np.nan
    return float(np.corrcoef(ra, rb)[0, 1])


def _z_tu_p(p):
    """Nghich dao phan phoi chuan mot phia. Khong dung scipy de vong lap VPS chay
    duoc voi moi truong toi thieu (Acklam, sai so < 1,15e-9)."""
    p = min(max(float(p), 1e-12), 1 - 1e-12)
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = np.sqrt(-2 * np.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q = np.sqrt(-2 * np.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def chuan_hoa(quan_sat, mau_null):
    """Neo thong ke vao NULL CUA CHINH NO thay vi vao so 0.

    Vi sao bat buoc: `gop_thi_truong` gop 28 thi truong bang PHEP THU DAU, ma phep
    thu dau chi dung khi null nam o 0. Nhieu phep do co null LECH KHOI 0 mot cach
    he thong - vi drift, vi ty le long/short, vi loi suat khong doi xung. Luc do dau
    cua so tho khong con nghia gi.
    Da bat duoc that trong phien 09/08: mot phep do co null trung binh -0,0246 con
    quan sat +0,0647; doc dau tho ra "duong nhe", doc theo null ra +2,6 do lech chuan.
    """
    mn = np.asarray([x for x in mau_null if np.isfinite(x)], float)
    if len(mn) < 50 or not np.isfinite(quan_sat):
        return float("nan")
    sd = mn.std()
    return float((quan_sat - mn.mean()) / sd) if sd > 0 else float("nan")


def hoan_vi_p(quan_sat, mau_null, phia="hai"):
    """p theo hoan vi. `mau_null` la mang thong ke duoi gia thuyet khong."""
    mau_null = np.asarray([x for x in mau_null if np.isfinite(x)], float)
    if len(mau_null) < 100 or not np.isfinite(quan_sat):
        return np.nan
    if phia == "hai":
        p = (np.abs(mau_null) >= abs(quan_sat)).mean()
    elif phia == "tren":
        p = (mau_null >= quan_sat).mean()
    else:
        p = (mau_null <= quan_sat).mean()
    return float((p * len(mau_null) + 1) / (len(mau_null) + 1))


# 28 thi truong KHONG PHAI 28 phep thu doc lap: DAX-CAC-AEX tuong quan gan 1, sau
# cap FX deu la ham cua dong do la. Phep thu dau tren 28 dong cho p dep gia tao.
# Nhom lai roi thu dau tren TRUNG VI TUNG NHOM - do moi la so duoc phep tin.
NHOM_TUONG_QUAN = {
    "chau_au": ["dax", "ftse100", "cac40", "eustoxx50", "aex", "ibex35", "smi"],
    "chau_a_tbd": ["nikkei", "hangseng", "asx200", "kospi", "taiwan", "sensex"],
    "chau_my": ["tsx", "bovespa"],
    "kim_loai": ["vang", "bac", "dong"],
    "nang_luong": ["dauwti", "khidot"],
    "nong_san": ["ngo", "dautuong"],
    "fx": ["eurusd", "gbpusd", "usdjpy", "audusd", "usdcad", "usdchf"],
}


def _p_nhi_thuc_2phia(so_duong, n):
    from math import comb
    if n == 0:
        return float("nan")
    k = max(so_duong, n - so_duong)
    return float(min(1.0, 2 * sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n))


def gop_thi_truong(ket, ten_tk):
    """Gop ket qua tung thi truong. Bao CA HAI:
      - phep thu DAU (bao nhieu thi truong cung dau): mien nhiem voi tuong quan cheo
      - Stouffer z: nhay hon nhung BI THOI PHONG khi cac thi truong tuong quan
    Khi hai cai noi khac nhau thi TIN PHEP THU DAU.
    """
    v = np.array([k[ten_tk] for k in ket if np.isfinite(k.get(ten_tk, np.nan))], float)
    ps = np.array([k["p"] for k in ket if np.isfinite(k.get("p", np.nan))], float)
    if len(v) == 0:
        return {}
    duong = int((v > 0).sum())
    n = len(v)
    p_dau = _p_nhi_thuc_2phia(duong, n)

    # phep thu dau theo NHOM - con so duoc phep tin
    theo_nhom = {}
    for nhom, ds in NHOM_TUONG_QUAN.items():
        vv = [k[ten_tk] for k in ket
              if k.get("thi_truong") in ds and np.isfinite(k.get(ten_tk, np.nan))]
        if vv:
            theo_nhom[nhom] = float(np.median(vv))
    nd = sum(1 for x in theo_nhom.values() if x > 0)
    p_nhom = _p_nhi_thuc_2phia(nd, len(theo_nhom))
    # Stouffer mot phia theo dau cua trung vi
    z = np.nan
    if len(ps) == len(v) and len(ps) > 1:
        dau = np.sign(np.median(v)) or 1
        zi = [dau * np.sign(vi) * _z_tu_p(pi) for vi, pi in zip(v, ps)]
        z = float(np.sum(zi) / np.sqrt(len(zi)))
    return {
        "so_thi_truong": n,
        "trung_vi": float(np.median(v)),
        "so_duong": duong,
        "p_phep_thu_dau": float(p_dau),
        "so_nhom": len(theo_nhom),
        "nhom_duong": nd,
        "p_theo_nhom": float(p_nhom),
        "trung_vi_nhom": theo_nhom,
        "stouffer_z": z,
    }


# ---------------------------------------------------------------------------
# CAC KHANG DINH. Moi ham nhan (khoa, df) -> dict(thong_ke, p, n, ...)
# ---------------------------------------------------------------------------

def kd_luan_phien(khoa, df, rng):
    """KD_LUAN_PHIEN - hai dot dieu chinh lien tiep co hinh dang doi lap.

    Elliott noi hai dot dieu chinh lien tiep phai KHAC nhau (nhon <-> phang)
    => tuong quan hang giua hinh dang doan dieu chinh thu i va thu i+1 phai AM.
    Thong ke bao cao = -corr, duong nghia la UNG HO luan phien.

    BAY DA CHAN: neu do hinh dang bang log(do doc) tho thi ket qua bi BIEN DONG CUM
    LAI lam gia - hai doan lien nhau nam trong cung mot che do bien dong nen doc
    giong nhau, va hoan vi thi pha mat cum do => ra "khong luan phien" cuc manh o
    28/28 thi truong ma khong noi len gi ve Elliott. Nen thuoc do CHINH la HIEU QUA
    khong thu nguyen:  do_dai / (ATR% tai luc bat dau * sqrt(thoi luong)).
    Chia cho bien do duong nhien cua buoc di ngau nhien => het phu thuoc che do vol.
    Van bao ca ban tho de doi chieu.
    """
    d = cac_doan(df, chan_song(df))
    if len(d) < 40:
        return None
    # "dieu chinh" = doan nguoc chieu xu the dai han (dung SMA200 nhan qua)
    sma = df["close"].rolling(200).mean().to_numpy()
    xu_the = np.sign(df["close"].to_numpy() - sma)
    hx = xu_the[d["tu"].to_numpy()]
    dc = d[(hx != 0) & (d["huong"].to_numpy() != hx)].copy()
    if len(dc) < 30:
        return None

    # ATR% NHAN QUA tai bar bat dau doan
    atr_pct = (atr(df, 14) / df["close"]).to_numpy()
    a0 = atr_pct[dc["tu"].to_numpy()]
    tl = dc["thoi_luong"].to_numpy()
    hieu_qua = dc["do_dai"].to_numpy() / (a0 * np.sqrt(tl))
    ok = np.isfinite(hieu_qua) & (hieu_qua > 0)
    hieu_qua = hieu_qua[ok]
    if len(hieu_qua) < 30:
        return None
    hinh = np.log(hieu_qua)
    tho = np.log(dc["do_doc"].to_numpy()[ok])

    q = spearman(hinh[:-1], hinh[1:])
    q_tho = spearman(tho[:-1], tho[1:])
    if not np.isfinite(q):
        return None
    null = []
    for _ in range(SO_LAN_HOAN_VI):
        h2 = rng.permutation(hinh)
        null.append(spearman(h2[:-1], h2[1:]))
    return {"thong_ke": chuan_hoa(-q, [-x for x in null]),
            "p": hoan_vi_p(-q, [-x for x in null], "tren"),
            "n": len(hinh), "quan_sat_tho": -q,
            "ghi_chu": f"corr(hieu qua)={q:+.3f} | corr(do doc tho)={q_tho:+.3f}"}


def kd_chan_giua(khoa, df, rng):
    """KD_CHAN_GIUA_DAI_NHAT / "song 3 khong bao gio ngan nhat".

    Lay moi bo BA doan CUNG CHIEU lien tiep (doan 1-3-5 cua mot cau truc). Elliott:
    chan giua khong duoc ngan nhat. Do P(chan giua ngan nhat); null = 1/3.
    Thong ke = 1/3 - P(ngan nhat), duong nghia la UNG HO Elliott.
    """
    d = cac_doan(df, chan_song(df))
    if len(d) < 30:
        return None
    L = d["do_dai"].to_numpy()
    H = d["huong"].to_numpy()
    bo = [(L[i], L[i + 2], L[i + 4]) for i in range(len(L) - 4)
          if H[i] == H[i + 2] == H[i + 4]]
    if len(bo) < 25:
        return None
    b = np.array(bo)
    ngan_nhat_giua = (np.argmin(b, axis=1) == 1).mean()
    dai_nhat_giua = (np.argmax(b, axis=1) == 1).mean()
    tk = 1 / 3 - ngan_nhat_giua
    null = []
    for _ in range(SO_LAN_HOAN_VI):
        bb = rng.permuted(b, axis=1)
        null.append(1 / 3 - (np.argmin(bb, axis=1) == 1).mean())
    return {"thong_ke": chuan_hoa(tk, null), "p": hoan_vi_p(tk, null, "tren"),
            "n": len(bo), "quan_sat_tho": float(tk),
            "ghi_chu": f"P(giua ngan nhat)={ngan_nhat_giua:.3f} "
                       f"P(giua dai nhat)={dai_nhat_giua:.3f}"}


def kd_bat_doi_xung_5_3(khoa, df, rng):
    """KD_BAT_DOI_XUNG_5_3 - chuoi 5 chan khac chuoi 3 chan ve thong ke.

    Nhan qua hoan toan: dem so doan da hoan thanh trong xu the hien tai; tai bar
    XAC NHAN cua doan thu 3 va doan thu 5, do loi suat 10 phien ke tiep (vao lenh
    o open bar sau - quy tac 1 cua du an).
    Thong ke = chenh lech trung binh loi suat sau chan 5 va sau chan 3.
    Null: hoan vi nhan 3/5 giua cac su kien.
    """
    d = cac_doan(df, chan_song(df))
    if len(d) < 30:
        return None
    o = df["open"].to_numpy()
    n = len(df)
    K = 10
    dem, moc = 0, []
    huong_truoc = 0
    for _, r in d.iterrows():
        if r["huong"] != huong_truoc:
            dem = 1
            huong_truoc = r["huong"]
        else:
            dem += 1
        moc.append((int(r["biet_tai"]), dem))
    lay = {3: [], 5: []}
    for bt, dem_i in moc:
        if dem_i in (3, 5) and bt + 1 + K < n:
            lay[dem_i].append(np.log(o[bt + 1 + K] / o[bt + 1]))
    if len(lay[3]) < 15 or len(lay[5]) < 15:
        return None
    a3, a5 = np.array(lay[3]), np.array(lay[5])
    tk = float(a5.mean() - a3.mean())
    gop = np.concatenate([a3, a5])
    n3 = len(a3)
    null = []
    for _ in range(SO_LAN_HOAN_VI):
        g = rng.permutation(gop)
        null.append(g[n3:].mean() - g[:n3].mean())
    return {"thong_ke": chuan_hoa(tk, null), "p": hoan_vi_p(tk, null, "hai"),
            "n": len(gop), "quan_sat_tho": tk,
            "ghi_chu": f"n3={len(a3)} n5={len(a5)} m3={a3.mean():+.4f} m5={a5.mean():+.4f}"}


def kd_don_cum_lenh_dung(khoa, df, rng):
    """KD_DON_CUM_LENH_DUNG - quet thanh khoan (ICT/SMC sweep, Wyckoff spring, stop hunt).

    Su kien: bar pha DINH 20 phien (high > dinh cu) NHUNG dong cua QUAY VE duoi dinh
    -> "quet roi tu choi". Doi chieu voi bar pha DINH VA dong cua TREN dinh (pha that).
    Vao o open bar ke tiep, giu 5 phien. Lam ca hai chieu, dao dau chieu ban.
    Thong ke = loi suat trung binh cua nhom "quet roi tu choi" (theo huong dao chieu).
    Null: chon ngau nhien cung so bar, cung phan bo thang trong nam.
    """
    N, K = 20, 5
    h, l, c, o = (df[x].to_numpy() for x in ("high", "low", "close", "open"))
    n = len(df)
    dinh = pd.Series(h).rolling(N).max().shift(1).to_numpy()
    day = pd.Series(l).rolling(N).min().shift(1).to_numpy()

    quet_tren = np.zeros(n, bool); quet_duoi = np.zeros(n, bool)
    pha_tren = np.zeros(n, bool)
    for i in range(N + 1, n - K - 2):
        if np.isfinite(dinh[i]):
            if h[i] > dinh[i] and c[i] < dinh[i]:
                quet_tren[i] = True
            elif h[i] > dinh[i] and c[i] > dinh[i]:
                pha_tren[i] = True
        if np.isfinite(day[i]) and l[i] < day[i] and c[i] > day[i]:
            quet_duoi[i] = True

    def loi(mask, chieu):
        idx = np.flatnonzero(mask)
        idx = idx[(idx + 1 + K) < n]
        if len(idx) == 0:
            return np.array([])
        return chieu * np.log(o[idx + 1 + K] / o[idx + 1])

    r_quet = np.concatenate([loi(quet_tren, -1), loi(quet_duoi, +1)])
    r_pha = loi(pha_tren, +1)
    if len(r_quet) < 40:
        return None
    tk = float(r_quet.mean())

    # placebo giu PHOI NHIEM: lay ngau nhien cung so bar, cung so lenh mua/ban
    n_tren = int((quet_tren[:n - K - 2]).sum())
    n_duoi = int((quet_duoi[:n - K - 2]).sum())
    hop_le = np.arange(N + 1, n - K - 2)
    null = []
    for _ in range(SO_LAN_HOAN_VI):
        s = rng.choice(hop_le, n_tren + n_duoi, replace=False)
        chieu = np.r_[-np.ones(n_tren), np.ones(n_duoi)]
        null.append(float((chieu * np.log(o[s + 1 + K] / o[s + 1])).mean()))
    return {"thong_ke": chuan_hoa(tk, null), "p": hoan_vi_p(tk, null, "tren"),
            "n": len(r_quet), "quan_sat_tho": tk, "null_tb": float(np.mean(null)),
            "ghi_chu": f"quet {tk*1e4:+.1f}bps | null {np.mean(null)*1e4:+.1f}bps | "
                       f"pha that {(r_pha.mean()*1e4 if len(r_pha) else float('nan')):+.1f}bps"}


def kd_lap_khoang_trong(khoa, df, rng):
    """KD_LAP_KHOANG_TRONG - fair value gap (ICT/SMC) / gap fill.

    FVG tang tai bar t: low[t] > high[t-2] (bar giua bo trong mot vung). Hoi: gia co
    quay lai lap vung do trong K=20 phien nhieu hon NGAU NHIEN khong?

    Doi chung phai KHOP KHOANG CACH - day la cho de tu lua nhat: gia lien tuc quay
    lai moi muc gan no, nen ty le lap 80% nghe to nhung khong noi len gi. Doi chung:
    cung do rong, cung khoang cach, dat o mot bar NGAU NHIEN cua chinh thi truong do.
    Thong ke = ty le lap that - ty le lap doi chung.
    """
    K = 20
    h, l, c = (df[x].to_numpy() for x in ("high", "low", "close"))
    n = len(df)

    # --- VECTOR HOA. Ban dau viet bang vong lap Python: 400 lan x ~3.000 su kien x
    # mot lat numpy = 33 trieu thao tac cho 28 thi truong, chay 15+ phut. Muc tieu la
    # chay duoc tren VPS yeu nen phai viet lai.
    #
    # Meo: "gia co cham muc cach X phan tram trong K phien toi khong" khong can cat
    # lat tung lan. Voi moi bar t, tinh SAN nguong:
    #     d_xuong[t] = 1 - min(low[t+1..t+K]) / close[t]
    #     d_len[t]   = max(high[t+1..t+K]) / close[t] - 1
    # Roi "lap duoc" chi con la mot phep SO SANH: khoang cach >= nguong. Tu 33 trieu
    # lat cat thanh 2 phep rolling + vai phep so sanh mang.
    if n < 3 + K + 2:
        return None
    cua_l = np.lib.stride_tricks.sliding_window_view(l, K)   # (n-K+1, K)
    cua_h = np.lib.stride_tricks.sliding_window_view(h, K)
    min_toi = np.full(n, np.nan)
    max_toi = np.full(n, np.nan)
    hop = np.arange(0, n - K)              # bar t co du K bar phia sau (bat dau t+1)
    min_toi[hop] = cua_l[hop + 1].min(axis=1)
    max_toi[hop] = cua_h[hop + 1].max(axis=1)
    d_xuong = 1 - min_toi / c              # khoang cach toi thieu de cham xuong
    d_len = max_toi / c - 1                # ... de cham len

    t_all = np.arange(2, n - K - 1)
    tang_gia = l[t_all] > h[t_all - 2]                    # khoang trong huong len
    giam_gia = (~tang_gia) & (h[t_all] < l[t_all - 2])
    la_sk = tang_gia | giam_gia
    t_sk = t_all[la_sk]
    if len(t_sk) < 40:
        return None
    canh = np.where(tang_gia[la_sk], h[t_sk - 2], l[t_sk - 2])
    kc = (c[t_sk] - canh) / c[t_sk]        # >0: canh nam duoi; <0: canh nam tren

    def lap_vec(bar, k):
        """Cham duoc muc cach `k` (tuong doi) tinh tu close cua `bar`, trong K phien?

        `d_xuong[bar]` la khoang cach XA NHAT ma gia cham toi trong K phien toi. Muc
        nao GAN hon muc do thi cham duoc => dieu kien la `<=`, khong phai `>=`.
        Viet nham dau nay mot lan roi: ty le lap ra dung phan bu (0,295 thay vi 0,705)
        va van chay tron, van in bang dep - dung loai loi ma toi vua che DeepSeek.
        """
        duoi = k > 0
        nguong = np.where(duoi, d_xuong[bar], d_len[bar])
        return np.abs(k) <= nguong

    that = lap_vec(t_sk, kc).astype(float)
    that = that[np.isfinite(np.where(kc > 0, d_xuong[t_sk], d_len[t_sk]))]
    if len(that) < 40:
        return None

    # Doi chung phai khop CA HAI: khoang cach tuong doi, VA che do bien dong.
    # Khop khoang cach khong thoi la chua du - khoang trong chi sinh ra trong nhung
    # phien bien dong manh, ma phien bien dong manh thi gia quay lai BAT KY muc nao
    # cung de hon. Boc bar ngau nhien bat ke vol se cho "khoang trong co suc hut"
    # trong khi tat ca chi la vol. Day la lan thu BA cung mot bay trong phien nay.
    ap = (atr(df, 14) / df["close"]).to_numpy()
    hop_le = t_all[np.isfinite(ap[t_all]) & np.isfinite(d_xuong[t_all])
                   & np.isfinite(d_len[t_all])]
    if len(hop_le) < 200:
        return None
    vien = np.nanquantile(ap[hop_le], [0.2, 0.4, 0.6, 0.8])
    tang_hl = np.digitize(ap[hop_le], vien)
    tang_sk = np.digitize(ap[t_sk], vien)

    SO_LAN = 400
    mau = np.empty((SO_LAN, len(t_sk)), dtype=np.int64)
    for g in range(5):
        cot = np.flatnonzero(tang_sk == g)
        if len(cot) == 0:
            continue
        kho = hop_le[tang_hl == g]
        if len(kho) == 0:
            kho = hop_le                      # tang rong thi lui ve toan bo
        mau[:, cot] = rng.choice(kho, size=(SO_LAN, len(cot)))
    dc = lap_vec(mau, np.broadcast_to(kc, mau.shape)).mean(axis=1)
    return {"thong_ke": chuan_hoa(that.mean(), dc),
            "p": hoan_vi_p(that.mean(), dc, "tren"), "n": len(that),
            "quan_sat_tho": float(that.mean()), "null_tb": float(dc.mean()),
            "ghi_chu": f"lap that {that.mean():.3f} vs doi chung {dc.mean():.3f}"}


def kd_kl_phan_ky_bien(khoa, df, rng):
    """KD_KL_PHAN_KY_BIEN - Wyckoff / VSA: khoi luong can o bien vung = dao chieu.

    Tai cac bar cham DINH 20 phien, do z-score khoi luong so voi 20 phien truoc.
    Neu khang dinh dung: khoi luong THAP o bien -> dao chieu -> loi suat 5 phien
    ke tiep AM => tuong quan hang (kl_z, loi suat) DUONG.
    Null: hoan vi chuoi loi suat giua cac su kien.
    """
    if (df["volume"] > 0).mean() < 0.80:
        return None
    K = 5
    h, o, v = (df[x].to_numpy() for x in ("high", "open", "volume"))
    n = len(df)
    dinh = pd.Series(h).rolling(20).max().shift(1).to_numpy()
    kl_tb = pd.Series(v).rolling(20).mean().shift(1).to_numpy()
    kl_sd = pd.Series(v).rolling(20).std().shift(1).to_numpy()
    idx = [i for i in range(21, n - K - 2)
           if np.isfinite(dinh[i]) and h[i] >= dinh[i] and np.isfinite(kl_sd[i]) and kl_sd[i] > 0]
    if len(idx) < 40:
        return None
    idx = np.array(idx)
    z = (v[idx] - kl_tb[idx]) / kl_sd[idx]
    r = np.log(o[idx + 1 + K] / o[idx + 1])
    q = spearman(z, r)
    if not np.isfinite(q):
        return None
    null = [spearman(z, rng.permutation(r)) for _ in range(SO_LAN_HOAN_VI)]
    return {"thong_ke": chuan_hoa(q, null), "p": hoan_vi_p(q, null, "tren"),
            "n": len(idx), "quan_sat_tho": q,
            "ghi_chu": f"IC(kl_z, loi suat {K} phien)={q:+.4f}"}


def kd_doi_xung_thoi_gian(khoa, df, rng):
    """KD_DOI_XUNG_THOI_GIAN - Gann / chu ky thoi gian.

    Khoang cach (so bar) giua cac chan lien tiep co cau truc lap lai khong? Neu co
    thi khoang truoc phai DU BAO duoc khoang sau => tuong quan hang lag-1 khac 0.
    Null: hoan vi chuoi khoang cach.
    Day la khang dinh de bi ao giac nhat: mot buoc di ngau nhien cung sinh ra
    "chu ky" khi nhin bang mat.
    """
    ch = chan_song(df)
    if len(ch) < 30:
        return None
    kc = np.diff(ch["vi_tri"].to_numpy()).astype(float)
    kc = kc[kc > 0]
    if len(kc) < 25:
        return None
    lk = np.log(kc)
    q = spearman(lk[:-1], lk[1:])
    if not np.isfinite(q):
        return None
    null = []
    for _ in range(SO_LAN_HOAN_VI):
        k2 = rng.permutation(lk)
        null.append(spearman(k2[:-1], k2[1:]))
    cv = float(np.std(kc) / np.mean(kc))
    return {"thong_ke": chuan_hoa(q, null), "p": hoan_vi_p(q, null, "hai"),
            "n": len(kc), "quan_sat_tho": q,
            "ghi_chu": f"corr lag-1={q:+.3f} he so bien thien={cv:.2f}"}


# --- cong repaint cho chinh bo gan nhan song -------------------------------

def _nhan_zigzag_ve_lai(df_cat):
    """Bo gan nhan kieu ZIGZAG THONG THUONG (cai ma indicator MT5/TradingView dung):
    nhan cua moi bar = huong doan dang chua no, TINH LAI tu dau moi lan co bar moi.
    Day chinh la cai VE LAI."""
    ch = chan_song(df_cat)
    nhan = np.zeros(len(df_cat))
    if len(ch) < 2:
        return nhan
    v = ch["vi_tri"].to_numpy(); lo = ch["loai"].to_numpy()
    for i in range(len(v) - 1):
        nhan[v[i]:v[i + 1]] = -lo[i]
    nhan[v[-1]:] = lo[-1]       # doan dang chay - day la cho no doi lien tuc
    return nhan


def _nhan_zigzag_nhan_qua(df_cat):
    """Cung zigzag do nhung CHI cong bo nhan sau khi chan da duoc XAC NHAN."""
    ch = chan_song(df_cat)
    nhan = np.zeros(len(df_cat))
    if len(ch) < 2:
        return nhan
    v = ch["vi_tri"].to_numpy(); x = ch["xac_nhan"].to_numpy(); lo = ch["loai"].to_numpy()
    for i in range(len(v) - 1):
        if x[i + 1] < len(df_cat):        # chi to mau doan da chot han
            nhan[v[i]:v[i + 1]] = -lo[i]
    return nhan


def kd_cong_repaint(khoa, df, rng):
    """Cong repaint tong quat ap len chinh bo gan nhan song (dung cho MOI phuong
    phap dem song: Elliott, Wyckoff phase, SMC market structure, zigzag...).

    So sanh hai ban: ban thong thuong (ve lai) va ban nhan qua (khong ve lai).
    """
    from brain_khang_dinh import cong_repaint
    d = df.iloc[-900:]
    a = cong_repaint(d, _nhan_zigzag_ve_lai, buoc=5, nguong=0.10)
    b = cong_repaint(d, _nhan_zigzag_nhan_qua, buoc=5, nguong=0.10)
    if "loi" in a or "loi" in b:
        return None
    return {"thong_ke": float(a["ty_le_nhan_doi"]), "p": np.nan,
            "n": int(a["so_bar_kiem"]),
            "ghi_chu": f"zigzag thuong ve lai {a['ty_le_nhan_doi']:.1%} | "
                       f"ban nhan qua {b['ty_le_nhan_doi']:.1%}"}


# ---------------------------------------------------------------------------
# DANG KY CO CHE
# ---------------------------------------------------------------------------

CO_CHE = {
    "elliott_cong_repaint":         (kd_cong_repaint,      "KD_*_dem_song", "tren"),
    "elliott_luan_phien":           (kd_luan_phien,        "KD_LUAN_PHIEN", "tren"),
    "elliott_song3_khong_ngan_nhat": (kd_chan_giua,        "KD_CHAN_GIUA_DAI_NHAT", "tren"),
    "elliott_bat_doi_xung_5_3":     (kd_bat_doi_xung_5_3,  "KD_BAT_DOI_XUNG_5_3", "hai"),
    "smc_don_cum_lenh_dung":        (kd_don_cum_lenh_dung, "KD_DON_CUM_LENH_DUNG", "tren"),
    "smc_lap_khoang_trong":         (kd_lap_khoang_trong,  "KD_LAP_KHOANG_TRONG", "tren"),
    "wyckoff_kl_phan_ky_bien":      (kd_kl_phan_ky_bien,   "KD_KL_PHAN_KY_BIEN", "tren"),
    "gann_doi_xung_thoi_gian":      (kd_doi_xung_thoi_gian, "KD_DOI_XUNG_THOI_GIAN", "hai"),
}

# Co che thi truong VN - da xep hang trong `brain_vong_lap` uu tien 90 nhung
# CHUA CO DU LIEU. Khai bao ro o day de vong lap bao dung ly do, khong bao
# "chua trien khai" chung chung nua.
CO_CHE_CHO_DU_LIEU = {
    "vn_room_ngoai": "can chuoi room ngoai theo ngay (SSI/VNDirect/TCBS) - chua keo",
    "vn_giai_chap_margin": "can du no margin CTCK theo quy + gia co phieu - chua keo",
    "vn_vn30_rebalance": "can lich va danh sach ro VN30 tung ky - chua keo",
    "vn_phien_atc": "can bar phut phien ATC cua HOSE - chua keo",
}


# ---------------------------------------------------------------------------
# API CHO VONG LAP
# ---------------------------------------------------------------------------

def do_ic(muc_tieu, tham_so=None):
    """Diem vao ma `brain_vong_lap.chay_sang()` goi.

    Tra ve dict phang: ic, n, placebo_so_bo, ... (vong lap ghi thang vao SO SANG).
    """
    tham_so = tham_so or {}
    if tham_so.get("tap") != "sang":
        raise ViPhamTapXacNhan("do_ic chi chay tren tap sang")

    if muc_tieu in CO_CHE_CHO_DU_LIEU:
        return {"ic": float("nan"), "n": 0, "placebo_so_bo": float("nan"),
                "trang_thai": "CHO_DU_LIEU", "tom_tat": CO_CHE_CHO_DU_LIEU[muc_tieu]}

    if muc_tieu not in CO_CHE:
        return {}

    kq = chay_co_che(muc_tieu)
    if not kq:
        return {}
    g = kq["gop"]
    return {
        "ic": g.get("trung_vi", float("nan")),
        "n": int(sum(k["n"] for k in kq["theo_thi_truong"])),
        "so_thi_truong": g.get("so_thi_truong", 0),
        "so_duong": g.get("so_duong", 0),
        "placebo_so_bo": 1 - g.get("p_theo_nhom", float("nan")),
        "p_phep_thu_dau": g.get("p_phep_thu_dau", float("nan")),
        "p_theo_nhom": g.get("p_theo_nhom", float("nan")),
        "nhom_duong": f"{g.get('nhom_duong',0)}/{g.get('so_nhom',0)}",
        "stouffer_z": g.get("stouffer_z", float("nan")),
        "khang_dinh": kq["khang_dinh"],
        "tom_tat": kq["tom_tat"],
    }


def chay_co_che(ten, in_ra=False):
    """Chay 1 co che tren toan TAP SANG voi nhieu hat."""
    ham, ma_kd, _phia = CO_CHE[ten]
    chi_kl = ten == "wyckoff_kl_phan_ky_bien"
    return chay_ham(ham, ten, ma_kd, chi_kl=chi_kl, in_ra=in_ra)


def chay_ham(ham, ten, ma_kd="?", chi_kl=False, in_ra=False, so_hat=3):
    """Chay MOT ham do luong bat ky qua dung bo ky luat cua tang kham pha.

    Day la diem noi cho tho ben ngoai (vd DeepSeek qua `ds_tho.py`): ho chi viet
    ham `do(khoa, df, rng) -> dict(thong_ke, p, n)`, con TAP SANG, nhieu hat,
    gop theo nhom tuong quan va cach doc ket qua thi do file nay quyet dinh.
    Nho vay mot tho au cung khong the che ra edge gia - cung lam khong toi.
    """
    thi_truong = nap_tap_sang(chi_co_khoi_luong=chi_kl)
    if not thi_truong:
        return {}

    theo_tt = []
    loi_gap = {}          # thong bao loi -> so thi truong dinh loi do
    for khoa, df in thi_truong.items():
        # nhieu hat: chay lai voi tung hat, lay p XAU NHAT (bao thu)
        gom = []
        for hat in HAT[:2 if ten == "elliott_cong_repaint" else so_hat]:
            rng = np.random.default_rng(hat)
            try:
                r = ham(khoa, df, rng)
                if r is None:
                    loi_gap["ham tra ve None (khong du dieu kien / khong du mau)"] = \
                        loi_gap.get("ham tra ve None (khong du dieu kien / khong du mau)", 0) + 1
            except Exception as e:
                import traceback
                tb = traceback.format_exc().strip().splitlines()
                # giu dong cuoi (loai loi) + dong code gay loi - du de sua, khong dai
                mo_ta = f"{type(e).__name__}: {e}"[:200]
                dong_code = next((d.strip() for d in reversed(tb)
                                  if d.strip().startswith("File") is False
                                  and d.strip() and not d.startswith(mo_ta[:20])), "")
                khoa_loi = f"{mo_ta} | tai: {dong_code[:120]}"
                loi_gap[khoa_loi] = loi_gap.get(khoa_loi, 0) + 1
                r = {"loi": mo_ta}
            if r and "loi" not in r:
                gom.append(r)
        if not gom:
            continue
        r0 = dict(gom[0])
        ps = [g["p"] for g in gom if np.isfinite(g.get("p", np.nan))]
        r0["p"] = float(max(ps)) if ps else float("nan")
        r0["p_min"] = float(min(ps)) if ps else float("nan")
        r0["thi_truong"] = khoa
        theo_tt.append(r0)
        if in_ra:
            print(f"    {khoa:<12} tk={r0['thong_ke']:+.4f} p={r0['p']:.3f} "
                  f"n={r0['n']:<5} {r0.get('ghi_chu','')}")

    if not theo_tt:
        # KHONG duoc nuot loi. Tho o xa (DeepSeek) chi thay dung cai chuoi nay de sua
        # code; tra ve "khong thi truong nao chay duoc" chung chung thi no sua mu, va
        # da that bai 4 vong lien tiep dung vi the.
        xep = sorted(loi_gap.items(), key=lambda x: -x[1])
        tong_luot = len(thi_truong) * min(so_hat, len(HAT))
        return {"loi_mau": "; ".join(f"[{s}/{tong_luot} luot chay] {m}"
                                     for m, s in xep[:3]) or "khong ro nguyen nhan"}
    gop = gop_thi_truong(theo_tt, "thong_ke")
    tom = (f"{gop['so_duong']}/{gop['so_thi_truong']} thi truong cung dau "
           f"({gop['nhom_duong']}/{gop['so_nhom']} NHOM), trung vi {gop['trung_vi']:+.4f}, "
           f"p(dau theo nhom)={gop['p_theo_nhom']:.4f}")
    return {"co_che": ten, "khang_dinh": ma_kd, "theo_thi_truong": theo_tt,
            "gop": gop, "tom_tat": tom}


# ---------------------------------------------------------------------------
# CLI + bao cao (mot file duy nhat, ghi de - quy tac 'bao cao gon mot file')
# ---------------------------------------------------------------------------

def viet_bao_cao(ket_qua):
    md = ["# THE BRAIN - tang kham pha: ket qua TAP SANG", "",
          f"*Chay {datetime.now():%Y-%m-%d %H:%M}. "
          f"Tap sang: {len(TAP_SANG)} thi truong ngoai tap xac nhan.*", "",
          "> **KHONG PHAI EDGE.** Day la tang 1 - khong cong nao, khong ton ngan sach FDR.",
          "> Muon goi la edge thi phai lap ho so, nguoi ky, va chay lai tren TAP XAC NHAN",
          f"> ({', '.join(TAP_XAC_NHAN)}) - cai chua bao gio bi nhin toi luc sang.", "",
          "| co che | khang dinh | trung vi | thi truong cung dau | **NHOM cung dau** | "
          "p (28 dong) | **p (theo nhom)** |",
          "|---|---|---|---|---|---|---|"]
    for k in ket_qua:
        if not k:
            continue
        g = k["gop"]
        md.append(f"| `{k['co_che']}` | {k['khang_dinh']} | {g['trung_vi']:+.4f} | "
                  f"{g['so_duong']}/{g['so_thi_truong']} | **{g['nhom_duong']}/{g['so_nhom']}** | "
                  f"{g['p_phep_thu_dau']:.4f} | **{g['p_theo_nhom']:.4f}** |")
    md += ["",
           "> **Doc cot nao.** 28 thi truong khong phai 28 phep thu doc lap - DAX/CAC/AEX "
           "tuong quan gan 1, sau cap FX deu la ham cua dong do la. Cot `p (28 dong)` vi the "
           "LUON dep hon su that. Con so duoc phep tin la `p (theo nhom)`: gop 28 thi truong "
           "ve 7 nhom tuong quan roi thu dau tren trung vi tung nhom.", "",
           "| nhom | thi truong |", "|---|---|"]
    for nhom, ds in NHOM_TUONG_QUAN.items():
        md.append(f"| {nhom} | {', '.join(ds)} |")
    md.append("")

    for k in ket_qua:
        if not k:
            continue
        tn = k["gop"].get("trung_vi_nhom", {})
        md += [f"## `{k['co_che']}`", "", f"{k['tom_tat']}", "",
               "Trung vi tung nhom: " + " · ".join(f"{a} {b:+.3f}" for a, b in tn.items()), "",
               "| thi truong | thong ke | p (hat xau nhat) | n | ghi chu |", "|---|---|---|---|---|"]
        for r in sorted(k["theo_thi_truong"], key=lambda x: -abs(x["thong_ke"])):
            md.append(f"| {r['thi_truong']} | {r['thong_ke']:+.4f} | {r['p']:.3f} | "
                      f"{r['n']} | {r.get('ghi_chu','')} |")
        md.append("")

    if CO_CHE_CHO_DU_LIEU:
        md += ["## Cho du lieu (khong phai chua trien khai)", "",
               "| co che | thieu gi |", "|---|---|"]
        for a, b in CO_CHE_CHO_DU_LIEU.items():
            md.append(f"| `{a}` | {b} |")
        md.append("")

    RA_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"\n  -> {RA_MD}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--liet-ke", action="store_true")
    ap.add_argument("--chay", default=None)
    ap.add_argument("--tat-ca", action="store_true")
    a = ap.parse_args()

    if a.liet_ke:
        print("CO CHE CHAY DUOC:")
        for t, (_, kd, _) in CO_CHE.items():
            print(f"  {t:<32} -> {kd}")
        print("\nCHO DU LIEU:")
        for t, v in CO_CHE_CHO_DU_LIEU.items():
            print(f"  {t:<32} {v}")
        return

    ds = list(CO_CHE) if a.tat_ca else ([a.chay] if a.chay else [])
    if not ds:
        ap.print_help(); return

    ket = []
    for t in ds:
        print(f"\n=== {t} ===")
        k = chay_co_che(t, in_ra=True)
        if k:
            print(f"  GOP: {k['tom_tat']}")
            ket.append(k)
        else:
            print("  khong du du lieu")
    if len(ket) > 1 or a.tat_ca:
        viet_bao_cao(ket)


if __name__ == "__main__":
    main()
