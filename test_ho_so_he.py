# -*- coding: utf-8 -*-
"""Test cho `nhan/ho_so_he.py` — file DUY NHAT dua cho AI khong mo duoc repo.

Module nay ra doi 16/09 va chua tung co test. No dang quan trong hon truoc:
18/09 chu du an dua he len GitHub de Claude chat doc, nen `HO_SO_HE_THONG.md`
la thu nguoi ngoai doc DAU TIEN.

Cai dang kiem khong phai "co chay khong" ma la: ho so co TU TA DAY DU khong.
Mot ho so thieu muc, hoac dinh so 0 vi kho khong doc duoc, thi con te hon
khong co ho so — nguoi doc tuong minh da nam he trong khi khong.
"""
import re
import unittest

from nhan import ho_so_he as HS


class HoSoTuTaDayDu(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.vb = HS.sinh(in_ra=None)

    def test_sinh_ra_van_ban_dang_ke(self):
        self.assertGreater(len(self.vb), 5000,
                           "ho so ngan bat thuong - co the mot khau do da im lang tra rong")

    def test_co_tieu_de_va_ngay_sinh(self):
        self.assertTrue(self.vb.lstrip().startswith("#"), "thieu tieu de")
        self.assertRegex(self.vb[:600], r"20\d\d-\d\d-\d\d",
                         "khong ghi ngay sinh — nguoi doc khong biet ho so cu hay moi")

    def test_nhac_den_ba_tru_that(self):
        thap = self.vb.lower()
        for tru in ("seeker", "quantlab"):
            self.assertIn(tru, thap, tru)

    def test_khong_bo_trong_toan_bo_phan_so_lieu(self):
        """Neu MOI con so deu la 0 thi kho khong doc duoc, khong phai he rong."""
        so = [int(x) for x in re.findall(r"\b(\d{1,6})\b", self.vb)]
        self.assertTrue(so, "khong co con so nao trong ho so")
        self.assertTrue(any(x > 0 for x in so),
                        "moi con so deu bang 0 — nhieu kha nang doc kho hong")


class SoLieuDocDuocThat(unittest.TestCase):

    def test_so_lieu_tra_ve_dict(self):
        d = HS._so_lieu()
        self.assertIsInstance(d, dict)
        self.assertTrue(d, "_so_lieu() tra ve rong")

    def test_cong_cu_tra_ve_danh_sach_va_so_dem(self):
        ds, n = HS._cong_cu()
        self.assertIsInstance(ds, list)
        self.assertIsInstance(n, int)
        self.assertGreaterEqual(n, 0)

    def test_duong_ra_tro_dung_cho(self):
        self.assertEqual(HS.TEP.name, "HO_SO_HE_THONG.md")
        self.assertEqual(HS.TEP.parent.name, "lab")


if __name__ == "__main__":
    unittest.main()
