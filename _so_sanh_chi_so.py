# -*- coding: utf-8 -*-
"""So sanh 8 chi so CASH cua XM: "em a" co thanh tien khong?

Chu du an goi UK100 va US500 la "nhung chi so em a va an toan nhat". Cau hoi
do do duoc: bien dong thap co bu lai duoc phi tai tro khong.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from nhan import bien_don_bay as B   # noqa: E402
from nhan import chi_phi as CP       # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"

CHI_SO = {
    "UK100": ("xm_uk100cash_d1.parquet", 0.06879),
    "US500": ("xm_us500cash_d1.parquet", 0.05761),
    "US30": ("xm_us30cash_d1.parquet", 0.05767),
    "GER40": ("xm_ger40cash_d1.parquet", 0.04879),
    "EU50": ("xm_eu50cash_d1.parquet", 0.05389),
    "FRA40": ("xm_fra40cash_d1.parquet", 0.05380),
    "JP225": ("xm_jp225cash_d1.parquet", 0.02591),
    "AUS200": ("xm_aus200cash_d1.parquet", 0.07484),
}


def main():
    print(f"{'chi so':<8}{'bar':>6}{'tu':>12}{'vol':>7}{'maxDD':>8}"
          f"{'phi/nam':>9}{'CAGR tho':>10}{'CAGR rong':>11}{'Sharpe':>8}{'Calmar':>8}")
    print("-" * 89)
    hang = []
    for ten, (f, phi) in CHI_SO.items():
        p = DATA / f
        if not p.exists():
            print(f"{ten:<8} khong co {f}")
            continue
        d = pd.read_parquet(p)
        d = d[~d.index.duplicated(keep="last")].sort_index()
        n = len(d)
        cp = CP.MoHinhChiPhi(ma=ten, spread_frac_chung=0.000095,
                             phi_nam_mua=phi, do_tin="SAN")
        cp0 = CP.MoHinhChiPhi(ma=ten, do_tin="KHAI")
        v = np.ones(n)
        rong = B.do_bien(d, v, cp, cac_don_bay=(1.0,), co_tuc=False,
                         ma=ten, khung="D1", da_dich=True)[0][0]
        tho = B.do_bien(d, v, cp0, cac_don_bay=(1.0,), co_tuc=False,
                        ma=ten, khung="D1", da_dich=True)[0][0]
        hang.append({"ten": ten, "n": n, "tu": d.index[0].date(),
                     "vol": rong["vol"], "dd": rong["maxdd"], "phi": phi,
                     "cagr_tho": tho["cagr"], "cagr": rong["cagr"],
                     "S": rong["sharpe"], "calmar": rong["calmar"]})
        print(f"{ten:<8}{n:>6}{str(d.index[0].date()):>12}{rong['vol']*100:>6.1f}%"
              f"{rong['maxdd']*100:>7.1f}%{phi*100:>8.2f}%{tho['cagr']*100:>9.2f}%"
              f"{rong['cagr']*100:>10.2f}%{rong['sharpe']:>8.3f}{rong['calmar']:>8.2f}")

    print("\n-- xep theo Sharpe RONG (sau phi that cua XM, khong co tuc) --")
    for r in sorted(hang, key=lambda x: -x["S"]):
        tran = B.tran_cagr(r["S"], 0.5) * 100
        print(f"  {r['ten']:<8}S={r['S']:+.3f}  vol {r['vol']*100:4.1f}%  "
              f"phi {r['phi']*100:.2f}%/nam  ->  tran nua Kelly {tran:5.1f} %/nam")

    print("\n-- 'em a' co thanh tien khong? --")
    a = sorted(hang, key=lambda x: x["vol"])
    print(f"  em nhat (vol thap nhat): {a[0]['ten']} vol {a[0]['vol']*100:.1f}%  "
          f"-> CAGR rong {a[0]['cagr']*100:+.2f}%  Sharpe {a[0]['S']:+.3f}")
    b = sorted(hang, key=lambda x: -x["S"])
    print(f"  tot nhat theo Sharpe   : {b[0]['ten']} vol {b[0]['vol']*100:.1f}%  "
          f"-> CAGR rong {b[0]['cagr']*100:+.2f}%  Sharpe {b[0]['S']:+.3f}")
    if hang:
        c = [r for r in hang if r["cagr"] < 0]
        if c:
            print(f"  AM sau phi: {', '.join(r['ten'] for r in c)}")


if __name__ == "__main__":
    main()
