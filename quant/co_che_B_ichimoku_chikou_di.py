# -*- coding: utf-8 -*-
"""co_che_B_ichimoku_chikou_di.py
Co che B: Ichimoku Chikou-Kijun + DI (huong).
- Chikou Span = gia close nhin lai 26 nen truoc (Khong dung du lieu tuong lai).
- Dieu kien LONG: chikou (gia 26 nen truoc) nam tren kijun cua 26 nen truoc
       VA DI+ > DI- (huong duong) hien tai.
- Dieu kien SHORT: doi xung.
- Giu lenh cho den khi tin hieu nguoc (flip), mat ADX, hoac het hold.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

THU_MUC = Path(__file__).resolve().parent
sys.path.insert(0, str(THU_MUC))
import du_lieu, metrics
from tin_hieu import ichimoku, adx_di


def tin_hieu(df, kijun=26, di_n=14, adx_nguong=20.0, hold=10) -> pd.Series:
    cl = df["close"]
    ich = ichimoku(df["high"], df["low"], cl, kijun=kijun)
    d = adx_di(df["high"], df["low"], cl, n=di_n)
    # chikou: gia close nhin lai 26 nen (chi du lieu qua khu)
    chikou = cl.shift(kijun)
    kijun_hist = ich["kijun"].shift(kijun)
    pos = pd.Series(0.0, index=df.index, dtype=float)
    ngay_mo = 0
    for i in range(kijun * 2, len(df)):
        ck = chikou.iloc[i]
        kj = kijun_hist.iloc[i]
        if np.isnan(ck) or np.isnan(kj):
            pos.iloc[i] = pos.iloc[i-1]
            continue
        if pos.iloc[i-1] != 0:
            so_ngay = i - ngay_mo
            flip_long = (ck < kj and d["mdi"].iloc[i] > d["pdi"].iloc[i])
            flip_short = (ck > kj and d["pdi"].iloc[i] > d["mdi"].iloc[i])
            if pos.iloc[i-1] == 1 and (flip_long or so_ngay >= hold):
                pos.iloc[i] = 0
                continue
            if pos.iloc[i-1] == -1 and (flip_short or so_ngay >= hold):
                pos.iloc[i] = 0
                continue
        if pos.iloc[i] == 0 and pos.iloc[i-1] == 0:
            in_trend = (not np.isnan(d["adx"].iloc[i])) and d["adx"].iloc[i] >= adx_nguong
            if ck > kj and d["pdi"].iloc[i] > d["mdi"].iloc[i] and in_trend:
                pos.iloc[i] = 1.0
                ngay_mo = i
                continue
            if ck < kj and d["mdi"].iloc[i] > d["pdi"].iloc[i] and in_trend:
                pos.iloc[i] = -1.0
                ngay_mo = i
                continue
        if pos.iloc[i] == 0:
            pos.iloc[i] = pos.iloc[i-1]
    return pos


def chay(symbol="^GSPC", kijun=26, di_n=14, adx_nguong=20.0, hold=10, period="10y"):
    df = du_lieu.nap(symbol, period=period)
    loai = du_lieu.SYMBOLS[symbol][0]
    pos = tin_hieu(df, kijun=kijun, di_n=di_n, adx_nguong=adx_nguong, hold=hold)
    kq = metrics.tong_hop(df["close"], pos, loai, "B_Ichimoku_Chikou_DI",
                          params={"kijun": kijun, "di_n": di_n, "adx_nguong": adx_nguong, "hold": hold})
    kq["symbol"] = symbol
    kq["so_lenh"] = int((pos.diff().abs() / 2).sum())
    return kq


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="^GSPC")
    ap.add_argument("--kijun", type=int, default=26)
    ap.add_argument("--di_n", type=int, default=14)
    ap.add_argument("--adx_nguong", type=float, default=20.0)
    ap.add_argument("--hold", type=int, default=10)
    ap.add_argument("--period", default="10y")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    kq = chay(a.symbol, a.kijun, a.di_n, a.adx_nguong, a.hold, a.period)
    if a.out:
        Path(a.out).write_text(json.dumps(kq, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(kq, ensure_ascii=False, indent=2, default=str))
