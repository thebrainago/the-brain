# -*- coding: utf-8 -*-
"""PLACEBO cho ung vien xu huong manh nhat (03/09/2026).

Memory `bo-loc-xu-huong-rot` ghi: ho bo loc xu huong TUNG ROT PLACEBO 74-81%.
Ung vien hom nay (`close > SMA200`, t_alpha 3,56 tren 98 nam, hon mua-giu
+3,45 diem%/nam o cung rui ro) chua duoc thu lai cua do.

`cong.placebo` hoan vi CHUOI VI THE (quay vong + bootstrap khoi), khong hoan
vi chuoi lai/lo — quy tac 19 cua du an: hoan vi lai/lo giu nguyen phan phoi
nen LUON ra ~50% va se "ket luan" sai rang moi he deu truot.

Chay tren CA BA cua so de biet ket qua co doan thoi ky hay khong.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from nhan import chi_phi as CP     # noqa: E402
from nhan import cong as C         # noqa: E402
from nhan import mau as MAU        # noqa: E402
from nhan import mo_phong as MP    # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"

HE = {
    "close>SMA200": lambda d: (d["close"] > MAU.sma(d["close"], 200)
                               ).astype(float).to_numpy(),
    "close>EMA20": lambda d: (d["close"] > MAU.ema(d["close"], 20)
                              ).astype(float).to_numpy(),
    "SMA50>SMA200": lambda d: (MAU.sma(d["close"], 50) >
                               MAU.sma(d["close"], 200)).astype(float).to_numpy(),
}


def main():
    df = pd.read_parquet(DATA / "sp500_daily.parquet")
    df = df[~df.index.duplicated(keep="last")].sort_index()
    cp = CP.MoHinhChiPhi(ma="SP500", spread_frac_chung=0.000095,
                         phi_nam_mua=0.02591, do_tin="SAN")

    print(f"{'he':<16}{'cua so':<14}{'p_xau_nhat':>12}{'p_tot_nhat':>12}"
          f"{'khoi':>6}  ket luan")
    print("-" * 74)
    for ten, f in HE.items():
        for nhan, a, b in (("1928-2026", 1928, 2026), ("1976-2026", 1976, 2026),
                           ("2011-2026", 2011, 2026)):
            d = df[(df.index.year >= a) & (df.index.year <= b)]
            th = np.nan_to_num(np.asarray(f(d), float))
            kq = MP.chay(d, th, cp, ma="SP500", khung="D1")
            r = C.placebo(d, kq, cp)
            px = r.get("p_xau_nhat")
            pt = r.get("p_tot_nhat")
            kl = "DAT" if (px is not None and px <= 0.05) else "ROT"
            print(f"{ten:<16}{nhan:<14}{px:>12.4f}{pt:>12.4f}"
                  f"{r.get('do_dai_khoi', 0):>6}  {kl}"
                  + (f"  ({r.get('ly_do','')})" if r.get("ly_do") else ""))


if __name__ == "__main__":
    main()
