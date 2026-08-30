# -*- coding: utf-8 -*-
"""co_che_A_cung_cau_engulfing.py
Co che A: Cung/cau retest + englobante (engulfing).
- Xac dinh vung cung (pivot high) va vung cau (pivot low) gan nhat,
  chi dung pivot DA DUOC XAC NHAN bang cac nen TRUOC DO (right=3) -> khong
  co lookahead bias.
- Khi gia quay ve (retest) vung cau va co cay nen bullish engulfing -> LONG.
- Khi gia quay ve (retest) vung cung va co cay nen bearish engulfing -> SHORT.
- Giu lenh HOLD nen (mac dinh 5), hoac thoat som khi co tin hieu nguoc.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

THU_MUC = Path(__file__).resolve().parent
sys.path.insert(0, str(THU_MUC))
import du_lieu, metrics
from tin_hieu import pivot, englobante


def tin_hieu(df: pd.DataFrame, hold=5, buffer_atr=0.5, right=3) -> pd.Series:
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    ph, pl = pivot(h, l, left=3, right=right)
    # pivot chi "duoc biet" sau right nen -> dich lui, tranh nhin tuong lai
    ph = pd.Series(ph, index=df.index).shift(right)
    pl = pd.Series(pl, index=df.index).shift(right)

    pos = pd.Series(0.0, index=df.index, dtype=float)
    vung_cau = np.nan
    vung_cung = np.nan
    ngay_mo = 0

    for i in range(right + 1, len(df)):
        # cap nhat vung khi co pivot moi da xac nhan
        if not np.isnan(ph.iloc[i]):
            vung_cung = h.iloc[i]
        if not np.isnan(pl.iloc[i]):
            vung_cau = l.iloc[i]
        # vung het hieu luc khi gia pha qua
        if not np.isnan(vung_cau) and c.iloc[i] < vung_cau - buffer_atr * atr.iloc[i]:
            vung_cau = np.nan
        if not np.isnan(vung_cung) and c.iloc[i] > vung_cung + buffer_atr * atr.iloc[i]:
            vung_cung = np.nan

        if pos.iloc[i-1] != 0:
            so_ngay = i - ngay_mo
            chot = so_ngay >= hold
            if not chot and pos.iloc[i-1] == 1 and not np.isnan(vung_cung) and \
               englobante(o.iloc[i], c.iloc[i], o.iloc[i-1], c.iloc[i-1], loai="bear") and \
               h.iloc[i] >= vung_cung:
                chot = True
            if not chot and pos.iloc[i-1] == -1 and not np.isnan(vung_cau) and \
               englobante(o.iloc[i], c.iloc[i], o.iloc[i-1], c.iloc[i-1], loai="bull") and \
               l.iloc[i] <= vung_cau:
                chot = True
            if chot:
                pos.iloc[i] = 0
                continue

        if pos.iloc[i] == 0 and pos.iloc[i-1] == 0:
            if not np.isnan(vung_cau) and l.iloc[i] <= vung_cau + buffer_atr * atr.iloc[i] and \
               englobante(o.iloc[i], c.iloc[i], o.iloc[i-1], c.iloc[i-1], loai="bull"):
                pos.iloc[i] = 1.0
                ngay_mo = i
                continue
            if not np.isnan(vung_cung) and h.iloc[i] >= vung_cung - buffer_atr * atr.iloc[i] and \
               englobante(o.iloc[i], c.iloc[i], o.iloc[i-1], c.iloc[i-1], loai="bear"):
                pos.iloc[i] = -1.0
                ngay_mo = i
                continue
        if pos.iloc[i] == 0:
            pos.iloc[i] = pos.iloc[i-1]
    return pos


def chay(symbol="^GSPC", hold=5, buffer_atr=0.5, right=3, period="10y"):
    df = du_lieu.nap(symbol, period=period)
    loai = du_lieu.SYMBOLS[symbol][0]
    pos = tin_hieu(df, hold=hold, buffer_atr=buffer_atr, right=right)
    kq = metrics.tong_hop(df["close"], pos, loai, "A_CungCau_Engulfing",
                          params={"hold": hold, "buffer_atr": buffer_atr, "right": right})
    kq["symbol"] = symbol
    kq["so_lenh"] = int((pos.diff().abs() / 2).sum())
    return kq


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="^GSPC")
    ap.add_argument("--hold", type=int, default=5)
    ap.add_argument("--buffer_atr", type=float, default=0.5)
    ap.add_argument("--right", type=int, default=3)
    ap.add_argument("--period", default="10y")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    kq = chay(a.symbol, a.hold, a.buffer_atr, a.right, a.period)
    if a.out:
        Path(a.out).write_text(json.dumps(kq, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(kq, ensure_ascii=False, indent=2, default=str))
