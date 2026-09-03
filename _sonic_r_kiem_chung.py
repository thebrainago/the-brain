# -*- coding: utf-8 -*-
"""SONIC R: kiem chung cau hinh TP 5% / SL 1% ra ngoai mau.

KHONG phai de bac bo - de biet con so 18,72%/nam co dung ngoai mau khong, va
no on dinh den dau khi doi tham so / doi tai san / doi giai doan.
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

TP, SL, GIO = 0.05, 0.01, 0


def _do(d, cp, ma, khung, tp=TP, sl=SL, gio=GIO, L=1.0):
    th = tin_hieu_sonic_r(d)
    kq = MP.chay_tpsl(d, th, tp, sl, cp, gio_toi_da=gio, ma=ma, khung=khung)
    nam = max((d.index[-1] - d.index[0]).days / 365.25, 1e-9)
    r1 = np.expm1(np.nan_to_num(kq.loi))
    x = 1.0 + r1 * L
    if (x <= 0).any():
        return None
    v = np.cumprod(x)
    dd = float((v / np.maximum.accumulate(v) - 1).min())
    cg = float(v[-1] ** (1 / nam) - 1)
    tk = _thong_ke(kq, nam) or {}
    return {"cagr": cg, "dd": dd, "calmar": cg / abs(dd) if dd < 0 else 0.0, **tk}


def _moc(d, cp, ma, khung):
    return B.do_bien(d, np.ones(len(d)), cp, cac_don_bay=(1.0,), co_tuc=False,
                     ma=ma, khung=khung, da_dich=True)[0][0]


def main():
    ma, khung = "US500CASH", "H4"
    df = DU.nap(ma, khung)
    cp = CP.tu_du_lieu(ma, df)
    cp = cp[0] if isinstance(cp, tuple) else cp
    tr, ho = DU.hai_nua(df, 0.6)

    print(f"=== 1. TRAIN / HOLDOUT (TP {TP*100:.0f}% / SL {SL*100:.0f}%) ===")
    print(f"  {'doan':<10}{'nam':<24}{'CAGR':>9}{'maxDD':>8}{'Calmar':>8}"
          f"{'lenh':>6}{'PF':>6}   moc mua-giu")
    for nhan, d in (("TRAIN", tr), ("HOLDOUT", ho), ("CA CHUOI", df)):
        r = _do(d, cp, ma, khung)
        m = _moc(d, cp, ma, khung)
        print(f"  {nhan:<10}{str(d.index[0].date())+' -> '+str(d.index[-1].date()):<24}"
              f"{r['cagr']*100:>8.2f}%{r['dd']*100:>7.1f}%{r['calmar']:>8.2f}"
              f"{int(r['lenh']):>6}{r['pf']:>6.2f}   "
              f"{m['cagr']*100:+.2f}% / {m['maxdd']*100:.1f}% / {m['calmar']:.2f}")

    print(f"\n=== 2. LAN CAN TP/SL tren HOLDOUT (cao nguyen hay cai gai?) ===")
    print(f"  {'TP':>6}{'SL':>6}{'CAGR':>9}{'maxDD':>8}{'Calmar':>8}{'lenh':>6}{'PF':>6}")
    o = []
    for tp in (0.03, 0.04, 0.05, 0.06, 0.08):
        for sl in (0.008, 0.010, 0.015):
            r = _do(ho, cp, ma, khung, tp=tp, sl=sl)
            if not r or not r.get("lenh"):
                continue
            o.append(r["calmar"])
            danh = "  <-- tam" if (tp == TP and sl == SL) else ""
            print(f"  {tp*100:>5.1f}%{sl*100:>5.1f}%{r['cagr']*100:>8.2f}%"
                  f"{r['dd']*100:>7.1f}%{r['calmar']:>8.2f}{int(r['lenh']):>6}"
                  f"{r['pf']:>6.2f}{danh}")
    if o:
        a = np.array(o)
        print(f"  -> {len(a)} o | duong {np.mean(a > 0)*100:.0f}% | "
              f"trung vi Calmar {np.median(a):.2f} | tot nhat {a.max():.2f} "
              f"(boi dinh {a.max()/max(np.median(a),1e-9):.2f}x)")

    print(f"\n=== 3. TAI SAN KHAC (cung TP/SL, khong chinh gi) ===")
    print(f"  {'tai san':<16}{'CAGR':>9}{'maxDD':>8}{'Calmar':>8}{'lenh':>6}"
          f"{'PF':>6}   moc mua-giu Calmar")
    for m2 in ("XM_UK100CASH", "XM_JP225CASH", "XM_GER40CASH", "XM_US30CASH"):
        try:
            d2 = DU.nap(m2, "H4")
            cp2 = CP.tu_du_lieu(m2, d2)
            cp2 = cp2[0] if isinstance(cp2, tuple) else cp2
            r = _do(d2, cp2, m2, "H4")
            mo = _moc(d2, cp2, m2, "H4")
            if not r:
                continue
            print(f"  {m2:<16}{r['cagr']*100:>8.2f}%{r['dd']*100:>7.1f}%"
                  f"{r['calmar']:>8.2f}{int(r['lenh']):>6}{r['pf']:>6.2f}"
                  f"   {mo['calmar']:.2f}")
        except Exception as e:
            print(f"  {m2:<16}loi: {type(e).__name__} {str(e)[:40]}")


if __name__ == "__main__":
    main()
