# -*- coding: utf-8 -*-
"""co_che_D_premium_choch.py
Co che D: Premium/Discount + CHoCH (Change of Character).
- Pham vi: range gia (high/low) trong cua so nhin lai (lookback).
- PREMIUM = gia tren trung diem range; DISCOUNT = gia duoi trung diem.
- LONG: gia o vung DISCOUNT VA co CHoCH bull (pha len pivot high da xac nhan).
- SHORT: doi xung.
- Thoat khi het hold.
Chi dung du lieu qua khu (pivot shift right, rolling nhin lui).
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

THU_MUC = Path(__file__).resolve().parent
sys.path.insert(0, str(THU_MUC))
import du_lieu, metrics
from tin_hieu import pivot


def tin_hieu(df, lookback=20, hold=10, buffer=0.0, right=3) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    hi = h.rolling(lookback).max()
    lo_l = l.rolling(lookback).min()
    mid = (hi + lo_l) / 2
    ph, pl = pivot(h, l, left=3, right=right)
    ph = pd.Series(ph, index=df.index).shift(right)
    pl = pd.Series(pl, index=df.index).shift(right)

    pos = pd.Series(0.0, index=df.index, dtype=float)
    ngay_mo = 0
    for i in range(lookback + right, len(df)):
        if pos.iloc[i-1] != 0:
            if i - ngay_mo >= hold:
                pos.iloc[i] = 0
                continue
        if pos.iloc[i] == 0 and pos.iloc[i-1] == 0:
            cac_ph = ph.iloc[i-lookback+1:i+1].dropna()
            cac_pl = pl.iloc[i-lookback+1:i+1].dropna()
            co_choch_bull = len(cac_ph) > 0 and c.iloc[i] > cac_ph.max()
            co_choch_bear = len(cac_pl) > 0 and c.iloc[i] < cac_pl.min()
            if c.iloc[i] < mid.iloc[i] - buffer and co_choch_bull:
                pos.iloc[i] = 1.0
                ngay_mo = i
                continue
            if c.iloc[i] > mid.iloc[i] + buffer and co_choch_bear:
                pos.iloc[i] = -1.0
                ngay_mo = i
                continue
        if pos.iloc[i] == 0:
            pos.iloc[i] = pos.iloc[i-1]
    return pos


def chay(symbol="^GSPC", lookback=20, hold=10, buffer=0.0, right=3, period="10y"):
    df = du_lieu.nap(symbol, period=period)
    loai = du_lieu.SYMBOLS[symbol][0]
    pos = tin_hieu(df, lookback=lookback, hold=hold, buffer=buffer, right=right)
    kq = metrics.tong_hop(df["close"], pos, loai, "D_PremiumDiscount_CHoCH",
                          params={"lookback": lookback, "hold": hold, "buffer": buffer, "right": right})
    kq["symbol"] = symbol
    kq["so_lenh"] = int((pos.diff().abs() / 2).sum())
    return kq


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="^GSPC")
    ap.add_argument("--lookback", type=int, default=20)
    ap.add_argument("--hold", type=int, default=10)
    ap.add_argument("--buffer", type=float, default=0.0)
    ap.add_argument("--right", type=int, default=3)
    ap.add_argument("--period", default="10y")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    kq = chay(a.symbol, a.lookback, a.hold, a.buffer, a.right, a.period)
    if a.out:
        Path(a.out).write_text(json.dumps(kq, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(kq, ensure_ascii=False, indent=2, default=str))
