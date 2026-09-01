# -*- coding: utf-8 -*-
"""Test cho `nhan/do_im_lang.py` - bo do tim tang dang cam.

Module nay sinh ra de bat "so 0 doc duoc thanh cau tra loi". Neu chinh no mac
loi do thi no thanh cai te nhat trong he: mot bo do bao "khong sao" mai mai.
Nen test o day danh dung vao cho do.
"""
from __future__ import annotations

import unittest

from nhan import do_im_lang as DIL


class BaTrangThaiKhongDuocGOP(unittest.TestCase):
    """CAM / NGHI / CHAY phai tach nhau. Gop lai la mat toan bo tac dung."""

    def test_co_vao_khong_ra_la_CAM(self):
        d = DIL.do_mot_tang("thu", "SELECT 999 n", "SELECT 0 n", 50)
        self.assertEqual(d["trang_thai"], "CAM")

    def test_khong_co_vao_la_NGHI_chu_khong_phai_CAM(self):
        """Kho con moi thi dau ra 0 la BINH THUONG, bao dong se thanh nhieu."""
        d = DIL.do_mot_tang("thu", "SELECT 3 n", "SELECT 0 n", 50)
        self.assertEqual(d["trang_thai"], "NGHI")

    def test_co_vao_co_ra_la_CHAY(self):
        d = DIL.do_mot_tang("thu", "SELECT 999 n", "SELECT 7 n", 50)
        self.assertEqual(d["trang_thai"], "CHAY")
        self.assertAlmostEqual(d["ty_le"], 7 / 999, places=4)


class KhongDoDuocKhacKhongCoGi(unittest.TestCase):
    """Cai bay goc: mot cau truy van HONG tra 0 va bi doc thanh 'tang nay cam'."""

    def test_truy_van_hong_ra_KHONG_DO_DUOC_chu_khong_ra_0(self):
        d = DIL.do_mot_tang("thu", "SELECT * FROM bang_khong_ton_tai", "SELECT 1 n", 0)
        self.assertEqual(d["trang_thai"], "KHONG_DO_DUOC")
        self.assertIsNone(d["vao"])

    def test_dem_tra_None_chu_khong_tra_0(self):
        self.assertIsNone(DIL._dem("SELECT * FROM bang_khong_ton_tai"))

    def test_dem_lay_GIA_TRI_chu_khong_lay_TEN_COT(self):
        """`SO.mot` tra dict; `list(r)[0]` se lay ten cot - da sap that 01/09."""
        self.assertEqual(DIL._dem("SELECT 42 n"), 42)


class NguonCamPhaiNoiVISAO(unittest.TestCase):
    """Bao 'cam' ma khong noi vi sao thi van phai ngoi truy tay - chua xong viec."""

    def test_moi_nguon_cam_deu_co_ly_do_va_viec_phai_lam(self):
        for r in DIL.nguon_cam():
            self.assertIn("vi_sao", r, r)
            self.assertTrue(r.get("lam_gi"), r)

    def test_tra_ca_HAI_kho_nguon_cua_seeker(self):
        """SEEKER co `NGUON` va `NGUON_TRINH_DUYET`; tra mot kho la ket luan nham
        'khong ai lay' cho 25 nguon doc qua trinh duyet."""
        from tru import seeker as S
        for ma in list(S.NGUON)[:3] + list(S.NGUON_TRINH_DUYET)[:3]:
            self.assertTrue(DIL._co_nguoi_lay(ma), ma)

    def test_khong_ai_lay_nhan_dung_ma_bia(self):
        self.assertFalse(DIL._co_nguoi_lay("nguon_khong_ton_tai_xyz"))


class QuetChayDuoc(unittest.TestCase):
    def test_quet_tra_du_khoa(self):
        q = DIL.quet()
        self.assertEqual(len(q["tang"]), len(DIL.TANG))
        for k in ("cam", "khong_do_duoc", "so_cam", "so_hong"):
            self.assertIn(k, q)

    def test_khong_tang_nao_KHONG_DO_DUOC_tren_so_that(self):
        """Mot cau truy van hong trong TANG = bo do mu mot mat ma khong ai biet."""
        self.assertEqual(DIL.quet()["khong_do_duoc"], [])

    def test_bao_cao_ra_chu(self):
        self.assertIn("Do im lang", DIL.bao_cao())


if __name__ == "__main__":
    unittest.main()
