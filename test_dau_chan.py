# -*- coding: utf-8 -*-
"""Bai kiem cho `nhan/dau_chan.py` - luan nguoc kieu danh tu dau chan cong khai.

Hai thu phai chan:

1. **Thieu du lieu tra `None`, khong tra 0.** Day la ho benh da sap nhieu lan
   ([[ket-luan-am-phai-phan-biet-chua-do]]): mot `0` o `nhoi_khi_lo` doc y het
   "da do va khong nhoi", trong khi that ra la "chua do duoc". Sai o day thi ca
   bang phan loai kieu danh bi lech ma khong ai thay.

2. **`phan_loai` phai xet theo THU TU khai bao.** Mot dau chan vua nhoi khi lo
   vua giu lau la `luoi_dca`, khong phai `xu_huong` - va thu tu la thu quyet
   dinh dieu do.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import dau_chan as DC        # noqa: E402

MOC = 1_700_000_000


class BacTai(unittest.TestCase):
    """`_bac_tai` = trung vi so BUOC TANG tai trong mot doan giu lien tuc."""

    def test_vao_mot_phat_roi_giu_la_mot_buoc(self):
        tai = np.array([0.0, 0.10, 0.10, 0.10, 0.0])
        self.assertEqual(DC._bac_tai(tai), 1.0)

    def test_nhoi_bon_lan_la_bon_buoc(self):
        tai = np.array([0.0, 0.10, 0.20, 0.40, 0.80, 0.0])
        self.assertEqual(DC._bac_tai(tai), 4.0)

    def test_nhich_duoi_5_phan_tram_khong_tinh_la_buoc(self):
        """Chi dem buoc tang DANG KE, de nhieu lam tron khong bi dem thanh nhoi."""
        tai = np.array([0.0, 0.100, 0.102, 0.103, 0.104, 0.0])
        self.assertEqual(DC._bac_tai(tai), 1.0)

    def test_khong_co_vi_the_nao_tra_None(self):
        self.assertIsNone(DC._bac_tai(np.zeros(10)))


class ThieuDuLieuTraNone(unittest.TestCase):

    def test_khong_co_gi_thi_moi_dac_trung_deu_None(self):
        d = DC.dac_trung(None, None, None)
        for k, v in d.items():
            self.assertIsNone(v, f"'{k}' phai la None khi khong co du lieu, nhan {v!r}")

    def test_it_lenh_khong_tinh_lech_trai(self):
        """Duoi 30 lenh thi do lech khong co nghia - phai la None."""
        d = DC.dac_trung(None, None, np.array([0.01] * 29))
        self.assertIsNone(d["lech_trai"])

    def test_du_lenh_thi_co_lech_trai(self):
        r = np.concatenate([np.full(59, 0.01), [-2.0]])   # duoi trai day
        d = DC.dac_trung(None, None, r)
        self.assertIsNotNone(d["lech_trai"])
        self.assertLess(d["lech_trai"], 0.0, "chuoi co mot lenh lo rat nang phai lech TRAI")

    def test_von_cho_lo_treo_dinh_va_so_ngay_song(self):
        n = 40
        ts = MOC + np.arange(n) * 86400.0
        bal = np.full(n, 1000.0)
        eq = bal.copy()
        eq[20] = 800.0                      # mot luc lo treo 20%
        von = np.column_stack([ts, bal, eq])
        d = DC.dac_trung(von, None, None)
        self.assertAlmostEqual(d["lo_treo_dinh"], 0.2, places=6)
        self.assertAlmostEqual(d["song_ngay"], n - 1, places=6)


class PhanLoaiTheoThuTu(unittest.TestCase):

    def test_luoi_dca(self):
        kieu, ly = DC.phan_loai({"nhoi_khi_lo": 0.8, "bac_tai": 4.0,
                                 "lo_treo_dinh": 0.35, "thang_pct": 88.0,
                                 "cat_sach": 0.5, "giu_phut": 5000.0})
        self.assertEqual(kieu, "luoi_dca", ly)

    def test_giu_lau_ma_co_nhoi_van_la_luoi_dca_khong_phai_xu_huong(self):
        """Thu tu xet la thu phan xu: nhoi khi lo thang truoc 'giu lau'."""
        kieu, _ = DC.phan_loai({"nhoi_khi_lo": 0.9, "bac_tai": 5.0,
                                "lo_treo_dinh": 0.5, "thang_pct": 95.0,
                                "cat_sach": 0.4, "giu_phut": 99999.0})
        self.assertEqual(kieu, "luoi_dca")

    def test_gong_lo_la_giu_lo_ma_khong_nhoi(self):
        kieu, _ = DC.phan_loai({"nhoi_khi_lo": 0.0, "bac_tai": 1.0,
                                "lo_treo_dinh": 0.4, "thang_pct": 90.0,
                                "cat_sach": 1.8, "giu_phut": 3000.0})
        self.assertEqual(kieu, "gong_lo")

    def test_scalp(self):
        kieu, _ = DC.phan_loai({"nhoi_khi_lo": 0.0, "bac_tai": 1.0,
                                "lo_treo_dinh": 0.01, "thang_pct": 55.0,
                                "cat_sach": 0.8, "giu_phut": 30.0})
        self.assertEqual(kieu, "scalp")

    def test_xu_huong(self):
        kieu, _ = DC.phan_loai({"nhoi_khi_lo": 0.0, "bac_tai": 1.0,
                                "lo_treo_dinh": 0.02, "thang_pct": 40.0,
                                "cat_sach": 0.9, "giu_phut": 5000.0})
        self.assertEqual(kieu, "xu_huong")

    def test_thieu_du_lieu_thi_khong_ro_VA_NOI_RO_THIEU_GI(self):
        kieu, ly = DC.phan_loai({})
        self.assertEqual(kieu, "khong_ro")
        self.assertIn("thieu:", ly, "phai noi ro thieu dac trung nao, "
                                    "khong duoc chi bao 'khong ro'")

    def test_moi_kieu_tra_ve_deu_nam_trong_KIEU(self):
        for d in ({}, {"nhoi_khi_lo": 0.9, "bac_tai": 3.0, "lo_treo_dinh": 0.3,
                       "thang_pct": 90.0, "cat_sach": 0.5, "giu_phut": 10.0}):
            self.assertIn(DC.phan_loai(d)[0], DC.KIEU)


if __name__ == "__main__":
    unittest.main()
