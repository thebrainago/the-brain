# -*- coding: utf-8 -*-
"""CHUYEN HE DA PASS SANG TAI SAN MOI: GIU TY LE KICH HOAT, KHONG GIU CON SO.

`nhan/ngoai_sinh.py` (03/09/2026). Chu du an: *"NGOAI SINH la toan bo he thong
giao dich ma seeker dao ve + cac he thong DA PASS se duoc tinh chinh lai cho
he thong va tai san moi."*

VI SAO KHONG DUNG `quy_doi_tham_so`: ham do chi doi duoc tham so CO THU NGUYEN
GIA (SL 50 diem tren vang khac 50 diem tren EURUSD). Nhung tham so cua template
thuong la nguong dao dong va cua so nhin lai - `rsi_dao_chieu(n=14, vao=30)`.
`30` khong co thu nguyen gia nen khong nhan ty le ATR duoc.

Cai KHONG doi khi sang tai san khac la **DO HIEM cua su kien**. Do that
03/09/2026: PASS `AUDCAD.H4.rsi_dao_chieu {n:14,vao:30,ra_:55}` kich hoat
19,61% so bar; giu nguyen ba con so do tren US500CASH.H4 chi con 15,58%.
Phai chinh thanh {n:5,vao:12,ra_:77} moi ve lai 19,65%.
"""
from __future__ import annotations

import unittest

import numpy as np

from nhan import mau as MAU
from nhan import ngoai_sinh as NGS
from nhan import ngu_phap as NP


class HeDaPass(unittest.TestCase):
    def test_doc_duoc_trang_thai_ke_thua_tu_so_cai(self):
        he = NGS.he_da_pass()
        self.assertIsInstance(he, list)
        for g in he:
            self.assertIn(g["trang_thai"], NGS.TRANG_THAI_KE_THUA)
            self.assertIsInstance(g["tham_so"], dict, g["ma"])
            for k in ("ma", "template", "tai_san", "khung"):
                self.assertIn(k, g)

    def test_loc_theo_trang_thai_that_su_co_tac_dung(self):
        """Hieu chuan chieu nguoc: neu loc khong lam gi thi bai tren vo nghia."""
        chi_pass = NGS.he_da_pass(("PASS",))
        ca_hai = NGS.he_da_pass()
        self.assertLessEqual(len(chi_pass), len(ca_hai))
        for g in chi_pass:
            self.assertEqual(g["trang_thai"], "PASS")


class TyLeKichHoat(unittest.TestCase):
    def setUp(self):
        NP.nap_vao_mau()

    def test_do_duoc_tren_tai_san_that(self):
        t = NGS.ty_le_kich_hoat("US500CASH", "H4", "rsi_dao_chieu",
                                {"n": 14, "vao": 30, "ra_": 55})
        self.assertIsNotNone(t)
        self.assertTrue(0.0 < t < 1.0)

    def test_tai_san_khong_co_thi_tra_None_chu_khong_tra_0(self):
        """Ket luan am phai phan biet 'do duoc va bang 0' voi 'chua do duoc'."""
        self.assertIsNone(
            NGS.ty_le_kich_hoat("KHONG_CO_MA_NAY", "H4", "rsi_dao_chieu", {}))

    def test_template_khong_chay_duoc_tren_khung_thi_tra_None(self):
        """Co che theo PHIEN tren khung khong co gio -> None, khong phai 0."""
        self.assertIsNone(
            NGS.ty_le_kich_hoat("US500CASH", "D1", "mua_qua_dem",
                                {"gio_vao": 20, "gio_ra": 14}))

    def test_do_tren_TRAIN_khac_do_tren_ca_chuoi(self):
        a = NGS.ty_le_kich_hoat("US500CASH", "H4", "ibs_bat_day",
                                {"nguong": 0.2, "giu": 1}, chi_train=True)
        b = NGS.ty_le_kich_hoat("US500CASH", "H4", "ibs_bat_day",
                                {"nguong": 0.2, "giu": 1}, chi_train=False)
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertNotAlmostEqual(a, b, places=6)


class Chuyen(unittest.TestCase):
    def setUp(self):
        NP.nap_vao_mau()
        self.gt = {"ma": "AUDCAD.H4.rsi_dao_chieu.n14_vao30_ra_55",
                   "template": "rsi_dao_chieu",
                   "tham_so": {"n": 14, "vao": 30, "ra_": 55},
                   "tai_san": "AUDCAD", "khung": "H4",
                   "ho": "quay_ve_trung_binh", "trang_thai": "PASS"}

    def test_chuyen_lam_ty_le_GAN_HON_so_voi_giu_nguyen_con_so(self):
        """Day la toan bo ly do file `ngoai_sinh` ton tai."""
        r = NGS.chuyen(self.gt, "US500CASH", "H4")
        self.assertIsNotNone(r)
        goc = r["ty_le_goc"]
        giu = r["ty_le_neu_giu_nguyen_so"]
        moi = r["ty_le_moi"]
        self.assertIsNotNone(giu)
        self.assertLessEqual(abs(np.log(moi / goc)), abs(np.log(giu / goc)) + 1e-9,
                             "chinh lai phai khong te hon giu nguyen con so")

    def test_tra_du_ca_hai_ben_de_nguoi_doc_doi_chieu(self):
        r = NGS.chuyen(self.gt, "US500CASH", "H4")
        for k in ("tu", "template", "tai_san_goc", "tham_so_goc", "ty_le_goc",
                  "tai_san_dich", "tham_so_moi", "ty_le_moi",
                  "ty_le_neu_giu_nguyen_so", "lech_log", "dat"):
            self.assertIn(k, r)

    def test_template_khong_co_trong_MAU_thi_tra_None(self):
        gt = dict(self.gt, template="khong_he_ton_tai")
        self.assertIsNone(NGS.chuyen(gt, "US500CASH", "H4"))

    def test_tai_san_dich_khong_chay_duoc_thi_tra_None(self):
        gt = dict(self.gt, template="mua_qua_dem",
                  tham_so={"gio_vao": 20, "gio_ra": 14})
        self.assertIsNone(NGS.chuyen(gt, "US500CASH", "D1"))

    def test_tham_so_moi_van_chay_duoc_that_tren_tai_san_dich(self):
        """Chinh xong ma khong chay duoc thi la chinh hong."""
        r = NGS.chuyen(self.gt, "US500CASH", "H4")
        t = NGS.ty_le_kich_hoat("US500CASH", "H4", r["template"], r["tham_so_moi"])
        self.assertIsNotNone(t)
        self.assertAlmostEqual(t, r["ty_le_moi"], places=4)

    def test_dat_la_co_theo_dung_sai_chu_khong_phai_phan_quyet(self):
        r = NGS.chuyen(self.gt, "US500CASH", "H4", dung_sai=1e-9)
        self.assertFalse(r["dat"], "dung sai sat 0 thi gan nhu khong bao gio dat")
        r2 = NGS.chuyen(self.gt, "US500CASH", "H4", dung_sai=10.0)
        self.assertTrue(r2["dat"])


class UngVien(unittest.TestCase):
    def test_tach_ro_hai_nguon_khong_tron_lam_mot(self):
        """Kho SEEKER va he DA PASS co do tin cay rat khac nhau."""
        r = NGS.ung_vien("US500CASH", "H4", gom_kho=False)
        self.assertEqual(r["tu_kho_seeker"], 0)
        self.assertIn("ke_thua", r)
        self.assertEqual(r["tai_san"], "US500CASH")

    def test_gom_kho_thi_dem_ca_kho_SEEKER(self):
        r = NGS.ung_vien("US500CASH", "H4", gom_kho=True)
        self.assertGreater(r["tu_kho_seeker"], 100)


if __name__ == "__main__":
    unittest.main()
