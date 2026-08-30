# -*- coding: utf-8 -*-
"""metrics.py - Do luong backtest chung: buy&hold, Sharpe/PF/Calmar, chi phi.
Dung chung cho moi co che trong lab/quant/.

Chi phi THUC (tham so hoa, mac dinh la uoc luong thuc te cua san MT5):
  - spread: chi phi tron (round-trip) khi dong/mo lenh, tinh theo "pips".
  - swap: chi phi giu qua dem moi ngay, tinh theo "pips/ngay".
Moi tai san co mot bo tham so chi phi rieng (xem CHI_PHI).
"""
import numpy as np
import pandas as pd

# pips gia tri cho tung loai tai san (1 "pip" = don vi gia tri quy uoc)
#  ^GSPC: 0.1 diem (index) | GC=F: 0.1 USD | EURUSD: 0.0001
_PIP = {"SP500": 0.1, "XAU": 0.1, "EURUSD": 0.0001}

# Uoc luong chi phi thuc te (so voi gia tai san), tren san MT5 loai CFD/futures:
#   spread_roundtrip_pip : do rong spread ca 2 chieu (mo + dong)
#   swap_pip_per_day     : phi giu qua dem (swap) quy doi ra pip/ngay
# Ghi chu: con so nay LA UOC LUONG, tinh trung binh, chua phai gia thuc tu san.
CHI_PHI = {
    "SP500":  dict(pip=_PIP["SP500"], spread_roundtrip_pip=2.0,  swap_pip_per_day=0.5),
    "XAU":    dict(pip=_PIP["XAU"],   spread_roundtrip_pip=3.5,  swap_pip_per_day=1.5),
    "EURUSD": dict(pip=_PIP["EURUSD"],spread_roundtrip_pip=1.2,  swap_pip_per_day=0.4),
    "NDX":    dict(pip=_PIP["SP500"],spread_roundtrip_pip=2.0,  swap_pip_per_day=0.5),
    "GBPUSD": dict(pip=_PIP["EURUSD"],spread_roundtrip_pip=1.5,  swap_pip_per_day=0.5),
}


def chi_phi_frac(loai, gia, swap_ngay=0):
    """Tra ve (spread_frac, swap_frac) theo phan tram gia."""
    cp = CHI_PHI[loai]
    spread_frac = cp["spread_roundtrip_pip"] * cp["pip"] / gia
    swap_frac = cp["swap_pip_per_day"] * cp["pip"] / gia if swap_ngay else 0.0
    return spread_frac, swap_frac


def log_returns(close: pd.Series) -> pd.Series:
    return np.log(close / close.shift(1)).dropna()


def build_equity(close: pd.Series, pos: pd.Series, loai: str,
                 spread_ngat=True, swap_ngay=True) -> pd.Series:
    """Tinh equity curve theo ngay cua mot chien luoc (pos: -1/0/+1).
    - spread: tinh khi co su thay doi vi the (mo hoac dong) + khi dong cuoi ky.
    - swap: tinh moi ngay dang giu lenh.
    Tra ve equity bat dau tai 1.0."""
    idx = close.index
    pos = pos.reindex(idx).fillna(0.0).clip(-1, 1)
    r = close.pct_change().fillna(0.0)
    cp = CHI_PHI[loai]
    pip = cp["pip"]
    spread_frac = cp["spread_roundtrip_pip"] * pip / close
    swap_frac = cp["swap_pip_per_day"] * pip / close

    # lai gop hang ngay tu di chuyen gia
    strat = pos * r
    # phi spread khi doi vi the
    chuyen = pos.diff().abs()
    if spread_ngat:
        strat = strat - chuyen * spread_frac
    # phi swap khi giu lenh
    if swap_ngay:
        strat = strat - pos.abs() * swap_frac
    # dong lenh con lai vao cuoi ky (chi tinh 1 lan spread)
    if spread_ngat:
        strat.iloc[-1] = strat.iloc[-1] - (pos.abs().iloc[-1]) * spread_frac.iloc[-1]
    eq = (1.0 + strat).cumprod()
    return eq


def do_luong(eq: pd.Series, freq=252) -> dict:
    """Cac chi so tu equity curve."""
    eq = eq.dropna()
    if len(eq) < 2:
        return {}
    r = eq.pct_change().dropna()
    nam = len(eq) / freq
    tong = eq.iloc[-1] / eq.iloc[0] - 1.0
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / nam) - 1 if nam > 0 else np.nan
    # Sharpe (annualized, rf=0)
    sd = r.std(ddof=1)
    sharpe = (r.mean() / sd * np.sqrt(freq)) if sd > 0 else np.nan
    # max drawdown
    roll_max = eq.cummax()
    dd = eq / roll_max - 1.0
    max_dd = dd.min()
    calmar = cagr / abs(max_dd) if max_dd < 0 else np.nan
    # profit factor (tren tong lai/lo hang ngay)
    loi = r[r > 0].sum()
    lo = -r[r < 0].sum()
    pf = (loi / lo) if lo > 0 else np.nan
    return {
        "tong_lai_pct": tong * 100,
        "cagr_pct": cagr * 100 if not np.isnan(cagr) else np.nan,
        "sharpe": sharpe,
        "calmar": calmar,
        "max_dd_pct": max_dd * 100,
        "pf": pf,
        "so_ngay": len(eq),
    }


def so_sanh(close: pd.Series, pos: pd.Series, loai: str,
            spread_ngat=True, swap_ngay=True) -> dict:
    """Chay chien luoc vs buy&hold tren cung khoang thoi gian, + khong chi phi."""
    eq_strat = build_equity(close, pos, loai, spread_ngat, swap_ngay)
    eq_bh = build_equity(close, pd.Series(1.0, index=close.index), loai, spread_ngat=False, swap_ngay=False)
    # khong chi phi (de thay chi phi la sat thu)
    eq_no_cost = build_equity(close, pos, loai, spread_ngat=False, swap_ngay=False)
    m_s = do_luong(eq_strat)
    m_bh = do_luong(eq_bh)
    m_nc = do_luong(eq_no_cost)
    return {
        "co_che": m_s,
        "buy_hold": m_bh,
        "khong_chi_phi": m_nc,
    }


def tong_hop(close, pos, loai, ten_co_che, params=None):
    so = so_sanh(close, pos, loai)
    return {
        "ten": ten_co_che,
        "loai_tai_san": loai,
        "params": params or {},
        **so,
    }
