# -*- coding: utf-8 -*-
"""SONIC R: noi luoi TP + do DON BAY. Cau hoi: no ra bao nhieu tien.

Luot truoc dinh nam o MEP luoi (TP = 3,0% la gia tri lon nhat da thu), nen phai
noi len. Va Calmar cua Sonic R (0,34-0,39) gap ~1,8 lan mua-giu (0,20) -> o
CUNG MUC SUT GIAM no phai hon. Do thang.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from _sonic_r_tpsl import _thong_ke, tin_hieu_sonic_r   # noqa: E402
from nhan import bien_don_bay as B                      # noqa: E402
from nhan import chi_phi as CP                          # noqa: E402
from nhan import du_lieu as DU                          # noqa: E402
from nhan import mo_phong as MP                         # noqa: E402


def main(ma="US500CASH", khung="H4"):
    df = DU.nap(ma, khung)
    cp = CP.tu_du_lieu(ma, df)
    cp = cp[0] if isinstance(cp, tuple) else cp
    nam = (df.index[-1] - df.index[0]).days / 365.25
    th = tin_hieu_sonic_r(df)
    bh = B.do_bien(df, np.ones(len(df)), cp, cac_don_bay=(1.0,), co_tuc=False,
                   ma=ma, khung=khung, da_dich=True)[0][0]
    print(f"=== SONIC R {ma}.{khung} — NOI LUOI TP ===")
    print(f"  MOC mua-giu: CAGR {bh['cagr']*100:+.2f}%  maxDD {bh['maxdd']*100:.1f}%  "
          f"Calmar {bh['calmar']:.2f}")

    TP = [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.15]
    SL = [0.006, 0.008, 0.010, 0.015, 0.020]
    GIO = [0, 48, 120, 240]
    ra = []
    for tp in TP:
        for sl in SL:
            for g in GIO:
                kq = MP.chay_tpsl(df, th, tp, sl, cp, gio_toi_da=g, ma=ma, khung=khung)
                tk = _thong_ke(kq, nam)
                if not tk or tk["lenh"] < 40:
                    continue
                v = kq.von
                dd = float((v / np.maximum.accumulate(np.maximum(v, 1e-300)) - 1).min())
                cagr = float(v[-1] ** (1 / nam) - 1) if v[-1] > 0 else -1.0
                ra.append({"tp": tp, "sl": sl, "gio": g, "cagr": cagr, "dd": dd,
                           "calmar": cagr / abs(dd) if dd < 0 else np.inf,
                           "loi": np.nan_to_num(kq.loi), **tk})
    d = pd.DataFrame(ra).sort_values("calmar", ascending=False)
    print(f"\n  quet {len(d)} cau hinh | co lai {(d.cagr>0).sum()} | "
          f"Calmar hon mua-giu: {(d.calmar > bh['calmar']).sum()}")
    print(f"\n  {'TP':>6}{'SL':>6}{'gio':>5}{'CAGR':>9}{'maxDD':>8}{'Calmar':>7}"
          f"{'lenh':>6}{'thang':>7}{'PF':>6}")
    for _, r in d.head(10).iterrows():
        print(f"  {r.tp*100:>5.1f}%{r.sl*100:>5.1f}%{int(r.gio):>5}{r.cagr*100:>8.2f}%"
              f"{r.dd*100:>7.1f}%{r.calmar:>7.2f}{int(r.lenh):>6}{r.thang*100:>6.1f}%"
              f"{r.pf:>6.2f}")

    # --- DON BAY tren cau hinh Calmar tot nhat ---
    tot = d.iloc[0]
    print(f"\n=== DON BAY tren TP {tot.tp*100:.1f}% / SL {tot.sl*100:.1f}% / "
          f"gio {int(tot.gio)} ===")
    print(f"  {'L':>5}{'CAGR':>9}{'maxDD':>8}{'Calmar':>7}")
    r1 = np.expm1(tot.loi)
    for L in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0):
        x = 1.0 + r1 * L
        if (x <= 0).any():
            print(f"  {L:>5.1f}   CHAY TAI KHOAN")
            continue
        v = np.cumprod(x)
        dd = float((v / np.maximum.accumulate(v) - 1).min())
        cg = float(v[-1] ** (1 / nam) - 1)
        moc = "  <-- ngang sut giam mua-giu" if abs(dd - bh["maxdd"]) < 0.03 else ""
        print(f"  {L:>5.1f}{cg*100:>8.2f}%{dd*100:>7.1f}%"
              f"{cg/abs(dd) if dd < 0 else 0:>7.2f}{moc}")

    print(f"\n  -- SO O CUNG SUT GIAM voi mua-giu ({bh['maxdd']*100:.1f}%) --")
    for L in np.arange(1.0, 5.01, 0.1):
        x = 1.0 + r1 * L
        if (x <= 0).any():
            break
        v = np.cumprod(x)
        dd = float((v / np.maximum.accumulate(v) - 1).min())
        if dd <= bh["maxdd"]:
            cg = float(v[-1] ** (1 / nam) - 1)
            print(f"  Sonic R @ {L:.1f}x : CAGR {cg*100:+.2f}%  maxDD {dd*100:.1f}%")
            print(f"  mua-giu   @ 1.0x : CAGR {bh['cagr']*100:+.2f}%  "
                  f"maxDD {bh['maxdd']*100:.1f}%")
            print(f"  -> HON {(cg-bh['cagr'])*100:+.2f} diem %/nam o CUNG rui ro")
            break


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else "US500CASH", a[1] if len(a) > 1 else "H4")
