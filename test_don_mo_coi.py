# -*- coding: utf-8 -*-
"""Kiem `nhan/don_mo_coi.py` - bo don tien trinh mo coi.

## Chuyen da xay ra 12/09/2026

Phong may ban quet nang bang `nohup ... &`. Tien trinh cha thoat nhung
`multiprocessing.Pool` de lai 24 worker, va Pool **SINH LAI** worker khi con
chet - nen giet con khong giai quyet duoc gi. Do duoc: 20 tien trinh x 85-92%
= **1.951% CPU (19,5/20 loi)** trong hon 20 phut.

Hau qua that khong phai "may cham": `qwen` do CPU truoc khi phong viec, thay
100% thi tu choi phong - **dung thiet ke**. He nam im, bang viec day, nhat ky
chi lap lai `con -1.0 loi` moi hai phut. Tren VPS chay nhieu thang khong nguoi
truc thi do la he tu te liet ma khong ai biet.

## Hai tinh chat phai giu

**1. KHONG GIET NHAM cay dieu phoi.** `qwen.chay`, `day_viec.py`, `dieu_phoi.py`
va con chau cua chung phai duoc mien. Giet nham chinh bo dieu phoi thi bo don
tro thanh thu gay ra su co no sinh ra de chua.

**2. GIET CA CAY, khong giet la.** Pool sinh lai worker sau vai giay.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import don_mo_coi as DMC  # noqa: E402


class QuetKhongDuocNEM(unittest.TestCase):
    def test_quet_tra_ve_dict_du_khoa(self):
        k = DMC.quet()
        if k.get("loi"):
            self.skipTest(k["loi"])
        for m in ("mien", "mo_coi", "cpu_mo_coi"):
            self.assertIn(m, k)
        self.assertIsInstance(k["mo_coi"], list)

    def test_tien_trinh_CUA_CHINH_PHIEN_NAY_duoc_mien(self):
        """Bo don ma giet chinh no thi khong con gi de noi."""
        k = DMC.quet(tuoi_toi_thieu=0.0)
        if k.get("loi"):
            self.skipTest(k["loi"])
        self.assertNotIn(os.getpid(), [m["pid"] for m in k["mo_coi"]])


class PhaiGIET_CA_CAY(unittest.TestCase):
    def test_goc_cay_lay_CHA_khi_cha_cung_mo_coi(self):
        """Pool sinh lai worker sau vai giay, nen phai giet tu GOC."""
        mo_coi = [{"pid": 101, "ppid": 100}, {"pid": 102, "ppid": 100},
                  {"pid": 100, "ppid": 99}]
        self.assertEqual(DMC._goc_cay(mo_coi), [99],
                         "khong lan len toi goc -> Pool se sinh lai worker")

    def test_cha_khong_mo_coi_thi_lay_chinh_cha_lam_goc(self):
        mo_coi = [{"pid": 201, "ppid": 200}, {"pid": 202, "ppid": 200}]
        self.assertEqual(DMC._goc_cay(mo_coi), [200])

    def test_moi_cay_mot_goc_khong_trung(self):
        mo_coi = [{"pid": 1, "ppid": 10}, {"pid": 2, "ppid": 10},
                  {"pid": 3, "ppid": 20}]
        self.assertEqual(DMC._goc_cay(mo_coi), [10, 20])


class CauHinhPhaiHOP_LY(unittest.TestCase):
    def test_co_nguong_tuoi_de_khong_giet_viec_vua_phong(self):
        self.assertGreaterEqual(DMC.TUOI_TOI_THIEU, 60.0)

    def test_dieu_phoi_co_du_ba_bo_lap_lich(self):
        for t in ("qwen.chay", "day_viec.py", "dieu_phoi.py"):
            self.assertIn(t, DMC.DIEU_PHOI)


class EvoPhaiTHAY_DUOC(unittest.TestCase):
    def test_evo_co_chi_so_mo_coi(self):
        from nhan import evo as EVO
        ten = {c["ten"] for c in EVO.suc_khoe_may()}
        self.assertIn("may.mo_coi", ten)

    def test_chi_so_mo_coi_co_cat_nghia(self):
        from nhan import evo as EVO
        self.assertIn("may.mo_coi", EVO.CAT_NGHIA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
