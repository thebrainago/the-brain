# -*- coding: utf-8 -*-
r"""auto_kham_pha.py v2 - QUANTLAB TU MAY MO, EP XUNG 16 NHAN.
Moi to hop (mechanism x params x symbol) la 1 cong viec DOC LAP -> chay song song
bang ProcessPoolExecutor(16). Bo sung them mechanism + tai san. Chamdiem = so cong
overlap: chay 120 to hop tren 16 nhan.
Chay:  python quant/auto_kham_pha.py [--n-worker 16]
"""
import sys, json, time, argparse, os
from pathlib import Path
import numpy as np
import pandas as pd

THU_MUC = Path(__file__).resolve().parent
sys.path.insert(0, str(THU_MUC))
import du_lieu
import metrics
import tin_hieu
import kiem_dinh

SYMBOLS = ["^GSPC", "GC=F", "EURUSD=X", "^NDX", "GBPUSD=X"]


def _sma(s, n):
    return s.rolling(n).mean()

def _momentum(df, n=20, **_):
    s = df["close"]; e = tin_hieu.ema(s, n)
    return pd.Series(np.sign(s - e), index=df.index).fillna(0.0)

def _momentum_band(df, n=20, rong=0.05, **_):
    s = df["close"]; e = tin_hieu.ema(s, n)
    d = (s - e) / e
    pos = pd.Series(0.0, index=df.index)
    pos[d > rong] = 1.0; pos[d < -rong] = -1.0
    return pos.replace(0.0, np.nan).ffill().fillna(0.0)

def _sma_cross(df, fast=10, slow=50, **_):
    s = df["close"]; f, sl = _sma(s, fast), _sma(s, slow)
    pos = pd.Series(np.where(f > sl, 1.0, -1.0), index=df.index)
    pos[f.isna() | sl.isna()] = 0.0
    return pos

def _rsi_revert(df, n=14, nhap=30, thoat=55, **_):
    s = df["close"]; r = tin_hieu.rsi(s, n)
    pos = pd.Series(0.0, index=df.index)
    pos[r < nhap] = 1.0; pos[r > thoat] = 0.0
    pos[pos.shift(1) == 1.0] = pos.shift(1)
    return pos.fillna(0.0)

def _bollinger_revert(df, n=20, k=2.0, **_):
    s = df["close"]; mid = _sma(s, n); sd = s.rolling(n).std()
    up, lo = mid + k * sd, mid - k * sd
    pos = pd.Series(0.0, index=df.index)
    pos[s < lo] = 1.0; pos[s > up] = -1.0
    pos[s > mid] = 0.0
    return pos.replace(0.0, np.nan).ffill().fillna(0.0)

def _donchian(df, n=20, **_):
    h, l, c = df["high"], df["low"], df["close"]
    hh, ll = h.rolling(n).max().shift(1), l.rolling(n).min().shift(1)
    pos = pd.Series(0.0, index=df.index)
    pos[c > hh] = 1.0; pos[c < ll] = -1.0
    return pos.replace(0.0, np.nan).ffill().fillna(0.0)

def _rsi_momentum(df, n=14, nhap=55, **_):
    s = df["close"]; r = tin_hieu.rsi(s, n)
    pos = pd.Series(0.0, index=df.index)
    pos[r > nhap] = 1.0; pos[r < 100 - nhap] = -1.0
    return pos.replace(0.0, np.nan).ffill().fillna(0.0)

MECH = {
    "momentum":   (_momentum,   [{"n": 10}, {"n": 20}, {"n": 50}]),
    "momentum_band": (_momentum_band, [{"n": 20, "rong": 0.03}, {"n": 20, "rong": 0.05}, {"n": 50, "rong": 0.05}]),
    "sma_cross":  (_sma_cross,  [{"fast": 5, "slow": 20}, {"fast": 10, "slow": 50}, {"fast": 20, "slow": 100}]),
    "rsi_revert": (_rsi_revert, [{"n": 7, "nhap": 30, "thoat": 55}, {"n": 14, "nhap": 30, "thoat": 55}, {"n": 14, "nhap": 25, "thoat": 60}]),
    "bollinger":  (_bollinger_revert, [{"n": 20, "k": 2.0}, {"n": 20, "k": 2.5}, {"n": 50, "k": 2.0}]),
    "donchian":   (_donchian,   [{"n": 10}, {"n": 20}, {"n": 55}]),
    "rsi_momentum": (_rsi_momentum, [{"n": 7, "nhap": 55}, {"n": 14, "nhap": 55}, {"n": 14, "nhap": 60}]),
}


def _mot(sym, ten, params):
    df = du_lieu.nap(sym, period="10y")
    loai = du_lieu.SYMBOLS[sym][0]
    fn = MECH[ten][0]
    pos = fn(df, **params).shift(1).fillna(0.0)   # chong lookahead
    so_lenh = int((pos.diff().abs() / 2).sum())
    v = kiem_dinh.sang_loc(df["close"], pos, loai, so_lenh, n_perm=99)
    v.update({"ten": ten, "params": params, "symbol": sym, "loai": loai})
    return v


def chay(symbols=None, n_worker=None, out="ket_qua_auto.json"):
    if n_worker is None:
        # tu thich nghi theo may: (so luong logic CPU) - 1 de cho 1 nhan ranh
        n_worker = max(1, (os.cpu_count() or 2) - 1)
    symbols = symbols or SYMBOLS
    # PRE-CACHE tuần tự truoc khi bam song song (tranh race khi nhieu worker download)
    for s in symbols:
        du_lieu.nap(s, period="10y")
    combos = [(s, t, p) for s in symbols for t, (fn, grids) in MECH.items() for p in grids]
    t0 = time.time()
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=n_worker) as ex:
        futs = [ex.submit(_mot, *c) for c in combos]
        results = [f.result() for f in futs]
    thoigian = time.time() - t0
    kq = {"chay_luc": time.strftime("%Y-%m-%d %H:%M:%S"), "n_worker": n_worker,
          "thoigian_giay": round(thoigian, 2), "to_hop": len(results),
          "dat": [r for r in results if r["dat"]], "da_quet": results}
    kq["dat"].sort(key=lambda r: -r["edge"])
    (THU_MUC / out).write_text(json.dumps(kq, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"=== AUTO KHAM PHA EP XUNG: {len(results)} to hop tren {n_worker} nhan trong {thoigian:.1f}s, DAT={len(kq['dat'])} ===")
    for r in kq["dat"][:15]:
        print(f"  edge={r['edge']:+.1f}% {r['ten']} {r['params']} {r['symbol']} lai={r['lai']}% BH={r['buy_hold']}% "
              f"PF={r['pf']} Sh={r['sharpe']} p={r['placebo_p']} era={r['era_edges']} lenh={r['so_lenh']}")
    return kq


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-worker", type=int, default=None)
    a = ap.parse_args()
    chay(n_worker=a.n_worker)
