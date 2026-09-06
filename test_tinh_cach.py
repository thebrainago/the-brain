# -*- coding: utf-8 -*-
"""Bai kiem cho `nhan/tinh_cach.py` - thuoc do tinh cach tai san.

Cai phai chan o day KHONG phai "Hurst tinh dung cong thuc khong". Module tu no
da ghi ro dieu quan trong: uoc luong Hurst tren chuoi tai chinh **lech len tren**
co he thong (157/157 ma deu > 0,5), nen **gia tri tuyet doi vo nghia, chi XEP
HANG moi co gia tri**. Vi vay bai kiem nay do dung cai do: chuoi xu huong phai
xep TREN chuoi hoi quy, tren moi thuoc do da khai la du bao duoc.

Neu ai do sau nay "sua" Hurst cho no ra dung 0,5 tren nhieu buoc ngau nhien,
cac bai kiem duoi day van xanh - va do la co y: dieu du an dung la thu tu, khong
phai con so.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import tinh_cach as TC        # noqa: E402


def _buoc_ngau_nhien(n=4000, hat=1):
    r = np.random.default_rng(hat).normal(0, 0.01, n)
    return 100.0 * np.exp(np.cumsum(r))


def _xu_huong(n=4000, hat=2, keo=0.6):
    """Buoc ngau nhien + thanh phan CO NHO duong (loi suat tu tuong quan +)."""
    g = np.random.default_rng(hat)
    r = np.zeros(n)
    e = g.normal(0, 0.01, n)
    for i in range(1, n):
        r[i] = keo * r[i - 1] + e[i]
    return 100.0 * np.exp(np.cumsum(r))


def _hoi_quy(n=4000, hat=3, keo=-0.4):
    """Loi suat tu tuong quan AM: len roi xuong, dien hinh cua quay ve TB."""
    g = np.random.default_rng(hat)
    r = np.zeros(n)
    e = g.normal(0, 0.01, n)
    for i in range(1, n):
        r[i] = keo * r[i - 1] + e[i]
    return 100.0 * np.exp(np.cumsum(r))


class ThuocDoXepHangDung(unittest.TestCase):
    """Thu tu, khong phai gia tri tuyet doi - xem docstring dau file."""

    @classmethod
    def setUpClass(cls):
        cls.xh = _xu_huong()
        cls.hq = _hoi_quy()
        cls.nn = _buoc_ngau_nhien()

    def test_hurst_xep_xu_huong_tren_hoi_quy(self):
        h_xh, h_hq = TC.hurst(self.xh), TC.hurst(self.hq)
        self.assertIsNotNone(h_xh)
        self.assertIsNotNone(h_hq)
        self.assertGreater(h_xh, h_hq,
                           f"Hurst phai xep xu huong tren hoi quy: {h_xh} vs {h_hq}")

    def test_ty_so_hieu_qua_xep_xu_huong_tren_hoi_quy(self):
        e_xh, e_hq = TC.ty_so_hieu_qua(self.xh), TC.ty_so_hieu_qua(self.hq)
        self.assertIsNotNone(e_xh)
        self.assertIsNotNone(e_hq)
        self.assertGreater(e_xh, e_hq, f"ER: {e_xh} vs {e_hq}")

    def test_tu_tuong_quan_bat_dung_dau(self):
        """ac1 khong du bao duoc ket qua that (do 05/09), nhung no phai do
        DUNG cai no noi la do - neu khong thi ca ho so sai."""
        self.assertGreater(TC.tu_tuong_quan(self.xh, 1), 0.0)
        self.assertLess(TC.tu_tuong_quan(self.hq, 1), 0.0)

    def test_vr10_xep_dung_thu_tu(self):
        a = TC.ty_so_phuong_sai(self.xh, 10)
        b = TC.ty_so_phuong_sai(self.hq, 10)
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertGreater(a[0], b[0], f"VR(10): {a[0]} vs {b[0]}")


class ChuoiQuaNganTraNone(unittest.TestCase):
    """[[ket-luan-am-phai-phan-biet-chua-do]]: khong do duoc phai la None,
    khong duoc la 0 - 0 se bi doc thanh 'da do va bang khong'."""

    def test_hurst_chuoi_ngan(self):
        self.assertIsNone(TC.hurst(np.linspace(100, 110, 50)))

    def test_nua_doi_chuoi_ngan(self):
        self.assertIsNone(TC.nua_doi(np.array([100.0, 101.0, 102.0])))

    def test_ho_so_du_khoa_ke_ca_khi_khong_do_duoc(self):
        h = TC.ho_so(np.array([100.0, 101.0, 100.5]))
        for k in ("hurst", "vr2", "vr10", "ac1", "nua_doi_bar", "er"):
            self.assertIn(k, h, f"ho_so thieu khoa '{k}'")


class NhanBoPhieuTrenBaThuocDo(unittest.TestCase):

    def test_ba_phieu_duong_thanh_xu_huong(self):
        lo_h, hi_h = TC.NGUONG["hurst"]
        lo_v, hi_v = TC.NGUONG["vr10"]
        lo_e, hi_e = TC.NGUONG["er"]
        self.assertEqual(
            TC.nhan({"hurst": hi_h + 0.01, "vr10": hi_v + 0.01, "er": hi_e + 0.01}),
            "XU_HUONG")

    def test_ba_phieu_am_thanh_hoi_quy(self):
        lo_h, _ = TC.NGUONG["hurst"]
        lo_v, _ = TC.NGUONG["vr10"]
        lo_e, _ = TC.NGUONG["er"]
        self.assertEqual(
            TC.nhan({"hurst": lo_h - 0.01, "vr10": lo_v - 0.01, "er": lo_e - 0.01}),
            "HOI_QUY")

    def test_mot_phieu_khong_du_de_ket_luan(self):
        _, hi_h = TC.NGUONG["hurst"]
        self.assertEqual(TC.nhan({"hurst": hi_h + 0.01}), "TRUNG_TINH")

    def test_thieu_het_thi_trung_tinh_chu_khong_no(self):
        self.assertEqual(TC.nhan({}), "TRUNG_TINH")
        self.assertEqual(TC.nhan({"hurst": None, "vr10": float("nan")}), "TRUNG_TINH")

    def test_khong_dung_vr2_va_ac1_de_bo_phieu(self):
        """Module khai ro: chi hurst/vr10/er duoc bo phieu, vi vr2 va ac1 do
        CUNG mot thu voi vr10 - dem chung la dem mot bang chung ba lan."""
        _, hi_h = TC.NGUONG["hurst"]
        chi_vr2_va_ac1 = {"hurst": hi_h + 0.01, "vr2": 9.0, "ac1": 0.9}
        self.assertEqual(TC.nhan(chi_vr2_va_ac1), "TRUNG_TINH",
                         "vr2/ac1 khong duoc tinh phieu")


if __name__ == "__main__":
    unittest.main()
