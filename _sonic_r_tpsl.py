# -*- coding: utf-8 -*-
"""SONIC R tren H4 + quet luoi TP/SL. Muc tieu: tim cau hinh RA TIEN.

Chu du an 03/09/2026: *"cau cu loc qua khat khe trong khi dau vao co rat nhieu,
toi can 1 he thong ra tien va hieu qua chu khong can he thong thoa man moi tieu
chi. Vi du mua khi theo sonic r khung h4 tim duoc nguong tp sl phu hop => chot.
Vay thoi."*

LOI SONIC R (theo `SONIC_R_PHAN_TICH.md` cua chinh du an):
  - Dai Dragon / PAC = EMA34 cua high, low, close  -> ba duong tao thanh dai
  - EMA89 = duong xu huong chinh
  - Vao: dang xu huong tang, gia HOI VE cham dai Dragon roi tiep tuc

Bao cao theo dung tieu chi chu du an dat: PnL, maxDD, so lenh, PF, ty le thang,
ky vong moi lenh. KHONG loc bang placebo/FDR o day - day la buoc TIM CAU HINH,
khong phai buoc chung nhan. Nhung VAN dung chi phi THAT va VAN chay
`Open[i+1]` (engine tu dich), vi hai cai do khong phai "tieu chi khat khe" ma
la dieu kien de con so co nghia gi.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from nhan import bien_don_bay as B    # noqa: E402
from nhan import chi_phi as CP        # noqa: E402
from nhan import du_lieu as DU        # noqa: E402
from nhan import mau as MAU           # noqa: E402
from nhan import mo_phong as MP       # noqa: E402


def tin_hieu_sonic_r(df: pd.DataFrame, ema_dragon: int = 34, ema_xu_huong: int = 89,
                     chieu: int = 1) -> np.ndarray:
    """Vao lenh khi gia hoi ve cham dai Dragon TRONG xu huong.

    Tinh tai CLOSE cua bar i; engine tu dich sang OPEN bar i+1.
    """
    c, h, l = df["close"], df["high"], df["low"]
    d_tren = MAU.ema(h, ema_dragon)
    d_duoi = MAU.ema(l, ema_dragon)
    xu_huong = MAU.ema(c, ema_xu_huong)
    if chieu > 0:
        trong_xu_huong = c > xu_huong
        cham_dai = l <= d_tren          # rau duoi cham vao dai tu tren xuong
        khong_thung = c > d_duoi        # dong cua van tren day dai
    else:
        trong_xu_huong = c < xu_huong
        cham_dai = h >= d_duoi
        khong_thung = c < d_tren
    v = (trong_xu_huong & cham_dai & khong_thung).astype(float)
    return np.nan_to_num(v.to_numpy())


def _thong_ke(kq, nam):
    v = kq.vi_the
    loi = np.nan_to_num(kq.loi)
    tr, i, n = [], 0, len(v)
    while i < n:
        if abs(v[i]) < 1e-12:
            i += 1
            continue
        j = i
        while j + 1 < n and abs(v[j + 1]) > 1e-12 and np.sign(v[j + 1]) == np.sign(v[i]):
            j += 1
        tr.append(float(np.sum(loi[i:j + 1])))
        i = j + 1
    tr = np.array(tr)
    if len(tr) == 0:
        return None
    w, lo = tr[tr > 0], tr[tr < 0]
    pf = (w.sum() / abs(lo.sum())) if len(lo) and lo.sum() != 0 else float("inf")
    return {"lenh": len(tr), "lenh_nam": len(tr) / nam,
            "thang": len(w) / len(tr), "pf": pf, "ky_vong": float(np.mean(tr))}


def main(ma="US500CASH", khung="H4"):
    df = DU.nap(ma, khung)
    cp = CP.tu_du_lieu(ma, df)
    cp = cp[0] if isinstance(cp, tuple) else cp
    nam = (df.index[-1] - df.index[0]).days / 365.25
    th = tin_hieu_sonic_r(df)
    kich = float(np.mean(th > 0))
    print(f"=== SONIC R {ma}.{khung} ===")
    print(f"  {len(df)} bar  {df.index[0].date()} -> {df.index[-1].date()} ({nam:.1f} nam)")
    print(f"  spread {cp.spread_frac_chung*1e4:.2f} bps | phi giu {cp.phi_nam_mua*100:.3f} %/nam")
    print(f"  tin hieu kich hoat {kich*100:.2f}% so bar")
    bh = B.do_bien(df, np.ones(len(df)), cp, cac_don_bay=(1.0,), co_tuc=False,
                   ma=ma, khung=khung, da_dich=True)[0][0]
    print(f"  MOC mua-giu: CAGR {bh['cagr']*100:+.2f}%  maxDD {bh['maxdd']*100:.1f}%  "
          f"Sharpe {bh['sharpe']:+.3f}")

    TP = [0.004, 0.006, 0.008, 0.010, 0.015, 0.020, 0.030]
    SL = [0.004, 0.006, 0.008, 0.010, 0.015, 0.020, 0.030]
    GIO = [0, 24, 48, 120]
    ra = []
    for tp in TP:
        for sl in SL:
            for g in GIO:
                kq = MP.chay_tpsl(df, th, tp, sl, cp, gio_toi_da=g,
                                  ma=ma, khung=khung)
                tk = _thong_ke(kq, nam)
                if not tk or tk["lenh"] < 40:
                    continue
                v = kq.von
                dinh = np.maximum.accumulate(np.maximum(v, 1e-300))
                dd = float((v / dinh - 1.0).min())
                cagr = float(v[-1] ** (1 / nam) - 1) if v[-1] > 0 else -1.0
                ra.append({"tp": tp, "sl": sl, "gio": g, "cagr": cagr, "dd": dd,
                           "calmar": cagr / abs(dd) if dd < 0 else np.inf, **tk})
    d = pd.DataFrame(ra)
    if d.empty:
        print("  khong cau hinh nao du 40 lenh")
        return
    d = d.sort_values("cagr", ascending=False)
    print(f"\n  quet {len(d)} cau hinh TP/SL/gio (>= 40 lenh)")
    print(f"  co LAI: {(d.cagr > 0).sum()} | hon mua-giu: {(d.cagr > bh['cagr']).sum()}")
    print(f"\n  {'TP':>6}{'SL':>6}{'gio':>5}{'CAGR':>9}{'maxDD':>8}{'Calmar':>7}"
          f"{'lenh':>6}{'l/nam':>7}{'thang':>7}{'PF':>6}{'kyvong':>8}")
    for _, r in d.head(15).iterrows():
        print(f"  {r.tp*100:>5.1f}%{r.sl*100:>5.1f}%{int(r.gio):>5}{r.cagr*100:>8.2f}%"
              f"{r.dd*100:>7.1f}%{r.calmar:>7.2f}{int(r.lenh):>6}{r.lenh_nam:>7.1f}"
              f"{r.thang*100:>6.1f}%{r.pf:>6.2f}{r.ky_vong*100:>7.3f}%")
    print(f"\n  -- xep theo CALMAR --")
    for _, r in d.sort_values("calmar", ascending=False).head(8).iterrows():
        print(f"  {r.tp*100:>5.1f}%{r.sl*100:>5.1f}%{int(r.gio):>5}{r.cagr*100:>8.2f}%"
              f"{r.dd*100:>7.1f}%{r.calmar:>7.2f}{int(r.lenh):>6}{r.lenh_nam:>7.1f}"
              f"{r.thang*100:>6.1f}%{r.pf:>6.2f}{r.ky_vong*100:>7.3f}%")
    Path("reports").mkdir(exist_ok=True)
    d.to_csv(f"reports/sonic_r_{ma.lower()}_{khung.lower()}.csv", index=False)
    print(f"\n  -> reports/sonic_r_{ma.lower()}_{khung.lower()}.csv")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else "US500CASH", a[1] if len(a) > 1 else "H4")
