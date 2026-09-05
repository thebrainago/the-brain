# -*- coding: utf-8 -*-
"""cham_diem.py - BANG DIEM THUC TE. Ra tien bao nhieu, rui ro the nao.

Chu du an 05/09/2026: *"Bo cham diem hay lam thuc te va noi vao trong tam: ra
tien lai bao nhieu, rui ro the nao, dung vong veo hoc thuat nua"*.

## SAU CON SO, KHONG HON

  `lai_pct_nam`   Lai mot nam tren VON PHAI BO RA. Von phai bo ra = max(sut giam
                  sau nhat, ky quy dinh) - khong phai so du danh nghia.
  `sut_giam_pct`  Sut giam sau nhat tren duong von. Cai nay quyet dinh co gong
                  duoc khong.
  `von_can`       Bao nhieu tien moi chay duoc cau hinh nay. Kem ban CENT
                  (chia 100) vi do la vung von that su cua chu du an.
  `hoi_von_thang` Bao nhieu THANG thi lai cong don bang von bo ra. Tra loi
                  "bao lau thi tien ve", khong phai "Sharpe bao nhieu".
  `so_lenh_nam`   It qua thi khong phai he thong; nhieu qua thi phi an het.
  `nguy_co_chay`  Ty le duong chay bi stop-out. Voi lop khong cat lo day la
                  con so DUY NHAT co nghia.

## BA MUC PHAN QUYET - dat theo NGUONG CHU DU AN, khong theo thong ke

  `CHAY_DUOC`  lai >= 20%/nam · sut giam <= 60% · >= 20 lenh/nam · khong chay
  `MONG`       co lai nhung khong dat mot trong cac nguong tren
  `BO`         lo, hoac chay tai khoan

## KHONG CO O DAY, VA CO Y

Sharpe, Calmar, p-value, FDR. Chung thuoc `nhan/cong.py` - noi tra loi "co that
khong". Bang nay tra loi "co dang chay khong". Mot cau hinh CHAY_DUOC ma chua
qua `cong.py` thi goi dung ten: **canh bac co ky vong duong do duoc**, chua phai
phat hien. Truong `da_qua_cong_that` ghi ro dieu do.
"""
from __future__ import annotations

import numpy as np

#: Nguong cua chu du an, dat 04-05/09. Doi o day, khong rai rac trong script.
MUC_LAI = 20.0          # %/nam tren von phai bo ra
TRAN_SUT_GIAM = 60.0    # %
MIN_LENH_NAM = 20.0
CENT = 100.0            # 1 USD chuan = 100 USD cent


def cham(lai_nam: float, von_can: float, sut_giam_pct: float,
         so_lenh_nam: float, so_nam: float, chay: bool = False,
         nguy_co_chay: float | None = None, ky_quy_dinh: float = 0.0,
         da_qua_cong_that: bool = False, ten: str = "") -> dict:
    """Mot cau hinh -> bang diem thuc te. Tat ca don vi tien la CUNG mot dong.

    `von_can` truyen vao thuong la sut giam sau nhat; ham tu nang len neu ky
    quy dinh con lon hon - vi tai khoan chet o cai lon hon trong hai.
    """
    von = max(float(von_can), float(ky_quy_dinh), 1e-9)
    lai_pct = lai_nam / von * 100.0
    hoi_von = (von / lai_nam * 12.0) if lai_nam > 0 else None

    ly_do = []
    if chay:
        ly_do.append("CHAY TAI KHOAN")
    if lai_nam <= 0:
        ly_do.append("khong co lai")
    if lai_pct < MUC_LAI:
        ly_do.append("lai %.1f%%/nam < muc %.0f%%" % (lai_pct, MUC_LAI))
    if abs(sut_giam_pct) > TRAN_SUT_GIAM:
        ly_do.append("sut giam %.0f%% > tran %.0f%%" % (abs(sut_giam_pct),
                                                        TRAN_SUT_GIAM))
    if so_lenh_nam < MIN_LENH_NAM:
        ly_do.append("chi %.1f lenh/nam - khong phai he thong" % so_lenh_nam)

    if chay or lai_nam <= 0:
        muc = "BO"
    elif not ly_do:
        muc = "CHAY_DUOC"
    else:
        muc = "MONG"

    return {
        "ten": ten, "muc": muc, "ly_do": ly_do,
        "lai_pct_nam": round(lai_pct, 2),
        "lai_tien_nam": round(lai_nam, 1),
        "von_can": round(von, 1),
        "von_can_cent": round(von / CENT, 2),
        "sut_giam_pct": round(abs(sut_giam_pct), 1),
        "hoi_von_thang": (round(hoi_von, 1) if hoi_von else None),
        "so_lenh_nam": round(so_lenh_nam, 1),
        "so_nam_do": round(so_nam, 1),
        "nguy_co_chay_pct": (None if nguy_co_chay is None
                             else round(nguy_co_chay * 100, 1)),
        "da_qua_cong_that": bool(da_qua_cong_that),
    }


def tu_ket_qua_luoi(r: dict, von_can: float, so_nam: float, **kw) -> dict:
    """Ban tien cho ket qua cua `mo_phong_v2.mo_phong`."""
    return cham(lai_nam=r.get("lai_nam", 0.0), von_can=von_can,
                sut_giam_pct=100.0 * von_can / max(von_can, 1e-9),
                so_lenh_nam=r.get("ro_nam", 0.0), so_nam=so_nam, **kw)


def bang(cac_diem: list[dict], in_ra=print, tran: int = 25) -> None:
    """In bang diem, xep theo LAI, khong theo Sharpe."""
    d = [x for x in cac_diem if x]
    d.sort(key=lambda x: -(x["lai_pct_nam"] if x["muc"] != "BO" else -1e9))
    in_ra("%-38s %-11s %9s %9s %11s %9s %8s"
          % ("cau hinh", "muc", "lai %/nam", "sut giam", "von can $",
             "cent $", "hoi von"))
    for x in d[:tran]:
        in_ra("%-38s %-11s %8.1f%% %8.1f%% %11.0f %9.2f %7s"
              % (str(x["ten"])[:38], x["muc"], x["lai_pct_nam"],
                 x["sut_giam_pct"], x["von_can"], x["von_can_cent"],
                 ("%.0f th" % x["hoi_von_thang"]) if x["hoi_von_thang"] else "-"))
    n = sum(1 for x in d if x["muc"] == "CHAY_DUOC")
    in_ra("")
    in_ra("CHAY_DUOC: %d | MONG: %d | BO: %d"
          % (n, sum(1 for x in d if x["muc"] == "MONG"),
             sum(1 for x in d if x["muc"] == "BO")))
    chua = [x for x in d if x["muc"] == "CHAY_DUOC" and not x["da_qua_cong_that"]]
    if chua:
        in_ra("%d cau hinh CHAY_DUOC chua qua cong that -> goi la 'canh bac co "
              "ky vong duong do duoc', chua phai phat hien." % len(chua))
