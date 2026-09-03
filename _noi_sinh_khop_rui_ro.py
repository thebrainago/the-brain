# -*- coding: utf-8 -*-
"""Do lai top ung vien noi sinh bang KHOP RUI RO, khong bang chenh Sharpe tho.

VI SAO. `_noi_sinh_chay.py` xep hang bang `S_he - S_mua_giu` tren cung doan.
Do la phep so sai khi hai ben o hai muc phoi nhiem khac han nhau, va du an da
sua dung loi nay trong `cong.he_so_khop_rui_ro` tu 30/08/2026.

Do that 03/09 tren US500CASH.H4: moc mua-giu co Sharpe **+0,294 tren TRAIN**
nhung **+0,768 tren HOLDOUT** - holdout la mot doan bo tot han. Mot co che chi
o trong thi truong 10% thoi gian gan nhu chac chan thua phep so tho o doan do,
KE CA khi chinh no tot len: `ns_stochastic14_<_q10_giu1` di tu S=0,624 (train)
len S=0,669 (holdout) ma van bi cham "chenh -0,098".

Cau hoi dung: *cung mot muc rui ro thi ben nao lai hon?*
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from nhan import bien_don_bay as B      # noqa: E402
from nhan import chi_phi as CP          # noqa: E402
from nhan import cong as C              # noqa: E402
from nhan import do_luong as DL         # noqa: E402
from nhan import du_lieu as DU          # noqa: E402
from nhan import mo_phong as MP         # noqa: E402
from nhan import ngu_phap as NP         # noqa: E402
from nhan import noi_sinh as NS         # noqa: E402

BAO = Path(__file__).resolve().parent / "reports"


def main(ma="US500CASH", khung="H4", top=12):
    df = DU.nap(ma, khung)
    cp = CP.tu_du_lieu(ma, df)
    cp = cp[0] if isinstance(cp, tuple) else cp
    tr, ho = DU.hai_nua(df, 0.6)

    f = BAO / f"noi_sinh_{ma.lower()}_{khung.lower()}.csv"
    xh = pd.read_csv(f).head(top)
    specs = {s["ten"]: s for s in (NS.sinh(tr) + NS.sinh_cap(tr, toi_da=2500))}

    print(f"=== KHOP RUI RO tren HOLDOUT: {ma}.{khung} ===")
    bh = B.do_bien(ho, np.ones(len(ho)), cp, cac_don_bay=(1.0,), co_tuc=False,
                   ma=ma, khung=khung, da_dich=True)[0][0]
    k_bh = MP.chay(ho, np.ones(len(ho)), cp, da_dich=True, gop="so_hoc")
    print(f"  moc mua-giu holdout: S={bh['sharpe']:+.3f}  CAGR {bh['cagr']*100:+.2f}%  "
          f"DD {bh['maxdd']*100:.1f}%  phoi nhiem 100%")
    print(f"\n  {'co che':<44}{'S_ho':>7}{'phoi':>6}{'k':>6}"
          f"{'CAGR@k':>9}{'DD@k':>8}{'alpha%':>8}{'t':>6}{"beta":>7}")
    ket = []
    for _, r in xh.iterrows():
        s = specs.get(r["ten"])
        if s is None:
            continue
        th = NP.sinh_tu_spec(s, ho)
        h = B.do_bien(ho, th, cp, cac_don_bay=(1.0,), co_tuc=False,
                      ma=ma, khung=khung)[0][0]
        k_he = MP.chay(ho, th, cp, gop="so_hoc")
        k, _ = C.he_so_khop_rui_ro(np.expm1(k_he.loi), np.expm1(k_bh.loi))
        if k is None:
            print(f"  {r['ten'][:43]:<44}{h['sharpe']:>7.3f}{h['phoi_nhiem']*100:>5.0f}%"
                  f"   khong khop rui ro duoc")
            continue
        hk = B.do_bien(ho, th, cp, cac_don_bay=(k,), co_tuc=False,
                       ma=ma, khung=khung)[0][0]
        al, t, beta = DL.alpha_newey_west(np.expm1(k_he.loi), np.expm1(k_bh.loi))
        ket.append({"ten": r["ten"], "S_ho": h["sharpe"], "k": k,
                    "cagr_k": hk["cagr"], "dd_k": hk["maxdd"],
                    "hon_moc": hk["cagr"] - bh["cagr"], "t": t, "beta": beta})
        print(f"  {r['ten'][:43]:<44}{h['sharpe']:>7.3f}{h['phoi_nhiem']*100:>5.0f}%"
              f"{k:>6.2f}{hk['cagr']*100:>8.2f}%{hk['maxdd']*100:>7.1f}%"
              f"{(hk['cagr']-bh['cagr'])*100:>+7.2f}{t:>6.2f}{beta:>7.2f}")

    if ket:
        d = pd.DataFrame(ket).sort_values("hon_moc", ascending=False)
        thang = d[d.hon_moc > 0]
        print(f"\n  HON moc o CUNG RUI RO: {len(thang)}/{len(d)}")
        print(f"  co t_alpha > 2      : {int((d.t.abs() > 2).sum())}")
        # `alpha_newey_west` tra (alpha_nam, t_alpha, BETA) - gia tri thu ba la
        # BETA chu KHONG phai p-value. Da dan nhan sai cot nay 03/09/2026.
        # Nguong |t| cho Bonferroni tren k phep thu, hai phia:
        from scipy import stats as _st
        nguong_t = float(_st.norm.ppf(1 - 0.05 / (2 * max(len(d), 1))))
        print(f"  nguong |t| Bonferroni cho {len(d)} lan nhin: {nguong_t:.2f}")
        dat = d[(d.hon_moc > 0) & (d.t.abs() > nguong_t)]
        print(f"  QUA CA HAI          : {len(dat)}")
        for _, r in dat.iterrows():
            print(f"     {r.ten}  +{r.hon_moc*100:.2f} diem%/nam  t={r.t:.2f} beta={r.beta:.2f}")


if __name__ == "__main__":
    a = sys.argv[1:] or ["US500CASH", "H4"]
    main(a[0], a[1] if len(a) > 1 else "H4")
