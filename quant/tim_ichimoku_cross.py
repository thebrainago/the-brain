# -*- coding: utf-8 -*-
"""tim_ichimoku_cross.py - Gia thuyet cua nguoi dung:
"2 duong Ichimoku cat nhau (Tenkan x Kijun) -> vao lenh ngay lap tuc.
Xem khung/hold nao phan ung tot nhat."

O day lan quet nhanh tren khung D1 (3 tai san), quet cac gia tri:
  - do dai hold (so nen giu lenh): 1,2,3,5,8,13,21
  - doi khi dung theo muc tieu gia (TP tinh theo ATR): 0.5,1.0,1.5,2.0,3.0
Luc nao co du lieu MT5 tick moi test duoc khung intraday (phut/gio) + do
tre cua "cat nhau" (close sau nen xac nhan). File nay = sang loc Python cap 1.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

THU_MUC = Path(__file__).resolve().parent
sys.path.insert(0, str(THU_MUC))
import du_lieu, metrics
from tin_hieu import ichimoku

SYMBOLS = ["^GSPC", "GC=F", "EURUSD=X"]


def atr(high, low, close, n=14):
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def tin_hieu_cross(df, cauchat="tenkan_kijun", hold=5, tp_atr=0.0, atr_n=14):
    """Tra ve Series pos (-1/0/+1) theo Ichimoku cross.
    cauchat='tenkan_kijun': Tenkan x Kijun (golden/death cross).
    Giu lenh toi da 'hold' nen, hoac dung som hon khi cham TP (tp_atr * ATR) neu tp_atr>0.
    Vao lenh o gia close sau nen xac nhan."
    """
    cl = df["close"]
    hi = df["high"]; lo = df["low"]
    ich = ichimoku(hi, lo, cl, tenkan=9, kijun=26, senkou=52)
    a = ich["tenkan"]; b = ich["kijun"]
    at = atr(hi, lo, cl, atr_n)
    pos = pd.Series(0.0, index=df.index, dtype=float)
    ngay_mo = -1; gia_mo = np.nan
    for i in range(1, len(df)):
        prev = pos.iloc[i-1]
        cur = 0.0
        if not (np.isnan(a.iloc[i]) or np.isnan(b.iloc[i]) or np.isnan(a.iloc[i-1]) or np.isnan(b.iloc[i-1])):
            la = a.iloc[i-1] - b.iloc[i-1]
            na = a.iloc[i] - b.iloc[i]
            if prev == 0:
                # vao lenh khi co cat duong (doi dau)
                if na > 0 > la:  # golden cross -> LONG
                    cur = 1.0; ngay_mo = i; gia_mo = cl.iloc[i]
                elif na < 0 < la:  # death cross -> SHORT
                    cur = -1.0; ngay_mo = i; gia_mo = cl.iloc[i]
                else:
                    cur = 0.0
            else:
                # dang giu lenh: dong neu cat nguoc, het hold, hoac cham TP
                flip = (prev == 1 and na < 0) or (prev == -1 and na > 0)
                so_ngay = i - ngay_mo
                cham_tp = False
                if tp_atr > 0 and not np.isnan(at.iloc[i]) and not np.isnan(gia_mo):
                    if prev == 1 and cl.iloc[i] >= gia_mo + tp_atr * at.iloc[ngay_mo]:
                        cham_tp = True
                    if prev == -1 and cl.iloc[i] <= gia_mo - tp_atr * at.iloc[ngay_mo]:
                        cham_tp = True
                if flip or so_ngay >= hold or cham_tp:
                    cur = 0.0
                else:
                    cur = prev
        else:
            cur = prev
        pos.iloc[i] = cur
    return pos


def chay(symbol, hold, tp_atr, period="10y"):
    df = du_lieu.nap(symbol, period=period)
    loai = du_lieu.SYMBOLS[symbol][0]
    pos = tin_hieu_cross(df, hold=hold, tp_atr=tp_atr)
    kq = metrics.tong_hop(df["close"], pos, loai, "Ichimoku_TenkanKijun_cross",
                          params={"hold": hold, "tp_atr": tp_atr})
    kq["symbol"] = symbol
    kq["so_lenh"] = int((pos.diff().abs() / 2).sum())
    return kq


def main(out="ket_qua_ichimoku_cross.json"):
    holds = [1, 2, 3, 5, 8, 13, 21]
    tps = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
    ket_qua = []
    for sym in SYMBOLS:
        # 1) quet hold (khong TP) - cau hoi "giu bao lau"
        for h in holds:
            r = chay(sym, h, 0.0)
            r["che_do"] = "hold"
            ket_qua.append(r)
        # 2) quet TP (hold -> 999, chi thoat theo muc tieu)
        for tp in tps[1:]:
            r = chay(sym, 999, tp)
            r["che_do"] = "tp"
            ket_qua.append(r)
    bang = []
    for k in ket_qua:
        c = k["co_che"]; bh = k["buy_hold"]
        bang.append({
            "symbol": k["symbol"], "che_do": k["che_do"],
            "hold": k["params"]["hold"], "tp_atr": k["params"]["tp_atr"],
            "so_lenh": k["so_lenh"],
            "lai_pct": c["tong_lai_pct"], "lai_bh_pct": bh["tong_lai_pct"],
            "sharpe": c["sharpe"], "pf": c["pf"], "max_dd_pct": c["max_dd_pct"],
            "calmar": c["calmar"],
        })
    bang.sort(key=lambda x: (x["lai_pct"] - x["lai_bh_pct"]), reverse=True)
    (THU_MUC / out).write_text(json.dumps(bang, ensure_ascii=False, indent=2), encoding="utf-8")
    top = bang[:8]
    print("TOP 8 (lai - buy&hold):")
    for b in top:
        print(f"  {b['symbol']:<9} {b['che_do']:<5} hold={b['hold']:<3} tp={b['tp_atr']:<4} "
              f"lenh={b['so_lenh']:<4} lai={b['lai_pct']:>7.1f}% BH={b['lai_bh_pct']:>7.1f}% "
              f"Sh={b['sharpe'] if b['sharpe'] is not None else 0:>5.2f} PF={b['pf'] if b['pf'] is not None else 0:>4.2f}")
    print("DA GHI ->", THU_MUC / out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="")
    ap.add_argument("--out", default="ket_qua_ichimoku_cross.json")
    a = ap.parse_args()
    if a.symbol:
        r = chay(a.symbol, 5, 0.0)
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    else:
        main(a.out)
