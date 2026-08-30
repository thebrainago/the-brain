# -*- coding: utf-8 -*-
"""co_che_C_ema_rsi.py
Co che C: EMA pullback + RSI reset.
- Xu huong: EMA(ema_nhanh) > EMA(ema_cham) (bull) / nguoc lai (bear).
- LONG: gia pullback ve EMA nhanh (gia cham EMA nhanh) VA RSI reset (RSI < 50
       roi quay dau len - "reset" sau khi het qua mua).
- SHORT: doi xung.
- Thoat khi gia cat EMA cham (mat xu huong) hoac het hold.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

THU_MUC = Path(__file__).resolve().parent
sys.path.insert(0, str(THU_MUC))
import du_lieu, metrics
from tin_hieu import ema, rsi


def tin_hieu(df, ma_nhanh=20, ma_cham=50, rsi_n=14, rsi_duoi=50.0, band=0.3, hold=10) -> pd.Series:
    cl = df["close"]
    e_nhanh = ema(cl, ma_nhanh)
    e_cham = ema(cl, ma_cham)
    r = rsi(cl, rsi_n)
    pos = pd.Series(0.0, index=df.index)
    ngay_mo = 0
    for i in range(ma_cham, len(df)):
        if pos.iloc[i-1] != 0:
            so_ngay = i - ngay_mo
            # thoat khi mat xu huong hoac het hold
            if pos.iloc[i-1] == 1 and (cl.iloc[i] < e_cham.iloc[i] or so_ngay >= hold):
                pos.iloc[i] = 0
                continue
            if pos.iloc[i-1] == -1 and (cl.iloc[i] > e_cham.iloc[i] or so_ngay >= hold):
                pos.iloc[i] = 0
                continue
        if pos.iloc[i] == 0 and pos.iloc[i-1] == 0:
            pull_nhanh = abs(cl.iloc[i] - e_nhanh.iloc[i]) / e_nhanh.iloc[i] < band
            # LONG: EMA nhanh > EMA cham, pullback ve EMA nhanh, RSI reset (tu < rsi_duoi)
            if e_nhanh.iloc[i] > e_cham.iloc[i] and pull_nhanh and r.iloc[i] < rsi_duoi:
                pos.iloc[i] = 1.0
                ngay_mo = i
                continue
            if e_nhanh.iloc[i] < e_cham.iloc[i] and pull_nhanh and r.iloc[i] > 100 - rsi_duoi:
                pos.iloc[i] = -1.0
                ngay_mo = i
                continue
        if pos.iloc[i] == 0:
            pos.iloc[i] = pos.iloc[i-1]
    return pos


def chay(symbol="^GSPC", ma_nhanh=20, ma_cham=50, rsi_n=14, rsi_duoi=50.0, band=0.3, hold=10, period="10y"):
    df = du_lieu.nap(symbol, period=period)
    loai = du_lieu.SYMBOLS[symbol][0]
    pos = tin_hieu(df, ma_nhanh=ma_nhanh, ma_cham=ma_cham, rsi_n=rsi_n, rsi_duoi=rsi_duoi, band=band, hold=hold)
    kq = metrics.tong_hop(df["close"], pos, loai, "C_EMA_Pullback_RSI",
                          params={"ma_nhanh": ma_nhanh, "ma_cham": ma_cham, "rsi_n": rsi_n,
                                  "rsi_duoi": rsi_duoi, "band": band, "hold": hold})
    kq["symbol"] = symbol
    kq["so_lenh"] = int((pos.diff().abs() / 2).sum())
    return kq


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="^GSPC")
    ap.add_argument("--ma_nhanh", type=int, default=20)
    ap.add_argument("--ma_cham", type=int, default=50)
    ap.add_argument("--rsi_n", type=int, default=14)
    ap.add_argument("--rsi_duoi", type=float, default=50.0)
    ap.add_argument("--band", type=float, default=0.3)
    ap.add_argument("--hold", type=int, default=10)
    ap.add_argument("--period", default="10y")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    kq = chay(a.symbol, a.ma_nhanh, a.ma_cham, a.rsi_n, a.rsi_duoi, a.band, a.hold, a.period)
    if a.out:
        Path(a.out).write_text(json.dumps(kq, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(kq, ensure_ascii=False, indent=2, default=str))
