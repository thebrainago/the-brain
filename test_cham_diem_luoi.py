# -*- coding: utf-8 -*-
"""`cham_diem.tu_ket_qua_luoi` - ban tien cho ket qua `mo_phong_v2`.

LOI TIM RA 19/09/2026. Ban cu tinh:

    sut_giam_pct = 100.0 * von_can / max(von_can, 1e-9)

tuc LUON BANG 100, tren moi dau vao. Hau qua: moi cau hinh luoi deu dinh
"sut giam 100% > tran 60%" va bi ha mot bac, voi mot LY DO BIA RA. Mot he lai
25%/nam tren von da tinh du dem cung bi cham la MONG.

Vi sao khong ai bat duoc: `cham_diem` la module MO COI - chinh docstring cua
no ghi vay - nen duong nay chua tung chay that lan nao. Mot cong khong ai di
qua thi khong ai biet no hong.
"""
from __future__ import annotations

import unittest

from nhan import cham_diem as CD


class SutGiamPhaiDO_TU_KET_QUA(unittest.TestCase):

    def _r(self, lai=500.0, von_dd=1000.0, ro=120.0):
        """Dang ket qua cua `mo_phong_v2.mo_phong`: `von` la sut giam sau nhat."""
        return {"lai_nam": lai, "ro_nam": ro, "von": von_dd}

    def test_KHONG_con_luon_bang_100(self):
        d = CD.tu_ket_qua_luoi(self._r(), von_can=2000.0, so_nam=5.0)
        self.assertNotEqual(d["sut_giam_pct"], 100.0,
                            "sut giam van la hang so - cong dang bia ly do")

    def test_sut_giam_la_TY_LE_sut_tren_von_bo_ra(self):
        """Bo ra 2.000 de om mot cu sut 1.000 thi sut giam la 50% von."""
        d = CD.tu_ket_qua_luoi(self._r(von_dd=1000.0), von_can=2000.0, so_nam=5.0)
        self.assertAlmostEqual(d["sut_giam_pct"], 50.0, places=6)

    def test_bo_dem_cang_day_thi_sut_giam_tren_von_cang_thap(self):
        it = CD.tu_ket_qua_luoi(self._r(), von_can=1000.0, so_nam=5.0)
        nhieu = CD.tu_ket_qua_luoi(self._r(), von_can=4000.0, so_nam=5.0)
        self.assertGreater(it["sut_giam_pct"], nhieu["sut_giam_pct"])

    def test_he_lai_tot_khong_con_bi_ha_bac_vi_ly_do_bia(self):
        d = CD.tu_ket_qua_luoi(self._r(lai=500.0, von_dd=1000.0),
                               von_can=2000.0, so_nam=5.0)
        self.assertFalse([x for x in d["ly_do"] if "sut giam" in x], d["ly_do"])

    def test_VAN_chan_khi_sut_giam_that_su_qua_tran(self):
        """Hieu chuan chieu nguoc: sua xong ma cong khong con chan gi thi no
        chi la mot cong bi tat, khong phai mot cong da sua."""
        d = CD.tu_ket_qua_luoi(self._r(von_dd=1900.0), von_can=2000.0, so_nam=5.0)
        self.assertTrue([x for x in d["ly_do"] if "sut giam" in x], d["ly_do"])

    def test_thieu_von_trong_ket_qua_thi_KHONG_doan(self):
        """Khong co `von` trong ket qua -> khong suy duoc sut giam. Bia mot con
        so o day la bia ca mot phan quyet."""
        d = CD.tu_ket_qua_luoi({"lai_nam": 500.0, "ro_nam": 120.0},
                               von_can=2000.0, so_nam=5.0)
        self.assertTrue([x for x in d["ly_do"] if "CHUA_DO_DUOC" in x
                         or "khong do duoc" in x], d["ly_do"])
