# -*- coding: utf-8 -*-
"""mau.py - THU VIEN MAU CHIEN LUOC (template + tham so).

THIET_KE muc 13: chien luoc khai bao bang TEMPLATE + THAM SO, khong sinh ma
tuy y. Moi mau tra ve `tin_hieu[i]` = phoi nhiem MONG MUON, tinh tu thong tin
BIET TAI CLOSE cua bar i. Engine tu dich mot bar - mau KHONG duoc tu dich.

Moi mau khai bao:
  ham    : (df, **tham_so) -> np.ndarray dai bang len(df)
  luoi   : danh sach cau hinh tham so de quet
  co_che : MOT CAU mo ta co che kinh te. Bat buoc - man hinh duyet cua nguoi
           doc cau nay chu khong doc danh sach tham so (THIET_KE muc 9).
  ho     : ten ho de tinh FDR chung
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ------------------------------------------------------------- CHI BAO CO BAN
def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    lai = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    lo = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = lai / lo.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def ibs(df: pd.DataFrame) -> pd.Series:
    """Internal Bar Strength: dong cua nam o dau trong bien do bar."""
    rong = (df["high"] - df["low"]).replace(0, np.nan)
    return ((df["close"] - df["low"]) / rong).fillna(0.5)


def _ra(x, n) -> np.ndarray:
    a = np.asarray(x, dtype=float).reshape(-1)
    return np.nan_to_num(a[:n] if len(a) >= n else np.pad(a, (0, n - len(a))), nan=0.0)


# ------------------------------------------------------------------- CAC MAU
def m_ibs_bat_day(df, nguong=0.2, giu=1, **_):
    """V6 cua du an: dong cua o day bien do ngay -> mua, giu N bar."""
    v = (ibs(df) < nguong).astype(float)
    if giu > 1:
        v = v.rolling(giu, min_periods=1).max()
    return _ra(v, len(df))


def m_momentum_ema(df, n=20, **_):
    c = df["close"]
    return _ra(np.sign(c - ema(c, n)), len(df))


def m_sma_cheo(df, nhanh=10, cham=50, **_):
    c = df["close"]
    f, s = sma(c, nhanh), sma(c, cham)
    v = np.where(f > s, 1.0, -1.0)
    v[(f.isna() | s.isna()).to_numpy()] = 0.0
    return _ra(v, len(df))


def m_donchian(df, n=20, **_):
    hh = df["high"].rolling(n).max().shift(1)
    ll = df["low"].rolling(n).min().shift(1)
    c = df["close"]
    v = pd.Series(np.nan, index=df.index)
    v[c > hh] = 1.0
    v[c < ll] = -1.0
    return _ra(v.ffill().fillna(0.0), len(df))


def m_rsi_dao_chieu(df, n=14, vao=30, ra_=55, **_):
    r = rsi(df["close"], n)
    v = pd.Series(np.nan, index=df.index)
    v[r < vao] = 1.0
    v[r > ra_] = 0.0
    return _ra(v.ffill().fillna(0.0), len(df))


def m_bollinger_ve(df, n=20, k=2.0, **_):
    c = df["close"]
    mid, sd = sma(c, n), c.rolling(n).std()
    v = pd.Series(np.nan, index=df.index)
    v[c < mid - k * sd] = 1.0
    v[c > mid + k * sd] = -1.0
    v[(c - mid).abs() < 0.1 * sd] = 0.0
    return _ra(v.ffill().fillna(0.0), len(df))


def m_ichimoku_cheo(df, tenkan=9, kijun=26, chi_mua=False, **_):
    h, l = df["high"], df["low"]
    t = (h.rolling(tenkan).max() + l.rolling(tenkan).min()) / 2
    k = (h.rolling(kijun).max() + l.rolling(kijun).min()) / 2
    v = np.where(t > k, 1.0, 0.0 if chi_mua else -1.0)
    v = pd.Series(v, index=df.index)
    v[(t.isna() | k.isna()).to_numpy()] = 0.0
    return _ra(v, len(df))


def m_cuoi_thang(df, truoc=3, sau=3, **_):
    """Turn-of-month: mua N ngay cuoi thang + N ngay dau thang sau."""
    ngay = pd.Series(df.index.day, index=df.index)
    cuoi_thang = pd.Series(df.index.days_in_month, index=df.index)
    v = ((ngay > cuoi_thang - truoc) | (ngay <= sau)).astype(float)
    return _ra(v, len(df))


class KhungThieuGio(ValueError):
    """Co che theo GIO bi chay tren khung khong co gio (D1, W1)."""


def _phai_co_gio(df, ten: str) -> None:
    """Chan co che theo PHIEN chay tren khung khong co gio.

    Do that 03/09/2026: `m_mua_qua_dem` tren US500CASH.D1 - moi bar deu co
    hour=0 nen `(g >= 20) | (g < 14)` dung VOI MOI BAR, tin hieu thanh hang so
    1,0, tuc MUA-GIU. No vao bang xep hang o hang 2 voi Sharpe 0,840, tren ca
    moc mua-giu that (0,815), mang ten mot co che phien.

    Ba mau phien khac (`gio_trong_ngay`, `moc_phien`, `orb_pha_vo`) tra ve
    toan 0 nen bi bo loc phoi nhiem nhat ra. Chi cai nay lot, va no lot vi no
    thoai hoa ve phia CO PHOI NHIEM chu khong phai ve 0. Im lang theo huong
    "trong nhu ket qua tot" la dang nguy hiem nhat.

    Nem loi thay vi tra 0: mot co che khong AP DUNG DUOC cho khung nay khac
    han mot co che ap dung duoc nhung khong bao gio vao lenh.
    """
    if len(getattr(df.index, "hour", [])) == 0:
        raise KhungThieuGio(f"{ten}: index khong co thuoc tinh gio")
    if len(set(df.index.hour)) <= 1:
        raise KhungThieuGio(
            f"{ten}: co che theo PHIEN nhung khung chi co mot gio duy nhat "
            f"({sorted(set(df.index.hour))}) - can khung noi ngay")


def m_gio_trong_ngay(df, gio_vao=4, so_gio=8, chieu=1, **_):
    """Session: chi giu trong mot cua so gio co dinh moi ngay."""
    _phai_co_gio(df, "gio_trong_ngay")
    g = df.index.hour
    trong = (g >= gio_vao) & (g < gio_vao + so_gio)
    return _ra(np.where(trong, float(chieu), 0.0), len(df))


def m_bien_do_thu_hep(df, n=20, ty_le=0.7, **_):
    """Bien do co lai (squeeze) -> theo huong pha vo."""
    a = atr(df, n)
    tb = a.rolling(n * 3).mean()
    hep = a < tb * ty_le
    huong = np.sign(df["close"] - df["close"].shift(n))
    return _ra(np.where(hep, huong, 0.0), len(df))


# ---------------------------------------------- MAU RUT TU CODE CO SAN TREN MAY
# Sau khi quet toan may 15/08: cac co che duoi day da ton tai duoi dang script
# roi, nhung chua bao gio di qua engine + cong. Dua vao day de chung duoc kiem
# dinh bang cung mot thuoc do, thay vi moi cai tu bao mot con so.

def m_orb_pha_vo(df, phut_mo=30, gio_mo=13, chi_mua=False, **_):
    """ORB - pha vo bien do mo cua. Nguon: CascadeProjects/windsurf-project.

    Lay bien do `phut_mo` phut dau tu gio mo cua, roi theo huong pha vo.
    """
    _phai_co_gio(df, "orb_pha_vo")
    g, p = df.index.hour, df.index.minute
    trong_mo = (g == gio_mo) & (p < phut_mo)
    ngay = pd.Series(df.index.normalize(), index=df.index)
    cao = df["high"].where(trong_mo).groupby(ngay).transform("max").ffill()
    thap = df["low"].where(trong_mo).groupby(ngay).transform("min").ffill()
    sau_mo = (g > gio_mo) | ((g == gio_mo) & (p >= phut_mo))
    c = df["close"]
    v = pd.Series(np.nan, index=df.index)
    v[sau_mo & (c > cao)] = 1.0
    v[sau_mo & (c < thap)] = 0.0 if chi_mua else -1.0
    v[~sau_mo] = 0.0
    return _ra(v.ffill().fillna(0.0), len(df))


def m_ou_quay_ve(df, n=100, z=2.0, **_):
    """Quay ve trung binh kieu Ornstein-Uhlenbeck. Nguon: Desktop/ou.py.

    Vao khi lech qua z do lech chuan khoi trung binh truot, ra khi ve gan 0.
    """
    c = df["close"]
    tb = c.rolling(n).mean()
    sd = c.rolling(n).std()
    zs = (c - tb) / sd.replace(0, np.nan)
    v = pd.Series(np.nan, index=df.index)
    v[zs < -z] = 1.0
    v[zs > z] = -1.0
    v[zs.abs() < 0.3] = 0.0
    return _ra(v.ffill().fillna(0.0), len(df))


def m_mua_qua_dem(df, gio_vao=20, gio_ra=14, **_):
    """Mua qua dem: vao cuoi phien, ra dau phien sau.
    Nguon: Desktop/stress.py (ban goc khong SL, o day chi giu phoi nhiem).

    LUU Y: day chinh la co che bi phi qua dem an nang nhat - dung de kiem
    xem engine co tinh dung phi khong.
    """
    _phai_co_gio(df, "mua_qua_dem")
    g = df.index.hour
    trong = (g >= gio_vao) | (g < gio_ra)
    return _ra(np.where(trong, 1.0, 0.0), len(df))


def _muc_phien_da_xong(df, gio_bd: int, gio_kt: int) -> tuple[pd.Series, pd.Series]:
    """Dinh/day cua phien gan nhat DA KET THUC tai moi bar.

    `groupby(...).transform(max/min)` phat extrema CUOI PHIEN ve ca cac bar truoc
    khi phien ket thuc. Ham nay gan moi phien mot `available_at`, sau do chi cho
    bar o hoac sau moc do nhin thay extrema cua phien.
    """
    if gio_bd == gio_kt:
        raise ValueError("gio_bd va gio_kt phai khac nhau")
    idx = pd.DatetimeIndex(df.index)
    g = idx.hour.to_numpy()
    ngay = pd.Series(idx.normalize(), index=idx)
    if gio_bd < gio_kt:
        trong = (g >= gio_bd) & (g < gio_kt)
        khoa = ngay
        them_ngay = 0
    else:
        trong = (g >= gio_bd) | (g < gio_kt)
        khoa = ngay.copy()
        khoa.iloc[g < gio_kt] = khoa.iloc[g < gio_kt] - pd.Timedelta(days=1)
        them_ngay = 1

    x = pd.DataFrame({"khoa": khoa.to_numpy(), "high": df["high"].to_numpy(),
                      "low": df["low"].to_numpy()}, index=idx)
    muc = x.loc[trong].groupby("khoa", sort=True).agg(cao=("high", "max"),
                                                       thap=("low", "min"))
    if muc.empty:
        rong = pd.Series(np.nan, index=idx)
        return rong, rong.copy()

    san_sang = (pd.DatetimeIndex(muc.index) + pd.Timedelta(days=them_ngay)
                + pd.Timedelta(hours=gio_kt))
    vi_tri = np.searchsorted(san_sang.asi8, idx.asi8, side="right") - 1
    hop_le = vi_tri >= 0
    cao = np.full(len(idx), np.nan, dtype=float)
    thap = np.full(len(idx), np.nan, dtype=float)
    cao[hop_le] = muc["cao"].to_numpy(dtype=float)[vi_tri[hop_le]]
    thap[hop_le] = muc["thap"].to_numpy(dtype=float)[vi_tri[hop_le]]
    return pd.Series(cao, index=idx), pd.Series(thap, index=idx)


def m_moc_phien(df, gio_bd=0, gio_kt=7, chieu=1, **_):
    """Pha vo dinh/day cua mot PHIEN truoc do (Á / London / My).
    Nguon: Desktop/sp500checkerv5.py (magnetic levels) + magnetic_master.py.
    """
    _phai_co_gio(df, "moc_phien")
    g = df.index.hour
    trong_phien = (g >= gio_bd) & (g < gio_kt)
    if gio_bd > gio_kt:
        trong_phien = (g >= gio_bd) | (g < gio_kt)
    cao, thap = _muc_phien_da_xong(df, int(gio_bd), int(gio_kt))
    c = df["close"]
    v = pd.Series(np.nan, index=df.index)
    v[(~trong_phien) & (c > cao)] = float(chieu)
    v[(~trong_phien) & (c < thap)] = -float(chieu)
    return _ra(v.ffill().fillna(0.0), len(df))


def m_lap_gap(df, nguong=0.001, **_):
    """Gap qua dem -> ky vong lap lai gap (fade). Nguon: magnetic/gap fill.

    CAI BAY DA SAP O DAY (15/08): ban dau viet
        dong_truoc = df["close"].groupby(ngay).transform("last").groupby(ngay).shift(1)
    `transform("last")` tra ve dong cua CUOI NGAY HOM NAY roi phat cho MOI bar
    trong ngay do - tuc dung gia tuong lai. `.shift(1)` sau do chi dich mot BAR
    trong ngay, khong phai mot NGAY. Ket qua: EURCAD H1 ra CAGR 115%, Sharpe 10,4.
    Dau hieu nhan ra dung la nguong da hieu chuan cua du an: Sharpe/t cao den
    muc do thi phai gia dinh nhin truoc truoc da.

    Ban dung: gom dong cua theo NGAY roi dich mot NGAY, sau do phat nguoc lai.
    """
    ngay = pd.Series(df.index.normalize(), index=df.index)
    mo_ngay = df["open"].groupby(ngay).transform("first")     # biet ngay dau ngay - hop le
    dong_theo_ngay = df["close"].groupby(ngay).last()          # mot gia tri moi ngay
    dong_ngay_truoc = ngay.map(dong_theo_ngay.shift(1))        # dong cua NGAY HOM TRUOC
    gap = (mo_ngay - dong_ngay_truoc) / dong_ngay_truoc.replace(0, np.nan)
    v = pd.Series(0.0, index=df.index)
    v[gap > nguong] = -1.0      # gap len -> fade xuong
    v[gap < -nguong] = 1.0      # gap xuong -> fade len
    return _ra(v.fillna(0.0), len(df))


# --- ba mau bo sung 30/08/2026 ------------------------------------------
# Do 24/08 tren 52 file .mq5 tai ve tu MQL5 Code Base: 18 chien luoc that,
# trong do **12 khong co template tuong ung** nen khong co duong vao QUANTLAB.
# Ba co che duoi day la thu xuat hien nhieu nhat trong 12 file do.
#
# Ca ba deu chi doc thong tin biet TAI close[i]; engine tu dich mot bar.

def supertrend(df, n=10, he_so=3.0):
    """Duong SuperTrend: dai ATR quanh gia trung binh, CHOT LAI khong lui.

    Phan "khong lui" moi la cai lam nen co che: mot khi dai da siet lai theo
    huong xu huong thi no khong noi ra, nen tin hieu doi chieu chi xay ra khi
    gia that su xuyen qua - khong phai khi bien do tinh co no ra.
    """
    tb = (df["high"] + df["low"]) / 2.0
    a = atr(df, n)
    tren_tho, duoi_tho = tb + he_so * a, tb - he_so * a
    # Vong lap nay BAT BUOC tuan tu (dai bar i phu thuoc dai bar i-1), nhung no
    # khong bat buoc phai cham. Ban cu truy tung phan tu cua MANG NUMPY va goi
    # `np.isnan` tren tung so vo huong - hai thao tac dat nhat co the trong mot
    # vong lap Python. Do tren mot luot QUANTLAB that (01/09): 208 lan goi ngon
    # 23,0 giay thoi gian RIENG = 14% ca luot, chi cho MOT chi bao.
    # Doi sang list Python thuan + `x != x` thay `np.isnan`: ket qua GIONG HET
    # tung phan tu (co kiem), nhanh hon ~6 lan.
    c = df["close"].to_numpy().tolist()
    tt = tren_tho.to_numpy().tolist()
    td = duoi_tho.to_numpy().tolist()
    n_bar = len(df)
    nan = float("nan")
    tren = [nan] * n_bar
    duoi = [nan] * n_bar
    huong = [0.0] * n_bar
    for i in range(1, n_bar):
        ti = tt[i]
        di = td[i]
        if ti != ti or di != di:          # x != x <=> x la NaN
            continue
        pt = tren[i - 1]
        pd_ = duoi[i - 1]
        cp = c[i - 1]
        # Dai tren chi duoc SIET XUONG, tru khi bar truoc da dong tren no.
        tren[i] = min(ti, pt) if (pt == pt and cp <= pt) else ti
        duoi[i] = max(di, pd_) if (pd_ == pd_ and cp >= pd_) else di
        ci = c[i]
        if ci > tren[i]:
            huong[i] = 1.0
        elif ci < duoi[i]:
            huong[i] = -1.0
        else:
            huong[i] = huong[i - 1]
    return pd.Series(huong, index=df.index, dtype="float64")


def stoch(df, n=14, lam_muot=3):
    """%K cua Stochastic: gia dong cua nam o dau bien do N bar."""
    thap = df["low"].rolling(n).min()
    cao = df["high"].rolling(n).max()
    bien = (cao - thap).replace(0.0, np.nan)
    k = 100.0 * (df["close"] - thap) / bien
    return k.rolling(lam_muot).mean()


def m_supertrend(df, n=10, he_so=3.0, chi_mua=False, **_):
    h = supertrend(df, n, he_so)
    v = h.copy()
    if chi_mua:
        v = v.clip(lower=0.0)
    return _ra(v.fillna(0.0), len(df))


def m_stoch_qua_ban(df, n=14, lam_muot=3, vao=20, ra_=60, **_):
    """Stochastic ban qua da -> mua, thoat khi ve giua bien do.

    Khac `rsi_dao_chieu` o cho no do vi tri trong BIEN DO cao-thap chu khong do
    ty le tang/giam - nen no bat duoc trang thai "sat day bien do N bar" ma RSI
    khong thay khi bien do hep.
    """
    k = stoch(df, n, lam_muot)
    v = pd.Series(np.nan, index=df.index)
    v[k < vao] = 1.0
    v[k > ra_] = 0.0
    return _ra(v.ffill().fillna(0.0), len(df))


def m_do_doc_ma(df, n=50, cua_so=10, nguong=0.0, **_):
    """DO DOC cua duong trung binh, khong phai vi tri gia so voi no.

    Khac `momentum_ema`: o day tin hieu la MA dang DI LEN hay DI XUONG, do bang
    thay doi tuong doi qua `cua_so` bar. Gia co the dang duoi MA ma MA van doc
    len - hai trang thai do khac nhau, va cac EA tai ve phan biet chung.
    """
    m = sma(df["close"], n)
    doc = (m - m.shift(cua_so)) / m.shift(cua_so).abs().replace(0.0, np.nan)
    v = pd.Series(0.0, index=df.index)
    v[doc > nguong] = 1.0
    v[doc < -nguong] = -1.0
    return _ra(v.fillna(0.0), len(df))


MAU = {
    "ibs_bat_day": {
        "ham": m_ibs_bat_day, "ho": "quay_ve_trung_binh",
        "co_che": "Dong cua o day bien do ngay phan anh ban thao cuoi phien; "
                  "nguoi mua thanh khoan duoc tra cong o phien ke tiep.",
        "luoi": [{"nguong": 0.15, "giu": 1}, {"nguong": 0.2, "giu": 1},
                 {"nguong": 0.2, "giu": 2}, {"nguong": 0.3, "giu": 1}],
    },
    "momentum_ema": {
        "ham": m_momentum_ema, "ho": "xu_huong",
        "co_che": "Gia tren duong trung binh = dong tien dang vao; xu huong tu nuoi.",
        "luoi": [{"n": 10}, {"n": 20}, {"n": 50}, {"n": 100}],
    },
    "sma_cheo": {
        "ham": m_sma_cheo, "ho": "xu_huong",
        "co_che": "Hai duong trung binh cat nhau danh dau doi che do xu huong.",
        "luoi": [{"nhanh": 5, "cham": 20}, {"nhanh": 10, "cham": 50},
                 {"nhanh": 20, "cham": 100}],
    },
    "donchian": {
        "ham": m_donchian, "ho": "pha_vo",
        "co_che": "Pha dinh/day N bar = xuat hien nguoi mua/ban co thong tin moi.",
        "luoi": [{"n": 10}, {"n": 20}, {"n": 55}],
    },
    "rsi_dao_chieu": {
        "ham": m_rsi_dao_chieu, "ho": "quay_ve_trung_binh",
        "co_che": "Ban qua da ngan han -> ap luc ban can kiet.",
        "luoi": [{"n": 7, "vao": 30, "ra_": 55}, {"n": 14, "vao": 30, "ra_": 55},
                 {"n": 14, "vao": 25, "ra_": 60}],
    },
    "bollinger_ve": {
        "ham": m_bollinger_ve, "ho": "quay_ve_trung_binh",
        "co_che": "Gia lech xa trung binh theo do lech chuan -> keo ve.",
        "luoi": [{"n": 20, "k": 2.0}, {"n": 20, "k": 2.5}, {"n": 50, "k": 2.0}],
    },
    "ichimoku_cheo": {
        "ham": m_ichimoku_cheo, "ho": "xu_huong",
        "co_che": "Tenkan cat Kijun = trung diem ngan han vuot trung diem trung han.",
        "luoi": [{"tenkan": 9, "kijun": 26}, {"tenkan": 9, "kijun": 26, "chi_mua": True},
                 {"tenkan": 20, "kijun": 60}],
    },
    "cuoi_thang": {
        "ham": m_cuoi_thang, "ho": "lich",
        "co_che": "Dong tien luong huu/quy chi so do vao quanh moc cuoi thang.",
        "luoi": [{"truoc": 2, "sau": 2}, {"truoc": 3, "sau": 3}, {"truoc": 1, "sau": 4}],
    },
    "gio_trong_ngay": {
        "ham": m_gio_trong_ngay, "ho": "phien",
        "co_che": "Thanh khoan va do bien dong tap trung theo phien dia ly.",
        "luoi": [{"gio_vao": 4, "so_gio": 8}, {"gio_vao": 8, "so_gio": 8},
                 {"gio_vao": 13, "so_gio": 6}],
    },
    "bien_do_thu_hep": {
        "ham": m_bien_do_thu_hep, "ho": "pha_vo",
        "co_che": "Bien do co lai bao truoc mot cu gian bien do; di theo huong gian.",
        "luoi": [{"n": 20, "ty_le": 0.7}, {"n": 20, "ty_le": 0.5}, {"n": 50, "ty_le": 0.7}],
    },
    "supertrend": {
        "ham": m_supertrend, "ho": "xu_huong",
        "nguon": "12/18 chien luoc .mq5 tai ve (quet 24/08) chua co template",
        "co_che": "Dai ATR chi siet theo huong xu huong, khong noi ra - nen doi "
                  "chieu chi xay ra khi gia THAT SU xuyen qua, khong phai khi "
                  "bien do tinh co gian.",
        "luoi": [{"n": 10, "he_so": 3.0}, {"n": 10, "he_so": 2.0},
                 {"n": 20, "he_so": 3.0}, {"n": 10, "he_so": 3.0, "chi_mua": True}],
    },
    "stoch_qua_ban": {
        "ham": m_stoch_qua_ban, "ho": "quay_ve_trung_binh",
        "nguon": "12/18 chien luoc .mq5 tai ve (quet 24/08) chua co template",
        "co_che": "Dong cua sat DAY BIEN DO N bar = ap luc ban da vet het lenh "
                  "cho; nguoi mua tiep theo duoc gia tot hon gia tri.",
        "luoi": [{"n": 14, "vao": 20, "ra_": 60}, {"n": 14, "vao": 10, "ra_": 50},
                 {"n": 5, "vao": 20, "ra_": 80}],
    },
    "do_doc_ma": {
        "ham": m_do_doc_ma, "ho": "xu_huong",
        "nguon": "12/18 chien luoc .mq5 tai ve (quet 24/08) chua co template",
        "co_che": "HUONG DI cua trung binh, khong phai vi tri gia so voi no: "
                  "gia co the nam duoi MA ma MA van doc len, va do la hai trang "
                  "thai khac nhau.",
        "luoi": [{"n": 50, "cua_so": 10}, {"n": 20, "cua_so": 5},
                 {"n": 100, "cua_so": 20}, {"n": 50, "cua_so": 10, "nguong": 0.002}],
    },
    # --- rut tu code da co san tren may (quet 15/08) ---
    "orb_pha_vo": {
        "ham": m_orb_pha_vo, "ho": "pha_vo",
        "nguon": "CascadeProjects/windsurf-project/src/orb_strategy.py",
        "co_che": "Bien do 15-60 phut dau phien chua phan lon lenh cho qua dem; "
                  "pha ra khoi bien do do danh dau ben nao thang.",
        "luoi": [{"phut_mo": 15, "gio_mo": 13}, {"phut_mo": 30, "gio_mo": 13},
                 {"phut_mo": 60, "gio_mo": 13}, {"phut_mo": 30, "gio_mo": 13, "chi_mua": True}],
    },
    "ou_quay_ve": {
        "ham": m_ou_quay_ve, "ho": "quay_ve_trung_binh",
        "nguon": "Desktop/ou.py",
        "co_che": "Gia dao quanh mot muc can bang; lech qua nhieu do lech chuan thi "
                  "luc keo ve manh hon luc day di.",
        "luoi": [{"n": 100, "z": 2.0}, {"n": 200, "z": 2.0}, {"n": 50, "z": 2.5}],
    },
    "mua_qua_dem": {
        "ham": m_mua_qua_dem, "ho": "phien",
        "nguon": "Desktop/stress.py",
        "co_che": "Phan bu rui ro cua co phieu doi ve dem chu khong ve phien; "
                  "giu qua dem an phan drift, doi lai tra phi qua dem.",
        "luoi": [{"gio_vao": 20, "gio_ra": 14}, {"gio_vao": 21, "gio_ra": 13}],
    },
    "moc_phien": {
        "ham": m_moc_phien, "ho": "pha_vo",
        "nguon": "Desktop/sp500checkerv5.py + magnetic_master.py",
        "co_che": "Dinh/day cua phien truoc la noi dat lenh cho, nen gia bi hut ve "
                  "roi pha qua thi chay tiep.",
        "luoi": [{"gio_bd": 0, "gio_kt": 7}, {"gio_bd": 7, "gio_kt": 13},
                 {"gio_bd": 0, "gio_kt": 7, "chieu": -1}],
    },
    "lap_gap": {
        "ham": m_lap_gap, "ho": "quay_ve_trung_binh",
        "nguon": "magnetic (GapFill)",
        "co_che": "Gap mo cua thuong duoc lap lai trong ngay vi thanh khoan quay lai.",
        "luoi": [{"nguong": 0.001}, {"nguong": 0.003}, {"nguong": 0.005}],
    },
}


def sinh(ten: str, df: pd.DataFrame, tham_so: dict) -> np.ndarray:
    if ten not in MAU:
        raise KeyError(f"khong co mau '{ten}'. Co: {', '.join(MAU)}")
    return MAU[ten]["ham"](df, **tham_so)


def tat_ca_to_hop() -> list[tuple[str, dict]]:
    return [(ten, ts) for ten, m in MAU.items() for ts in m["luoi"]]


if __name__ == "__main__":
    print(f"{len(MAU)} mau, {len(tat_ca_to_hop())} to hop tham so\n")
    for ten, m in MAU.items():
        print(f"  {ten:<18} ho={m['ho']:<20} {len(m['luoi'])} cau hinh")
        print(f"      co che: {m['co_che']}")
