# -*- coding: utf-8 -*-
"""Chay 88 co che XU HUONG noi sinh, do bang KHOP RUI RO ngay tu dau.

Dung phep so tho (`S_he - S_mua_giu`) cho ho xu huong la vo nghia: chung o
trong thi truong 79-96% so bar, gan bang mua-giu, nen chenh Sharpe khong noi
duoc gi. Cau hoi dung: *cung mot muc rui ro thi ben nao lai hon?*
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
from nhan import cong as C            # noqa: E402
from nhan import do_luong as DL       # noqa: E402
from nhan import du_lieu as DU        # noqa: E402
from nhan import mo_phong as MP       # noqa: E402
from nhan import ngu_phap as NP       # noqa: E402
from nhan import noi_sinh as NS       # noqa: E402


def mot_doan(d, specs, cp, ma, khung, nhan, top=None):
    bh = B.do_bien(d, np.ones(len(d)), cp, cac_don_bay=(1.0,), co_tuc=False,
                   ma=ma, khung=khung, da_dich=True)[0][0]
    k_bh = MP.chay(d, np.ones(len(d)), cp, da_dich=True, gop="so_hoc")
    r_bh = np.expm1(k_bh.loi)
    print(f"\n--- {nhan} ---")
    print(f"  moc mua-giu: S={bh['sharpe']:+.3f}  CAGR {bh['cagr']*100:+.2f}%  "
          f"DD {bh['maxdd']*100:.1f}%")
    ra = []
    for s in specs:
        try:
            th = NP.sinh_tu_spec(s, d)
        except Exception:
            continue
        k_he = MP.chay(d, th, cp, gop="so_hoc")
        k, _ = C.he_so_khop_rui_ro(np.expm1(k_he.loi), r_bh)
        if k is None:
            continue
        h = B.do_bien(d, th, cp, cac_don_bay=(k,), co_tuc=False,
                      ma=ma, khung=khung)[0][0]
        h1 = B.do_bien(d, th, cp, cac_don_bay=(1.0,), co_tuc=False,
                       ma=ma, khung=khung)[0][0]
        al, t, beta = DL.alpha_newey_west(np.expm1(k_he.loi), r_bh)
        ra.append({"ten": s["ten"], "k": k, "cagr_k": h["cagr"],
                   "dd_k": h["maxdd"], "hon": h["cagr"] - bh["cagr"],
                   "S": h1["sharpe"], "pn": h1["phoi_nhiem"], "t": t, "beta": beta})
    d2 = pd.DataFrame(ra).sort_values("hon", ascending=False)
    print(f"  {len(d2)} co che khop duoc rui ro | HON moc: {(d2.hon > 0).sum()}"
          f" | co t>2: {int((d2.t > 2).sum())}")
    print(f"  {'co che':<34}{'k':>6}{'CAGR@k':>9}{'DD@k':>8}{'hon':>8}"
          f"{'phoi':>6}{'t':>7}{'beta':>7}")
    for _, r in d2.head(top or 10).iterrows():
        print(f"  {r.ten[:33]:<34}{r.k:>6.2f}{r.cagr_k*100:>8.2f}%{r.dd_k*100:>7.1f}%"
              f"{r.hon*100:>+7.2f}{r.pn*100:>5.0f}%{r.t:>7.2f}{r.beta:>7.2f}")
    return d2, bh


def main():
    ma, khung = "US500CASH", "H4"
    df = DU.nap(ma, khung)
    cp = CP.tu_du_lieu(ma, df)
    cp = cp[0] if isinstance(cp, tuple) else cp
    tr, ho = DU.hai_nua(df, 0.6)
    specs = NS.sinh_xu_huong(tr)
    print(f"=== NOI SINH XU HUONG: {ma}.{khung} — {len(specs)} co che ===")

    d_tr, _ = mot_doan(tr, specs, cp, ma, khung, "TRAIN 2016-2022")
    tt = [s for s in specs if s["ten"] in set(d_tr.head(10).ten)]
    d_ho, bh_ho = mot_doan(ho, tt, cp, ma, khung, "HOLDOUT 2022-2026 (top 10 train)")
    print(f"\n  giu dau ngoai mau o CUNG RUI RO: {(d_ho.hon > 0).sum()}/{len(d_ho)}")

    # chuoi DAI: cho biet cau tra loi doi khi doan 15 nam hay khong
    print("\n\n=== CUNG CO CHE, tren 98 NAM SP500 ===")
    dai = pd.read_parquet(Path(__file__).resolve().parent.parent /
                          "data" / "sp500_daily.parquet")
    dai = dai[~dai.index.duplicated(keep="last")].sort_index()
    cpd = CP.MoHinhChiPhi(ma="SP500", spread_frac_chung=0.000095,
                          phi_nam_mua=0.02591, do_tin="SAN")
    sp_dai = NS.sinh_xu_huong(dai.iloc[:len(dai) // 2])
    mot_doan(dai, sp_dai, cpd, "SP500", "D1", "1928-2026 toan bo", top=12)


if __name__ == "__main__":
    main()
