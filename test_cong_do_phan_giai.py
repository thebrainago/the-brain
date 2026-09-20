# -*- coding: utf-8 -*-
"""Cong khong duoc tu khoa lai bang mot p-value co SAN do phan giai.

Loi da xay ra that (the he cong 3, 15-21/08/2026):

    p_hop_thanh_fdr = max(p_alpha, p_placebo)

Placebo chay 199 hoan vi nen p nho nhat no CO THE tra la 1/200 = 0,005. Nguong
LORD giam theo 1/j^1.6 va tut duoi 0,005 tu phep thu thu 4. Ke tu do, khong gi
qua duoc cong nua - ke ca mot tin hieu do chinh xac 60% cho Sharpe 2,97 va alpha
+19,9%/nam. Toan bo 346 phan quyet FAIL cua the he 3 sinh ra tu day.

Bo test nay khoa ba thu: san phan giai duoc tinh dung, nguong LORD that su tut
duoi san do, va luat quyet dinh khong con dua p co san vao chuoi FDR.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import cong as CONG


class SanPhanGiai(unittest.TestCase):

    def test_san_p_placebo_dung_cong_thuc(self):
        self.assertAlmostEqual(CONG.san_p_placebo(199), 1 / 200)
        self.assertAlmostEqual(CONG.san_p_placebo(999), 1 / 1000)
        # n=0 khong duoc chia cho 0.
        self.assertAlmostEqual(CONG.san_p_placebo(0), 1.0)

    def test_nguong_lord_giam_theo_so_phep_thu(self):
        moc = [CONG.nguong_lord(j) for j in (1, 10, 100, 400)]
        self.assertEqual(moc, sorted(moc, reverse=True))
        self.assertLess(moc[-1], moc[0] / 100)

    def test_nguong_tut_duoi_san_rat_som(self):
        """Day la phep so sanh da lo ra loi. Giu no de khong ai quen."""
        san = CONG.san_p_placebo()
        j = next(j for j in range(1, 10_000) if CONG.nguong_lord(j) < san)
        self.assertLess(j, 20, "san phan giai va nguong FDR khong con va nhau "
                               "- doc lai truoc khi doi luat")


class LuatQuyetDinh(unittest.TestCase):

    def test_the_he_cong_da_tang_khi_doi_luat(self):
        """Doi luat quyet dinh PHAI mo chuoi FDR moi, khong dung chung the he cu."""
        self.assertGreaterEqual(CONG.THE_HE_CONG, 4)

    def test_khong_con_lay_max_voi_p_placebo(self):
        """Chan hoi quy: `max(p_alpha, p_placebo)` la chinh cai khoa cong."""
        import inspect
        nguon = inspect.getsource(CONG.xet)
        self.assertNotIn("max(p_alpha_hop_le, p_placebo_hop_le)", nguon)
        self.assertIn("p_hop_thanh_fdr = p_alpha_hop_le", nguon)

    def test_placebo_van_la_dieu_kien_bat_buoc(self):
        """Bo placebo khoi so hoc FDR KHONG duoc bien no thanh do trang tri."""
        import inspect
        nguon = inspect.getsource(CONG.xet)
        self.assertIn('dk["5_placebo"]', nguon)
        # Placebo truot thi suat FDR phai bi tieu voi p=1, khong duoc cap reject.
        self.assertIn('else 1.0', nguon)


class LordVanChanDuoc(unittest.TestCase):
    """Bai kiem LUC o muc so hoc: nguong phai chan p lon va cho qua p rat nho."""

    def test_p_lon_bi_chan_ngay_phep_thu_dau(self):
        self.assertGreater(0.05, CONG.nguong_lord(1))

    def test_p_du_nho_van_qua_duoc_o_phep_thu_thu_400(self):
        nguong = CONG.nguong_lord(400)
        self.assertGreater(nguong, 0.0)
        self.assertLess(1e-9, nguong, "nguong nho hon 1e-9 thi khong thong ke "
                                      "lien tuc nao voi toi - cong lai khoa cung")


class CheDoNghienCuu(unittest.TestCase):
    """Chuoi khong mua duoc van phai tra loi duoc cau 'co co che khong'.

    Truoc 21/08 khong tra loi duoc: chi phi `do_tin='KHAI'` lam dieu kien 7
    truot, ma dieu kien 7 la cong RE nen placebo KHONG chay, nen FDR nhan p=1 va
    dieu kien 5 lan 10 truot theo. Ba dieu kien truot deu tu MOT goc, va ket qua
    la 22 nam NIKKEI khong do duoc gi - ke ca voi tin hieu do chinh xac 85%
    (Sharpe 9,0).
    """

    def _chay(self, che_do, do_tin="KHAI"):
        from types import SimpleNamespace
        from unittest import mock
        import numpy as np
        import pandas as pd
        # 420 bar NGAY, va mot `df` THAT.
        #
        # Ban cu dung 200 bar va truyen `df=None`. Tu 20/09/2026 cong
        # `11_khong_an_khe_dao_ngay` khong con HONG THI MO: khong do duoc thi
        # verdict bi chan tran o `UNG_VIEN`. Voi `df=None` thi phep do nem, va
        # voi 200 bar ngay thi moi o THU chi co ~28 mau - duoi nguong 30 cua
        # `khe_gio_bat_thuong`, tuc van khong do duoc.
        #
        # Day la bai kiem LUC ("neu khong con duong nao ra PASS thi ca he vo
        # nghia"), nen no phai chay tren mot chuoi DO DUOC - neu khong no dang
        # do mot thu khac. 420 bar cho ~60 mau moi thu, va `open[i] =
        # close[i-1]` nen khe bang 0 o moi o: mot chuoi SACH that su.
        n = 420
        idx = pd.date_range("2020-01-01", periods=n, freq="D")
        gia = np.linspace(100.0, 120.0, n)
        df_sach = pd.DataFrame(
            {"open": np.r_[gia[0], gia[:-1]], "high": gia * 1.001,
             "low": gia * 0.999, "close": gia}, index=idx)
        kq = SimpleNamespace(so_lenh=n, loi=np.zeros(n), index=idx,
                             vi_the=np.ones(n), chi_phi_spread=0.0)
        so_sanh = {
            "he": {"tong_lai_pct": 50.0, "sharpe": 2.0, "calmar": 2.0,
                   "phoi_nhiem": 0.5, "so_bar": n},
            "mua_giu_net": {"tong_lai_pct": 5.0, "sharpe": 0.2, "calmar": 0.2},
            # t_alpha > 5 se cham luat "nghi nhin truoc" cua cong - dung 3,0
            "alpha_vs_mua_giu": {"t_alpha": 3.0, "alpha_nam_pct": 20.0},
        }
        pl = {"p_xau_nhat": 0.001, "null_hop_le": True, "bootstrap_hop_le": True}
        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh), \
                mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]), \
                mock.patch.object(CONG, "placebo", return_value=pl):
            return CONG.xet(df_sach, kq, SimpleNamespace(),
                            SimpleNamespace(do_tin=do_tin, canh_bao=None),
                            gt_ma=f"CHE_DO.{che_do}.{do_tin}", ho="test_che_do",
                            da_dang_ky=True, tren_holdout=True, che_do=che_do)

    def test_che_do_giao_dich_chan_chi_phi_khai_bao(self):
        ra = self._chay("giao_dich", "KHAI")
        self.assertFalse(ra["dieu_kien"]["7_chi_phi_do_duoc"])
        self.assertEqual(ra["verdict"], "FAIL")

    def test_che_do_nghien_cuu_tra_loi_duoc_cau_co_che(self):
        ra = self._chay("nghien_cuu", "KHAI")
        self.assertEqual(ra["verdict"], "CO_CO_CHE")
        self.assertNotIn("7_chi_phi_do_duoc", ra["dieu_kien"])
        self.assertTrue(ra["dieu_kien"]["5_placebo"], "placebo phai duoc chay")

    def test_che_do_nghien_cuu_KHONG_BAO_GIO_ra_PASS(self):
        """Bat bien quan trong nhat: chua ai chung minh thu nay giao dich duoc."""
        for do_tin in ("KHAI", "DO", "SAN"):
            with self.subTest(do_tin=do_tin):
                self.assertNotEqual(self._chay("nghien_cuu", do_tin)["verdict"], "PASS")

    def test_che_do_giao_dich_van_ra_PASS_duoc(self):
        """Bai kiem LUC: neu khong con duong nao ra PASS thi ca he vo nghia."""
        self.assertEqual(self._chay("giao_dich", "DO")["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
