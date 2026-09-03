# -*- coding: utf-8 -*-
"""BO LOC XU HUONG AN TIEN O DAU? Do tren 98 nam SP500, tach theo CHE DO.

Chu du an 03/09/2026: *"Neu thi truong bull thi ve li ta cang de kiem loi voi
cac he thong trendfollowing va breakout. Tai sao mot thi truong co trend ma ta
co he thong + don bay lai khong an duoc no?"*

Gia thuyet cua toi: **bo loc xu huong khong tra tien trong thi truong bo dai;
no tra tien trong thi truong co SUT GIAM LON VA KEO DAI.** Trong mot nhip tang
dai, he theo xu huong TOI UU chinh la mua-giu (luon long) - moi bo loc co luc
thoat deu phai bo lo mot phan nhip len, va no chi hoan von neu ne duoc mot cu
sut du sau.

Neu dung: bo loc xu huong phai THUA mua-giu o 2011-2026 va 2011-2021, nhung
THANG o 1929-1932, 2000-2002, 2007-2009.
Neu sai (bo loc thua o MOI che do) thi gia thuyet nay bi bac bo va van de nam
o cho khac.
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

#: Che do thi truong. Chon theo SU KIEN lich su, khong theo toi uu hoa.
CHE_DO = [
    ("1929-1932 sup do", 1929, 1932), ("1933-1945 hoi phuc", 1933, 1945),
    ("1946-1965 bo dai", 1946, 1965), ("1966-1982 di ngang", 1966, 1982),
    ("1983-1999 bo dai", 1983, 1999), ("2000-2002 dot-com", 2000, 2002),
    ("2003-2007 hoi phuc", 2003, 2007), ("2008-2009 khung hoang", 2008, 2009),
    ("2010-2021 bo dai", 2010, 2021), ("2022-2026 gan day", 2022, 2026),
    ("TOAN BO 1928-2026", 1928, 2026),
]

#: He THEO XU HUONG - deu la loai o trong thi truong PHAN LON thoi gian.
HE = {
    "close>SMA200": lambda d: MAU.m_do_doc_ma(d, n=200, cua_so=1, nguong=-1e9)
    if False else (d["close"] > MAU.sma(d["close"], 200)).astype(float).to_numpy(),
    "close>SMA50": lambda d: (d["close"] > MAU.sma(d["close"], 50)).astype(float).to_numpy(),
    "SMA50>SMA200": lambda d: (MAU.sma(d["close"], 50) >
                               MAU.sma(d["close"], 200)).astype(float).to_numpy(),
    "donchian50": lambda d: MAU.m_donchian(d, n=50),
    "momentum12thang": lambda d: (d["close"] >
                                  d["close"].shift(252)).astype(float).to_numpy(),
}


def main():
    df = pd.read_parquet(DATA / "sp500_daily.parquet")
    df = df[~df.index.duplicated(keep="last")].sort_index()
    # chi phi: spread chi so + phi tai tro RE NHAT do duoc (JP225 2,59%/nam la
    # muc thap nhat quan sat duoc tren san that; dung no de KHONG do loi cho phi)
    cp = CP.MoHinhChiPhi(ma="SP500", spread_frac_chung=0.000095,
                         phi_nam_mua=0.02591, do_tin="SAN")

    print(f"{'che do':<22}{'nam':>4}{'B&H CAGR':>10}{'B&H DD':>8}  "
          + "".join(f"{k:>16}" for k in HE))
    print("-" * (44 + 16 * len(HE)))
    tong = {k: [0, 0] for k in HE}          # [thang, tong]
    for ten, a, b in CHE_DO:
        d = df[(df.index.year >= a) & (df.index.year <= b)]
        if len(d) < 400:
            continue
        bh = B.do_bien(d, np.ones(len(d)), cp, cac_don_bay=(1.0,), co_tuc=False,
                       ma="SP500", khung="D1", da_dich=True)[0][0]
        dong = (f"{ten:<22}{b-a+1:>4}{bh['cagr']*100:>9.2f}%"
                f"{bh['maxdd']*100:>7.1f}%  ")
        for k, f in HE.items():
            try:
                th = np.nan_to_num(np.asarray(f(d), float))
            except Exception:
                dong += f"{'loi':>16}"
                continue
            h = B.do_bien(d, th, cp, cac_don_bay=(1.0,), co_tuc=False,
                          ma="SP500", khung="D1")[0][0]
            hon = h["cagr"] - bh["cagr"]
            if ten.startswith("TOAN BO") is False:
                tong[k][1] += 1
                if hon > 0:
                    tong[k][0] += 1
            dong += f"{hon*100:>+9.2f}/{h['phoi_nhiem']*100:>3.0f}%"
        print(dong)

    print("\n-- so che do (khong ke dong TOAN BO) ma he THANG mua-giu --")
    for k, (t, n) in tong.items():
        print(f"   {k:<18} {t}/{n}")

    print("\n-- CHI cac che do co SUT GIAM > 40% --")
    for ten, a, b in CHE_DO:
        d = df[(df.index.year >= a) & (df.index.year <= b)]
        if len(d) < 400:
            continue
        bh = B.do_bien(d, np.ones(len(d)), cp, cac_don_bay=(1.0,), co_tuc=False,
                       ma="SP500", khung="D1", da_dich=True)[0][0]
        if bh["maxdd"] > -0.40 or ten.startswith("TOAN BO"):
            continue
        print(f"   {ten:<22} B&H CAGR {bh['cagr']*100:+7.2f}%  DD {bh['maxdd']*100:6.1f}%")
        for k, f in HE.items():
            th = np.nan_to_num(np.asarray(f(d), float))
            h = B.do_bien(d, th, cp, cac_don_bay=(1.0,), co_tuc=False,
                          ma="SP500", khung="D1")[0][0]
            print(f"      {k:<18} CAGR {h['cagr']*100:+7.2f}%  DD {h['maxdd']*100:6.1f}%"
                  f"  hon B&H {(h['cagr']-bh['cagr'])*100:+7.2f} diem%")


if __name__ == "__main__":
    main()
