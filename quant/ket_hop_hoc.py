# -*- coding: utf-8 -*-
r"""ket_hop_hoc.py - QUANTLAB: KET HOP CAC SYSTEM (ensemble).
Cac chi bao/system rieng le co the yeu, nhung ket hop co the tot hon.
- Lay vi the (pos) cua tung co che (A/B/C/D) cho 1 tai san.
- Thu cac to hop (cap + bo ba) bang: trung binh vi the + vote da so.
- Cham diem moi to hop qua metrics.tong_hop (du lieu THUC, so buy&hold).
- Chi giu to hop CAI THIEN so voi to hop tot nhat trong cac thanh phan.
Chay:  python ket_hop_hoc.py --symbol EURUSD=X
"""
import sys, json, itertools, argparse
from pathlib import Path
import numpy as np
import pandas as pd

THU_MUC = Path(__file__).resolve().parent
sys.path.insert(0, str(THU_MUC))
import du_lieu, metrics
import co_che_A_cung_cau_engulfing as A
import co_che_B_ichimoku_chikou_di as B
import co_che_C_ema_rsi as C
import co_che_D_premium_choch as D

MECH = {"A": A, "B": B, "C": C, "D": D}

def _pos(mod, df):
    try:
        return mod.tin_hieu(df).reindex(df.index).fillna(0.0)
    except Exception:
        return pd.Series(0.0, index=df.index)

def _ket_hop(ps, cach="avg"):
    """ps: dict ten->pos. Tra pos tong hop."""
    names = list(ps.keys())
    if not names:
        return None
    P = pd.DataFrame({n: ps[n] for n in names})
    if cach == "avg":
        return P.mean(axis=1)
    if cach == "vote":
        return (P.sum(axis=1) / len(names)).apply(lambda x: 1.0 if x > 0.3 else (-1.0 if x < -0.3 else 0.0))
    return P.mean(axis=1)

def chay(symbol="EURUSD=X", toi_da_lenh=28):
    df = du_lieu.nap(symbol, period="10y")
    loai = du_lieu.SYMBOLS[symbol][0]
    ps = {t: _pos(m, df) for t, m in MECH.items()}
    # diem tung cai
    don = {}
    for t, p in ps.items():
        k = metrics.tong_hop(df["close"], p, loai, "don_" + t, params={})
        don[t] = {"edge": round((k["co_che"]["tong_lai_pct"] or 0) - (k["buy_hold"]["tong_lai_pct"] or 0), 2),
                  "pf": round(k["co_che"]["pf"] or 0, 2), "sharpe": round(k["co_che"]["sharpe"] or 0, 2),
                  "lenh": int((p.diff().abs() / 2).sum())}
    # thu to hop
    kq = []
    for r in (2, 3):
        for comb in itertools.combinations(ps.keys(), r):
            for cach in ("avg", "vote"):
                P = _ket_hop({n: ps[n] for n in comb}, cach)
                k = metrics.tong_hop(df["close"], P, loai, "hop", params={})
                kq.append({"to_hop": "+".join(comb), "cach": cach,
                           "edge": round((k["co_che"]["tong_lai_pct"] or 0) - (k["buy_hold"]["tong_lai_pct"] or 0), 2),
                           "lai": round(k["co_che"]["tong_lai_pct"] or 0, 2),
                           "pf": round(k["co_che"]["pf"] or 0, 2), "sharpe": round(k["co_che"]["sharpe"] or 0, 2),
                           "lenh": int((P.diff().abs() / 2).sum())})
    kq = [x for x in kq if x["lenh"] >= 20]
    kq.sort(key=lambda x: -x["sharpe"])
    kq.sort(key=lambda x: -x["edge"])
    r = {"symbol": symbol, "don": don, "to_hop": kq[:10]}
    out = THU_MUC / "ket_hop_hoc.json"
    out.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"=== KET HOP SYSTEM {symbol} ===")
    print("TUNG CAI:", {t: (v['edge'], v['pf'], v['sharpe']) for t, v in don.items()})
    print("TOP TO HOP (edge, pf, sharpe, lenh):")
    for x in kq[:8]:
        print(f"  {x['to_hop']:9} {x['cach']:5} edge={x['edge']:+6.1f}% PF={x['pf']} Sh={x['sharpe']} lenh={x['lenh']}")
    return r

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="EURUSD=X")
    a = ap.parse_args()
    chay(a.symbol)
