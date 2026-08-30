# -*- coding: utf-8 -*-
"""tin_hieu.py - Cac ham chi bao ky thuat dung chung cho cac co che.
Tu viet de tranh phu thuoc package ngoai (chi dung pandas/numpy).
"""
import numpy as np
import pandas as pd


def pivot(high: pd.Series, low: pd.Series, left=3, right=3):
    """Tra ve (pivot_high, pivot_low) - mang float, NaN o vi tri khong phai pivot."""
    n = len(high)
    ph = np.full(n, np.nan)
    pl = np.full(n, np.nan)
    h = high.to_numpy()
    l = low.to_numpy()
    for i in range(left, n - right):
        if h[i] == max(h[i - left:i + right + 1]):
            ph[i] = h[i]
        if l[i] == min(l[i - left:i + right + 1]):
            pl[i] = l[i]
    return ph, pl


def englobante(o, c, prev_o, prev_c, loai="bull"):
    """Cay nen engulf (nuot) - so sanh than nen hien tai va than nen truoc."""
    body = abs(c - o)
    prev_body = abs(prev_c - prev_o)
    if body <= 0 or prev_body <= 0:
        return False
    if loai == "bull":
        return c > o and prev_c < prev_o and c >= prev_o and o <= prev_c
    else:
        return c < o and prev_c > prev_o and o >= prev_c and c <= prev_o


def ema(s, span):
    return s.ewm(span=span, adjust=False).mean()


def rsi(close, n=14):
    delta = close.diff()
    up = delta.clip(lower=0)
    dn = -delta.clip(upper=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    rs = au / ad.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def adx_di(high, low, close, n=14):
    up = high.diff()
    dn = -low.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pd.Series(plus_dm, index=high.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    mdi = 100 * pd.Series(minus_dm, index=high.index).ewm(alpha=1 / n, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    av = dx.ewm(alpha=1 / n, adjust=False).mean()
    return pd.DataFrame({"pdi": pdi, "mdi": mdi, "adx": av})


def ichimoku(high, low, close, tenkan=9, kijun=26, senkou=52):
    df = pd.DataFrame(index=high.index)
    df["tenkan"] = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
    df["kijun"] = (high.rolling(kijun).max() + low.rolling(kijun).min()) / 2
    df["senkou_a"] = (df["tenkan"] + df["kijun"]) / 2
    df["senkou_b"] = (high.rolling(senkou).max() + low.rolling(senkou).min()) / 2
    df["chikou_raw"] = close
    return df
