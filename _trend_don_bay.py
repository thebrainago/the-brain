# -*- coding: utf-8 -*-
"""BO LOC XU HUONG CO LAM DON BAY GANH DUOC NHIEU HON KHONG?

Cau hoi cua chu du an 03/09/2026: *"thi truong co trend ma ta co he thong +
don bay lai khong an duoc no"*.

Lap luan can kiem: rao can cua don bay la SUT GIAM, khong phai loi nhuan
(Calmar phang 0,37-0,45 o moi muc L tren mot he CO DINH). Neu bo loc xu huong
cat maxDD manh ma chi ton ~1 diem CAGR thi Calmar CUA HE tang -> gioi han don
bay noi ra -> CAGR cuoi cung co the cao hon mua-giu don bay.

Kiem tren 98 nam, phi tai tro RE NHAT quan sat duoc tren san that (2,59%/nam
cua JP225) de khong do loi cho phi. So SANH O CUNG SUT GIAM, khong so tho.

CANH BAO da ghi trong so (memory `bo-loc-xu-huong-rot`): bo loc xu huong tung
thang mua-giu CO PHI nhung **rot placebo 74-81%** va **thua phoi nhiem co
dinh**. File nay khong bo qua dieu do - no do lai o CUNG MUC SUT GIAM, va do
chinh la phep "thua phoi nhiem co dinh" noi tren.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from nhan import bien_don_bay as B     # noqa: E402
from nhan import chi_phi as CP         # noqa: E402
from nhan import mau as MAU            # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
L_QUET = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0)


def _he(d, ten):
    if ten == "mua-giu":
        return np.ones(len(d)), True
    if ten == "close>SMA200":
        return (d["close"] > MAU.sma(d["close"], 200)).astype(float).to_numpy(), False
    if ten == "SMA50>SMA200":
        return (MAU.sma(d["close"], 50) >
                MAU.sma(d["close"], 200)).astype(float).to_numpy(), False
    raise KeyError(ten)


def bang(d, nhan, cp):
    print(f"\n=== {nhan} ===")
    print(f"{'he':<16}{'L':>5}{'CAGR':>9}{'maxDD':>9}{'Calmar':>8}{'Sharpe':>8}{'phoi':>6}")
    ket = {}
    for ten in ("mua-giu", "close>SMA200", "SMA50>SMA200"):
        th, dd = _he(d, ten)
        ket[ten] = []
        for L in L_QUET:
            h = B.do_bien(d, th, cp, cac_don_bay=(L,), co_tuc=False,
                          ma="SP500", khung="D1", da_dich=dd)[0][0]
            ket[ten].append(h)
            print(f"{ten:<16}{L:>5.1f}{h['cagr']*100:>8.2f}%{h['maxdd']*100:>8.1f}%"
                  f"{h['calmar']:>8.2f}{h['sharpe']:>8.3f}{h['phoi_nhiem']*100:>5.0f}%"
                  + ("  <-- CHAY TK" if h["chay"] else ""))
    return ket


def so_o_cung_sut_giam(ket, muc):
    """Voi moi he: lay muc don bay CAO NHAT ma maxDD con nong hon `muc`."""
    print(f"\n-- SO O CUNG MUC SUT GIAM (maxDD khong qua {muc*100:.0f}%) --")
    print(f"{'he':<16}{'L cao nhat':>11}{'CAGR':>9}{'maxDD':>9}{'Calmar':>8}")
    tot = None
    for ten, hs in ket.items():
        hop = [h for h in hs if h["maxdd"] >= muc and not h["chay"]]
        if not hop:
            print(f"{ten:<16}{'khong co':>11}")
            continue
        h = max(hop, key=lambda x: x["cagr"])
        print(f"{ten:<16}{h['don_bay']:>11.1f}{h['cagr']*100:>8.2f}%"
              f"{h['maxdd']*100:>8.1f}%{h['calmar']:>8.2f}")
        if tot is None or h["cagr"] > tot[1]:
            tot = (ten, h["cagr"], h["don_bay"])
    if tot:
        print(f"   -> TOT NHAT o muc nay: {tot[0]} @ {tot[2]:.1f}x = {tot[1]*100:.2f} %/nam")


def main():
    df = pd.read_parquet(DATA / "sp500_daily.parquet")
    df = df[~df.index.duplicated(keep="last")].sort_index()
    cp = CP.MoHinhChiPhi(ma="SP500", spread_frac_chung=0.000095,
                         phi_nam_mua=0.02591, do_tin="SAN")

    for nhan, a, b in (("98 nam 1928-2026", 1928, 2026),
                       ("50 nam 1976-2026", 1976, 2026),
                       ("15 nam 2011-2026", 2011, 2026)):
        d = df[(df.index.year >= a) & (df.index.year <= b)]
        ket = bang(d, nhan, cp)
        for muc in (-0.35, -0.50, -0.65):
            so_o_cung_sut_giam(ket, muc)


if __name__ == "__main__":
    main()
