# -*- coding: utf-8 -*-
"""ichimoku_cross.py - QUANTLAB: Ichimoku cross tren du lieu M1 local (khong can mang).
Resample len H1/H4/D1, vao lenh khi close cat Kijun (+filter Tenkan>Kijun),
hold N bar, tu kiem dinh bang placebo (shuffle) -> p-value.
Theo vi du trong for ds.txt.
"""
import json, random, sys, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(r"C:\Users\SV STORE\Downloads\Research SP500")
DATA = ROOT / "data"
LAB  = ROOT / "lab"
PY3  = sys.version_info >= (3,)

def load_m1(cap):
    p = DATA / f"{cap}_M1_mq.parquet"
    df = pd.read_parquet(p)
    df = df[["time","open","high","low","close","tick_volume","spread"]].copy()
    return df

def resample(df, khung):
    rule = {"D1": "1D", "H4": "4h", "H1": "1h"}.get(khung, khung if khung.endswith(("h", "D", "min", "T")) else khung)
    d = df.set_index("time").resample(rule)
    o = d["open"].first(); h = d["high"].max(); lo = d["low"].min()
    c = d["close"].last(); v = d["tick_volume"].sum(); sp = d["spread"].mean()
    out = pd.DataFrame({"open": o, "high": h, "low": lo, "close": c,
                        "vol": v, "spread": sp}).dropna()
    return out

def ichi(o, h, l, c, tk=9, kj=26, sb=52):
    def rmx(s, n): return s.rolling(n).max()
    def rmn(s, n): return s.rolling(n).min()
    tenkan = (rmx(h, tk) + rmn(l, tk)) / 2
    kijun  = (rmx(h, kj) + rmn(l, kj)) / 2
    return tenkan, kijun

def sim(o, h, l, c, tenkan, kijun, hold, spread_pts):
    n = len(c); sig = (c > kijun) & (tenkan > kijun)
    enter = sig & (~sig.shift(1, fill_value=False))
    idx = np.where(enter.values)[0]
    idx = [i for i in idx if i + hold < n]
    if not idx:
        return {"trades": 0, "points": 0.0, "win": 0, "pval": None}
    pnl = []
    for i in idx:
        pnl.append(float(c.iloc[i + hold] - c.iloc[i]) * (10**5) - 2 * float(spread_pts))
    p = np.array(pnl)
    return {"trades": len(p), "points": float(p.sum()),
            "win": float((p > 0).mean() * 100)}

def placebo(o, h, l, c, tenkan, kijun, hold, spread_pts, M=100, seed=1):
    n = len(c); sig = (c > kijun) & (tenkan > kijun)
    enter = sig & (~sig.shift(1, fill_value=False))
    idx = np.array([i for i in np.where(enter.values)[0] if i + hold < n], dtype=int)
    if len(idx) == 0: return None
    real = float(c.iloc[idx + hold].to_numpy().sum() - c.iloc[idx].to_numpy().sum()) * (10**5)
    real -= 2 * float(spread_pts) * len(idx)
    rng = random.Random(seed); k = len(idx)
    c_arr = c.to_numpy()
    hits = 0
    for _ in range(M):
        j = np.array(sorted(rng.sample(range(n - hold), k)), dtype=int)
        pb = float((c_arr[j + hold] - c_arr[j]).sum()) * (10**5)
        pb -= 2 * float(spread_pts) * k
        if pb >= real: hits += 1
    return {"real": round(real, 1), "pval": round((hits + 1) / (M + 1), 3), "n_ph": M}

def chay(cap, khung, holds):
    t0 = time.time()
    df = load_m1(cap)
    r = resample(df, khung)
    o = r["open"]; h = r["high"]; lo = r["low"]; c = r["close"]
    sp = float(r["spread"].mean())
    tk, kj = ichi(o, h, lo, c)
    rows = []
    for hold in holds:
        s = sim(o, h, lo, c, tk, kj, hold, sp)
        p = placebo(o, h, lo, c, tk, kj, hold, sp)
        rows.append({"khung": khung, "hold": hold, **s,
                     "pval": p["pval"] if p else None,
                     "real_points": p["real"] if p else None})
    return {"cap": cap, "khung": khung, "bars": len(r), "giay": round(time.time()-t0, 1), "rows": rows}

def main():
    cap = sys.argv[1] if len(sys.argv) > 1 else "EURCAD"
    khungs = sys.argv[2].split(",") if len(sys.argv) > 2 else ["H1","H4","D1"]
    holds  = [int(x) for x in (sys.argv[3].split(",") if len(sys.argv) > 3 else ["1","3","6","12","24"])]
    allr = []
    for kh in khungs:
        rule = "1D" if kh == "D1" else ("4h" if kh == "H4" else "1h")
        try:
            r = chay(cap, kh, holds); allr.append(r)
            for row in r["rows"]:
                print(f"  {cap} {kh} hold={row['hold']:>2} | lenh={row['trades']:>3} "
                      f"points={row['points']:>9.1f} win={row['win'] if row['win'] is None else round(row['win'],1)} "
                      f"pval={row['pval']} ({r['giay']}s)", flush=True)
        except Exception as e:
            print(f"  {cap} {kh} LOI: {str(e)[:150]}", flush=True)
            allr.append({"cap": cap, "khung": kh, "loi": str(e)[:200]})
    out = {"luc": time.strftime("%Y-%m-%d %H:%M:%S"), "thuyet": "ichi cross Kijun + filter Tenkan>Kijun (long)",
           "cap": cap, "ket_qua": allr}
    fp = LAB / "reports" / f"quantlab_ichimoku_{cap}.json"
    fp.parent.mkdir(exist_ok=True)
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DA GHI:", fp)

if __name__ == "__main__":
    main()
