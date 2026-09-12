# -*- coding: utf-8 -*-
"""MO XE ung vien manh nhat tim duoc 05/09: `mean_reversion_z5` tren XM_US100CASH.

Chu du an: *"phai tim ra duoc he thong co edge hoac phai chinh sua thong so de
ra duoc he thong co edge"*.

Ung vien: mua khi z-score 5 ngay cua close < -1, thoat khi z >= -1. XM US100Cash
(CFD NASDAQ-100 tren XM - symbol GIAO DICH DUOC, khong phai chuoi nghien cuu).

DA BIET truoc file nay (do o phien 05/09):
  - holdout 2020-05 -> 2026-07: L=1,5 cho CAGR 21,1% / maxDD -19,9% /
    Sharpe 1,21 / Calmar 1,06 / 204 lenh / phoi nhiem 30,5%
  - mua-giu DON BAY LEN CUNG MUC DD chi cho 6,35% -> hon 14,8 diem
  - duong moi nam trong 7 nam, thang mua-giu cung DD 5/7
  - song den spread 10 bps (spread CFD chi so do that cua du an: 0,78 bps)
  - train 2011-2020: CAGR 10,4% / Sharpe 0,72 - thap hon nhung CUNG DAU

CHUA BIET, va day la nhung gi file nay do:
  1. **Hinh dang vung lan can.** Cao nguyen hay cai gai? Quet (n, nguong z).
     Mot cai gai = mot con so ngau nhien; cao nguyen = mot co che.
  2. **Placebo.** Hoan vi KHOI VI THE (khong hoan vi lai/lo - do la loi 29/07).
  3. **Ca chuoi 14,9 nam**, de vuot tieu chi `song_du` ma holdout 6,17 nam
     khong dat.
  4. **Doi chieu voi V6/IBS** cua chinh du an - neu day la cung mot hien tuong
     thi no la XAC NHAN chu khong phai phat hien thu hai.
"""
from __future__ import annotations

import json
import sys
import warnings

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from nhan import bien_don_bay as B
from nhan import chi_phi as CP
from nhan import cong as CONG
from nhan import cong_ra_tien as CRT
from nhan import du_lieu as DL
from nhan import mo_phong as MP
from nhan import ngu_phap as NP
from pathlib import Path

MA, KHUNG, TEN = "XM_US100CASH", "D1", "mean_reversion_z5"
L = 1.5


def spec_voi(n: int, nguong: float) -> dict:
    """Ban sao cua spec goc voi (cua so z, nguong z) thay doi."""
    return {
        "ten": "z%d_duoi_%.2f" % (n, nguong), "ho": "quay_ve_trung_binh",
        "chieu": 1, "giu": 500,
        "vao": [{"trai": {"chi_bao": "zscore",
                          "cua": {"chi_bao": "gia", "cot": "close"}, "n": n},
                 "phep": "<", "phai": {"hang": float(nguong)}}],
        "ra": [{"trai": {"chi_bao": "zscore",
                         "cua": {"chi_bao": "gia", "cot": "close"}, "n": n},
                "phep": ">=", "phai": {"hang": float(nguong)}}],
    }


def _cp(d):
    c = CP.tu_du_lieu(MA, d)
    return c[0] if isinstance(c, tuple) else c


def do_mot(d, spec, cp, don_bay=L):
    v = np.asarray(NP.sinh_tu_spec(spec, d), float)
    kq = MP.chay(d, v, cp, ma=MA, khung=KHUNG, don_bay=don_bay, gop="so_hoc")
    c = B._chi_so(kq)
    c["so_lenh"] = int(kq.so_lenh)
    return c, kq


def chay() -> None:
    df = DL.nap(MA, KHUNG)
    tr, ho = DL.hai_nua(df, 0.6)
    print("=" * 80)
    print("MO XE %s tren %s" % (TEN, MA))
    print("=" * 80)
    print("ca chuoi %d bar %s -> %s (%.1f nam)"
          % (len(df), df.index[0].date(), df.index[-1].date(),
             (df.index[-1] - df.index[0]).days / 365.25))

    # ---------------------------------------------------- 1. hinh dang lan can
    print("\n--- 1. HINH DANG VUNG LAN CAN (holdout, L=%.1f) ---" % L)
    print("Cot = nguong z, hang = cua so n. So la CAGR%/nam.")
    cps = _cp(ho)
    ns = [3, 4, 5, 6, 8, 10, 15, 20]
    ngs = [-0.5, -0.75, -1.0, -1.25, -1.5, -2.0]
    bang = {}
    print("  %-5s" % "n" + "".join("%9.2f" % g for g in ngs))
    for n in ns:
        hang = []
        for g in ngs:
            try:
                c, _ = do_mot(ho, spec_voi(n, g), cps)
                hang.append(c["cagr"])
            except Exception:
                hang.append(float("nan"))
        bang[n] = hang
        print("  %-5d" % n + "".join(
            ("%8.1f%%" % (x * 100)) if np.isfinite(x) else "       -" for x in hang))
    arr = np.array([bang[n] for n in ns], float)
    tot = np.nanmax(arr)
    o_duong = int(np.nansum(arr > 0))
    o_dat = int(np.nansum(arr >= CRT.MUC_CAGR))
    print("  o duong: %d/%d | o dat >=20%%/nam: %d/%d | tot nhat %.1f%%"
          % (o_duong, arr.size, o_dat, arr.size, tot * 100))
    print("  >> Cao nguyen (nhieu o lien nhau cung dat) hay cai gai (mot o)?")
    print("     Mot o duy nhat dat = con so ngau nhien, khong phai co che.")

    # -------------------------------------------------------- 2. ca chuoi dai
    print("\n--- 2. CA CHUOI 14,9 NAM (vuot tieu chi `song_du`) ---")
    goc = {c.get("ten"): c for c in NP.doc_kho()}[TEN]
    cpf = _cp(df)
    v = np.asarray(NP.sinh_tu_spec(goc, df), float)
    r = CRT.xet(df, v, cpf, ma=MA, khung=KHUNG)
    print("  verdict CONG RA TIEN: %s  truot: %s" % (r["verdict"], r["truot"]))
    h, bh = r["he"], r["mua_giu_cung_dd"]
    print("  he      : L=%.1f  CAGR %.2f%%  maxDD %.1f%%  Sharpe %.2f  "
          "Calmar %.2f  %d lenh"
          % (h["don_bay"], h["cagr"] * 100, h["maxdd"] * 100, h["sharpe"],
             h["calmar"], h["so_lenh"]))
    print("  mua-giu cung DD: L=%.2f  CAGR %.2f%%  Sharpe %.2f"
          % (bh["don_bay"] or 0, bh["cagr"] * 100, bh["sharpe"]))
    print("  cach biet: %+.2f diem %%/nam" % (r["cach_biet_cagr"] * 100))

    # ---------------------------------------------------------- 3. tung nam
    print("\n--- 3. TUNG NAM tren CA CHUOI ---")
    _, kq = do_mot(df, goc, cpf, don_bay=h["don_bay"])
    rr = pd.Series(np.expm1(np.nan_to_num(kq.loi)), index=df.index)
    Lbh = bh["don_bay"] or 1.0
    kb = MP.chay(df, np.ones(len(df)), cpf, ma=MA, khung=KHUNG,
                 don_bay=float(Lbh), gop="so_hoc")
    rb = pd.Series(np.expm1(np.nan_to_num(kb.loi)), index=df.index)
    thang = 0
    nam = sorted(set(df.index.year))
    for y in nam:
        a = (1 + rr[rr.index.year == y]).prod() - 1
        b = (1 + rb[rb.index.year == y]).prod() - 1
        thang += a > b
        print("  %d  he %+7.1f%%   B&H cungDD %+7.1f%%  %s"
              % (y, a * 100, b * 100, "HE THANG" if a > b else ""))
    print("  he thang %d/%d nam | he duong %d/%d nam"
          % (thang, len(nam),
             sum(1 for y in nam if (1 + rr[rr.index.year == y]).prod() > 1), len(nam)))

    # ------------------------------------------------------------ 4. placebo
    print("\n--- 4. PLACEBO (hoan vi KHOI VI THE, giu nguyen phoi nhiem) ---")
    try:
        p = CONG.placebo(df, kq, cpf)
        print("  " + json.dumps({k: (round(x, 4) if isinstance(x, float) else x)
                                 for k, x in p.items() if k != "chi_tiet"},
                                ensure_ascii=False)[:400])
    except Exception as e:
        print("  loi: %s: %s" % (type(e).__name__, str(e)[:120]))

    # ------------------------------------------- 5. co phai V6/IBS doi ten?
    print("\n--- 5. CO PHAI V6/IBS DOI TEN KHONG ---")
    ibs = ((df["close"] - df["low"]) / (df["high"] - df["low"]).replace(0, np.nan))
    v_ibs = (ibs < 0.2).astype(float).to_numpy()
    v_z = np.asarray(NP.sinh_tu_spec(goc, df), float)
    chung = float(np.mean((v_ibs > 0) & (v_z > 0)))
    rieng_z = float(np.mean((v_z > 0) & (v_ibs == 0)))
    rieng_ibs = float(np.mean((v_ibs > 0) & (v_z == 0)))
    tq = float(pd.Series(v_z).corr(pd.Series(v_ibs)))
    print("  ty le bar CO vi the: z5=%.3f  IBS<0,2=%.3f  ca hai=%.3f"
          % (v_z.mean(), v_ibs.mean(), chung))
    print("  tuong quan tin hieu: %.3f | rieng z5 %.3f | rieng IBS %.3f"
          % (tq, rieng_z, rieng_ibs))
    print("  >> Tuong quan cao = cung mot hien tuong (XAC NHAN V6, khong phai")
    print("     phat hien thu hai). Thap = hai co che khac nhau cung mot ho.")


if __name__ == "__main__":
    chay()
