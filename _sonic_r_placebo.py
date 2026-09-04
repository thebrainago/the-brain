# -*- coding: utf-8 -*-
"""SONIC R: PLACEBO - phep thu re nhat va quyet dinh nhat, va no CHUA tung chay.

TINH TRANG TRUOC KHI CO FILE NAY (do 04/09/2026):
  - `gia_thuyet` trong so cai: **0 ban ghi nao co ten sonic**. Chua dang ky.
  - `_sonic_r_kiem_chung.py` co train/holdout va quet lan can TP/SL, nhung
    **khong mot dong placebo nao**.
  - Con so duoc nhac lai nhieu lan: 26,01%/nam o don bay 3, Calmar holdout
    0,47 -> 1,50.

MOT CANH BAO PHAI NOI TRUOC KHI DOC BAT KY SO NAO O DUOI.

Cau hinh TP 5% / SL 1% **duoc chon sau khi da nhin holdout**: `kiem_chung`
quet mot luoi 5x3 tham so TREN HOLDOUT roi bao "cao nguyen hay cai gai". Do la
mot viec hop ly de LAM QUEN voi be mat, nhung ke tu luc do **holdout khong con
la holdout** cho cau hinh nay - no da tham gia vao viec chon tham so.

Nen: moi con so "holdout" cua Sonic R tu truoc den nay phai doc nhu con so
TRONG MAU. Muon co mot phep thu ngoai mau that thi phai dang ky truoc
(`plan_hash`) roi cham vao mot doan du lieu CHUA AI NHIN. File nay khong lam
viec do - no chi tra loi mot cau re hon va den truoc:

    Tin hieu nay co khac gi mot tin hieu ngau nhien co cung hinh dang khong?

Neu cau tra loi la KHONG thi khong can ban them ve holdout, don bay, hay EA.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from _sonic_r_tpsl import tin_hieu_sonic_r    # noqa: E402
from nhan import chi_phi as CP                # noqa: E402
from nhan import cong as CONG                 # noqa: E402
from nhan import du_lieu as DU                # noqa: E402
from nhan import mo_phong as MP               # noqa: E402

MA, KHUNG = "US500CASH", "H4"
TP, SL = 0.05, 0.01


def _chay(d, cp):
    th = tin_hieu_sonic_r(d)
    return MP.chay_tpsl(d, th, TP, SL, cp, gio_toi_da=0, ma=MA, khung=KHUNG)


def main() -> int:
    df = DU.nap(MA, KHUNG)
    cp = CP.tu_du_lieu(MA, df)
    cp = cp[0] if isinstance(cp, tuple) else cp
    tr, ho = DU.hai_nua(df, 0.6)

    print(f"=== SONIC R PLACEBO — {MA} {KHUNG}, TP {TP*100:.0f}% / SL {SL*100:.0f}% ===")
    print(f"    {len(df)} bar, {df.index[0].date()} -> {df.index[-1].date()}")
    print(f"    nguong san p: {CONG.san_p_placebo():.4f}\n")

    print(f"  {'doan':<10}{'lenh':>6}{'loi gop':>10}{'p placebo':>12}  ket luan")
    xau = 0.0
    for nhan, d in (("TRAIN", tr), ("HOLDOUT", ho), ("CA CHUOI", df)):
        kq = _chay(d, cp)
        p = CONG.placebo(d, kq, cp)
        pv = p.get("p") if isinstance(p, dict) else p
        so_lenh = int(np.nansum(np.abs(np.diff(np.r_[0.0, kq.vi_the])) > 0))
        loi = float(np.nansum(kq.loi))
        dat = (pv is not None) and pv <= CONG.san_p_placebo()
        xau = max(xau, pv or 1.0)
        print(f"  {nhan:<10}{so_lenh:>6}{loi:>10.3f}{(pv if pv is not None else float('nan')):>12.4f}"
              f"  {'DAT' if dat else 'TRUOT'}")
        if isinstance(p, dict) and p.get("chi_tiet"):
            print(f"             {str(p['chi_tiet'])[:110]}")

    print(f"\n  p XAU NHAT tren ba doan: {xau:.4f}")
    print("  Ghi nho: cau hinh nay da duoc chon SAU khi nhin holdout, nen cot")
    print("  HOLDOUT o tren khong phai mot phep thu ngoai mau that.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
