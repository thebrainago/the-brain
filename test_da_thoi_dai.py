# -*- coding: utf-8 -*-
"""Bai kiem cho `nhan/da_thoi_dai.py` - chay mot co che tren MOI cua so sach.

Ly do module ton tai: SP500 D1 co 24.754 nen nhung he chi dung 3.404, vi duong
cat chi lay MOT cua so open-that roi con lay 40% lam holdout. Gop nhieu thoi
dai lai la cach lay lai suc thong ke da mat.

Cai phai chan la phep GOP. Sharpe gop theo trong so SO NEN, va sai so chuan
phai GIAM khi gop them thoi dai - do la ly do ky thuat duy nhat cua ca file.
Neu ai do doi sang trung binh khong trong so, cua so 5.000 nen se bi mot cua so
450 nen keo di ma khong ai thay.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import da_thoi_dai as DTD        # noqa: E402


class GopSharpe(unittest.TestCase):

    def test_gop_theo_trong_so_so_nen_chu_khong_phai_trung_binh_deu(self):
        muc = [{"sharpe": 1.0, "so_bar": 9000}, {"sharpe": 0.0, "so_bar": 1000}]
        r = DTD.gop_sharpe(muc)
        self.assertAlmostEqual(r["sharpe_gop"], 0.9, places=6,
                               msg="trung binh deu se ra 0,5 - cua so 1.000 nen "
                                   "khong duoc nang ngang cua so 9.000 nen")

    def test_sai_so_chuan_giam_khi_gop_them_thoi_dai(self):
        it = DTD.gop_sharpe([{"sharpe": 0.5, "so_bar": 1000}])
        nhieu = DTD.gop_sharpe([{"sharpe": 0.5, "so_bar": 1000}] * 4)
        self.assertLess(nhieu["sai_so_chuan"], it["sai_so_chuan"],
                        "gop them thoi dai phai lam sai so GIAM - do la ca ly do "
                        "ky thuat cua module nay")

    def test_dong_thuan_dem_so_thoi_dai_cung_dau(self):
        r = DTD.gop_sharpe([{"sharpe": 1.0, "so_bar": 100},
                            {"sharpe": 0.8, "so_bar": 100},
                            {"sharpe": -0.9, "so_bar": 100}])
        self.assertEqual(r["so_thoi_dai"], 3)
        self.assertEqual(r["cung_dau"], 2)
        self.assertAlmostEqual(r["dong_thuan"], 2 / 3, places=3)

    def test_mot_thoi_dai_duong_mot_am_gan_trieu_tieu_nhau(self):
        """Doi xung: hai thoi dai cung so nen, Sharpe doi dau -> gop ~ 0."""
        r = DTD.gop_sharpe([{"sharpe": 1.0, "so_bar": 500},
                            {"sharpe": -1.0, "so_bar": 500}])
        self.assertAlmostEqual(r["sharpe_gop"], 0.0, places=6)

    def test_bo_muc_thieu_sharpe_hoac_thieu_so_bar(self):
        r = DTD.gop_sharpe([{"sharpe": 1.0, "so_bar": 100},
                            {"sharpe": None, "so_bar": 100},
                            {"sharpe": 2.0, "so_bar": 0}])
        self.assertEqual(r["so_thoi_dai"], 1)
        self.assertAlmostEqual(r["sharpe_gop"], 1.0, places=6)

    def test_khong_co_muc_nao_thi_None_chu_khong_phai_0(self):
        """[[ket-luan-am-phai-phan-biet-chua-do]]: 0 doc thanh 'da do va bang
        khong', trong khi that ra la chua do duoc gi."""
        r = DTD.gop_sharpe([])
        self.assertIsNone(r["sharpe_gop"])
        self.assertEqual(r["so_bar"], 0)
        self.assertEqual(r["so_thoi_dai"], 0)

    def test_giu_sharpe_tung_thoi_dai_de_nguoi_doc_kiem_lai(self):
        r = DTD.gop_sharpe([{"sharpe": 1.0, "so_bar": 100},
                            {"sharpe": -0.5, "so_bar": 300}])
        self.assertEqual(r["sharpe_tung_thoi_dai"], [1.0, -0.5])


class SanBar(unittest.TestCase):

    def test_san_bar_du_lon_de_sharpe_co_nghia(self):
        self.assertGreaterEqual(DTD.SAN_BAR, 200,
                                "cua so qua ngan thi Sharpe la nhieu, khong phai do")

    def test_ma_khong_co_thi_NEM_LOI_chu_khong_im_lang_tra_rong(self):
        """`du_lieu.nap` nem `FileNotFoundError` kem danh sach ma co that.

        Ghi lai o day vi than `cac_cua_so_sach` co nhanh `if df is None` - doc
        vao de tuong no nuot loi va tra `[]`. Khong: mot ma go sai se DUNG day
        chuyen chu khong lang le thanh 'khong co thoi dai nao sach', va do la
        hanh vi dung ([[ket-luan-am-phai-phan-biet-chua-do]])."""
        with self.assertRaises(FileNotFoundError):
            DTD.cac_cua_so_sach("MA_KHONG_TON_TAI_XYZ")


if __name__ == "__main__":
    unittest.main()
