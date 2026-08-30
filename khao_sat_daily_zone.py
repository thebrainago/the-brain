# -*- coding: utf-8 -*-
"""khao_sat_daily_zone.py - Quet tham so TP cho co che #1, do PF + Drawdown.
TP la tham so LAY TU GIA THUYET de do va tinh chinh (khong tu chon).
Mo hinh: tin hieu Daily Zone breakout-return, luoi DCA lot phang, thoat khi
gia hoi phuc ve avg + TP. Do: PF, max drawdown, tan suat, ty le thang.
"""
import sys, time, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORT = ROOT / "lab" / "reports"

PIP = {"JPY": 0.01, "XAU": 0.1, "XAG": 0.01, "USD": 0.0001}
KHONG_PIP = {"XAUUSD": 0.1, "XAGUSD": 0.01, "XAUUSDm": 0.1, "XAUEURm": 0.1, "XAUGBPm": 0.1}

PHA_PIP = 40.0
BUOC_PIP = 100.0
VE_TRONG = 20.0
CUA_SO_HOI = 96
GIOI_HAN_NGAY = 30
TP_SWEEP = [50, 100, 150, 200]


def pip_cua(cap):
    cap = cap.upper()
    if cap in KHONG_PIP:
        return KHONG_PIP[cap]
    for k, v in PIP.items():
        if k in cap:
            return v
    return 0.0001


def atr14_d1(h, l, c):
    n = len(c)
    tr = np.empty(n); tr[0] = h[0] - l[0]
    for i in range(1, n):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1]))
    a = np.full(n, np.nan)
    if n >= 14:
        a[13] = tr[:14].mean()
        for i in range(14, n):
            a[i] = (a[i-1]*13 + tr[i]) / 14.0
    return a


def ep_co(cap):
    """Nap du lieu, tra (t, hi, lo, c, pip, episodes[(loai,anchor,ep0)])."""
    pip = pip_cua(cap)
    f = None
    for pat in (f"{cap}_M1_mq.parquet", f"{cap}_M5_day_du.parquet", f"{cap}_M5.parquet"):
        cand = DATA / pat
        if cand.exists():
            f = cand; break
    if f is None:
        return None
    full = pd.read_parquet(f, columns=["time", "open", "high", "low", "close"])
    full = full[full["high"] > 0]
    m15 = full.set_index("time").resample("15min").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    d1 = full.set_index("time").resample("1D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    h_d = d1["high"].to_numpy(); l_d = d1["low"].to_numpy(); c_d = d1["close"].to_numpy()
    didx = d1.index.to_numpy()
    t = m15.index.to_numpy()
    pos = np.clip(np.searchsorted(didx, t) - 1, 0, len(didx) - 1)
    hp = h_d[np.clip(pos - 1, 0, len(didx) - 1)]
    lp = l_d[np.clip(pos - 1, 0, len(didx) - 1)]
    hi = m15["high"].to_numpy(); lo = m15["low"].to_numpy(); c = m15["close"].to_numpy()
    n = len(c)
    eps = []
    i = 1
    while i < n:
        if i + 1 >= n:
            break
        if c[i] > hp[i] + PHA_PIP * pip:
            loai = 1; anchor = hp[i]; toi = lp[i]
        elif c[i] < lp[i] - PHA_PIP * pip:
            loai = -1; anchor = lp[i]; toi = hp[i]
        else:
            i += 1; continue
        j = i + 1; cua_so = CUA_SO_HOI; bat_dau = None
        while j < n and cua_so > 0:
            if loai == 1 and toi <= c[j] <= anchor + VE_TRONG * pip:
                bat_dau = j; break
            if loai == -1 and anchor - VE_TRONG * pip <= c[j] <= toi:
                bat_dau = j; break
            cua_so -= 1; j += 1
        if bat_dau is None:
            i += 1; continue
        eps.append((loai, anchor, bat_dau))
        i = bat_dau + 1
    return t, hi, lo, c, pip, eps


def mo_phong(loai, anchor, ep0, hi, lo, c, t, pip, tp_pip):
    """Luoi DCA lot phang, thoat khi gia hoi phuc ve avg + TP.
    Tra ve (pnl_moi_lot, so_lot) — loi = +tp_pip nen; lo (timeout) = -MAE pip."""
    e = c[ep0]
    buys = [e]; avg = e
    min_lo = lo[ep0]; max_hi = hi[ep0]
    k = ep0 + 1
    while k < len(c):
        if loai == 1:
            while len(buys) < 2000 and lo[k] <= anchor - BUOC_PIP * pip * len(buys):
                buys.append(anchor - BUOC_PIP * pip * len(buys))
            avg = sum(buys) / len(buys)
            min_lo = min(min_lo, lo[k])
            if hi[k] >= avg + tp_pip * pip:
                return tp_pip, len(buys)
        else:
            while len(buys) < 2000 and hi[k] >= anchor + BUOC_PIP * pip * len(buys):
                buys.append(anchor + BUOC_PIP * pip * len(buys))
            avg = sum(buys) / len(buys)
            max_hi = max(max_hi, hi[k])
            if lo[k] <= avg - tp_pip * pip:
                return tp_pip, len(buys)
        if float((t[k] - t[ep0]) / np.timedelta64(1, 'D')) >= GIOI_HAN_NGAY:
            break
        k += 1
    mae_price = (avg - min_lo) if loai == 1 else (max_hi - avg)
    mae_price = max(mae_price, 0.0)
    return -mae_price / pip, len(buys)


def khao_sat_tp(cap, tp_pip):
    t0 = time.time()
    d = ep_co(cap)
    if d is None:
        return None
    t, hi, lo, c, pip, eps = d
    pnl = []
    for (loai, anchor, ep0) in eps:
        p, nlot = mo_phong(loai, anchor, ep0, hi, lo, c, t, pip, tp_pip)
        pnl.append(p * nlot)
    pnl = np.array(pnl)
    nsig = len(pnl)
    nam = float((t[-1] - t[0]) / np.timedelta64(1, 'D')) / 365.25
    if nsig == 0:
        return {"cap": cap, "tp": tp_pip, "nam": round(nam, 1), "n": 0,
                "tan_suat": 0, "pf": 0, "dd": 0, "win": 0, "giay": round(time.time()-t0, 1)}
    P = pnl[pnl > 0].sum(); L = -pnl[pnl < 0].sum()
    pf = P / L if L > 0 else (99.0 if P > 0 else 0.0)
    eq = np.cumsum(pnl); peak = np.maximum.accumulate(eq); dd = float((peak - eq).max())
    win = float((pnl > 0).mean())
    return {"cap": cap, "tp": tp_pip, "nam": round(nam, 1), "n": nsig,
            "tan_suat": round(nsig / max(nam, 0.01), 1), "pf": round(pf, 2),
            "dd": round(dd, 0), "win": round(win, 3), "giay": round(time.time()-t0, 1)}


def main():
    caps = sys.argv[1:] or ["AUDCAD", "AUDNZD", "EURCAD", "EURGBP", "EURCHF",
                            "EURJPY", "AUDCHF", "EURAUD"]
    REPORT.mkdir(parents=True, exist_ok=True)
    rows = []
    for cap in caps:
        best = None
        for tp in TP_SWEEP:
            r = khao_sat_tp(cap, tp)
            if r is None or r["n"] == 0:
                continue
            if best is None or r["pf"] > best["pf"]:
                best = r
            print(f"  {cap} TP={tp}: n={r['n']} pf={r['pf']} dd={r['dd']} win={r['win']} ({r['giay']}s)", flush=True)
        if best:
            rows.append(best)
    rows.sort(key=lambda x: x["pf"], reverse=True)
    out = REPORT / "khao_sat_daily_zone.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n=== QUET TP - CO CHE DAILY ZONE (best TP moi cap) ===")
    print(f"{'CAP':9} {'TP':>5} {'NAM':>5} {'N':>5} {'/NAM':>6} {'PF':>6} {'DD':>7} {'WIN':>6}")
    for r in rows:
        print(f"{r['cap']:9} {r['tp']:5d} {r['nam']:5.1f} {r['n']:5d} {r['tan_suat']:6.1f} "
              f"{r['pf']:6.2f} {r['dd']:7.0f} {r['win']:6.2f}")
    print("\n->", out)


if __name__ == "__main__":
    main()
