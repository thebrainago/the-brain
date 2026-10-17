# -*- coding: utf-8 -*-
"""Che do cong "loi_nhuan" (17/10/2026): CHI ba yeu to cot loi cua chu du an.

  "chi can tim ra mot he co lai sau khi tru di phi va cac muc gian, sut giam khong qua 80%
   va loi nhuan tren 10% mot nam ... bo het nhung cai do di"

Hieu chuan HAI CHIEU: he dat cot loi phai qua du thua mua-giu / placebo / alpha / phi khai bao;
he lo, he lai qua mong so voi sut giam, he an khe gia dao ngay thi phai truot.
"""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd

from nhan import cong as CONG, so as SO


class CongLoiNhuan(unittest.TestCase):
    def setUp(self):
        self._db_cu = SO.DB
        self._tmp = tempfile.TemporaryDirectory()
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()

    def _xet(self, cagr, dd, tong=None, do_tin="KHAI", che_do="giao_dich", p_placebo=0.9, bh_tot=True):
        idx = pd.date_range("2020-01-01", periods=200, freq="D")
        kq = SimpleNamespace(so_lenh=6, loi=np.zeros(200), index=idx, vi_the=np.ones(200))
        bh = {"tong_lai_pct": 300.0, "sharpe": 3.0, "calmar": 3.0} if bh_tot else {"tong_lai_pct": 1.0, "sharpe": 0.1, "calmar": 0.1}
        so_sanh = {"he": {"tong_lai_pct": cagr * 5 if tong is None else tong, "cagr_pct": cagr, "max_dd_pct": -abs(dd),
                          "sharpe": 0.3, "calmar": 0.1, "phoi_nhiem": 0.5, "so_bar": 200},
                   "mua_giu_net": bh, "alpha_vs_mua_giu": {"t_alpha": 0.2, "alpha_nam_pct": -1.0}}
        pl = {"p_xau_nhat": p_placebo, "null_hop_le": True, "bootstrap_hop_le": True}
        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh), \
                mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]), \
                mock.patch.object(CONG, "che_do_cong", return_value="loi_nhuan"), \
                mock.patch.object(CONG, "placebo", return_value=pl):
            return CONG.xet(None, kq, SimpleNamespace(), SimpleNamespace(do_tin=do_tin, canh_bao=None),
                            da_dang_ky=False, tren_holdout=True, che_do=che_do, ghi_so=False,
                            economic_plan_hash="plan-loi-nhuan-%s-%s" % (cagr, dd), lane="candidate_validation",
                            family="test_loi_nhuan", data_release="test", decision_generation=CONG.THE_HE_CONG)

    def test_he_dat_cot_loi_qua_du_thua_mua_giu_placebo_va_phi_khai_bao(self):
        ra = self._xet(cagr=5.0, dd=30.0)        # 5/30 = 0,167 >= 10/80 -> lot x2 cho 10%/nam, DD ~60%
        self.assertEqual(ra["verdict"], "PASS")
        self.assertTrue(ra["dieu_kien"]["15_lai_10_sut_giam_80"])
        self.assertFalse(ra["dieu_kien"]["1_loi_hon_mua_giu"])
        self.assertFalse(ra["dieu_kien"]["7_chi_phi_do_duoc"])
        self.assertTrue(any("lot x2.00" in x for x in ra["ly_do"]))
        self.assertTrue(any("KHAI BAO" in x for x in ra["nhan"]))

    def test_lai_mong_so_voi_sut_giam_thi_truot(self):
        ra = self._xet(cagr=5.0, dd=50.0)        # 5/50 = 0,10 < 0,125: lot nao cung khong ra 10%/nam voi DD <= 80%
        self.assertEqual(ra["verdict"], "FAIL")
        self.assertFalse(ra["dieu_kien"]["15_lai_10_sut_giam_80"])

    def test_sut_giam_qua_80_van_dat_neu_giam_lot_duoc(self):
        ra = self._xet(cagr=40.0, dd=120.0)      # giam lot x0,67 -> DD 80%, lai ~27%/nam
        self.assertTrue(ra["dieu_kien"]["15_lai_10_sut_giam_80"])

    def test_lo_thi_truot(self):
        ra = self._xet(cagr=-2.0, dd=30.0, tong=-10.0)
        self.assertEqual(ra["verdict"], "FAIL")
        self.assertFalse(ra["dieu_kien"]["14_lai_rong_duong"])

    def test_chuoi_nghien_cuu_van_la_ung_vien(self):
        ra = self._xet(cagr=12.0, dd=50.0, che_do="nghien_cuu")
        self.assertEqual(ra["verdict"], "UNG_VIEN")

    def test_an_khe_gia_dao_ngay_van_chan_phi_khai_bao_thi_khong(self):
        # do khe gia can du lieu that (DL.khe_gio_bat_thuong); o day kiem cach XEP LOAI
        self.assertIn("11_khong_an_khe_dao_ngay", CONG.CHAN_LOI_NHUAN)
        self.assertNotIn("7_chi_phi_do_duoc", CONG.CHAN_LOI_NHUAN)


if __name__ == "__main__":
    unittest.main(verbosity=2)
