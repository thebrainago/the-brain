# -*- coding: utf-8 -*-
"""Test cong FDR ban 2."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd

from nhan import cong as CONG, so as SO


class TestFdrV2(unittest.TestCase):
    def setUp(self):
        self._db_cu = SO.DB
        self._tmp = tempfile.TemporaryDirectory()
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()

    @staticmethod
    def _epoch_kw(**doi):
        kw = {
            "lane": "candidate_validation",
            "family": "mean_reversion",
            "data_release": "sp500_h1_2026-08-16_v1",
            "decision_generation": CONG.THE_HE_CONG,
        }
        kw.update(doi)
        return kw

    def test_epoch_khai_bao_ro_va_khong_co_reset_theo_quy(self):
        epoch = CONG.tao_epoch_fdr(**self._epoch_kw())
        self.assertEqual(
            epoch,
            "fdr-v2|lane=candidate_validation|family=mean_reversion|"
            "data_release=sp500_h1_2026-08-16_v1|"
            f"decision_generation={CONG.THE_HE_CONG}")
        self.assertNotIn(CONG.ky_hien_tai(), epoch)
        self.assertNotIn("Q", CONG.ho_fdr("mean_reversion"))

    def test_duplicate_plan_tra_quyet_dinh_dau_khong_sua_so(self):
        dau = CONG.lord_v2(0.001, "economic-plan-A", **self._epoch_kw())
        lai = CONG.lord_v2(0.99, "economic-plan-A", **self._epoch_kw())

        self.assertFalse(dau["duplicate"])
        self.assertTrue(lai["duplicate"])
        self.assertEqual(lai["fdr_id"], dau["fdr_id"])
        self.assertEqual(lai["bac_bo"], dau["bac_bo"])
        self.assertEqual(lai["p_su_dung"], 0.001)
        self.assertEqual(lai["p_de_nghi_lan_nay"], 0.99)
        self.assertTrue(lai["p_khac_lan_dau"])
        self.assertEqual(SO.mot("SELECT COUNT(*) n FROM fdr")["n"], 1)
        self.assertEqual(SO.mot("SELECT p FROM fdr")["p"], 0.001)

    def test_hai_ma_legacy_cung_plan_hash_chi_tieu_mot_suat(self):
        plan_hash = "a" * 40
        for ma in ("GT.A", "GT.B"):
            SO.chay(
                "INSERT INTO gia_thuyet(ma,plan_hash,dang_ky_luc) VALUES(?,?,?)",
                ma, plan_hash, SO.bay_gio())

        dau = CONG.lord(0.01, "mean_reversion", "GT.A")
        lai = CONG.lord(0.90, "mean_reversion", "GT.B")

        self.assertFalse(dau["duplicate"])
        self.assertTrue(lai["duplicate"])
        self.assertEqual(dau["economic_plan_hash"], plan_hash)
        self.assertEqual(lai["economic_plan_hash"], plan_hash)
        self.assertEqual(SO.mot("SELECT COUNT(*) n FROM fdr")["n"], 1)

    def test_p_khong_hop_le_duoc_ghi_bao_thu_bang_mot(self):
        ra = CONG.lord_v2(float("nan"), "economic-plan-bad-p", **self._epoch_kw())
        self.assertEqual(ra["p_su_dung"], 1.0)
        self.assertTrue(ra["p_da_thay_bang_1"])
        self.assertFalse(ra["bac_bo"])
        self.assertEqual(SO.mot("SELECT p FROM fdr")["p"], 1.0)

    def test_plan_cham_holdout_truot_cong_re_van_tieu_mot_suat(self):
        idx = pd.date_range("2026-01-01", periods=10, freq="h")
        kq_he = SimpleNamespace(
            so_lenh=0, loi=np.zeros(10), index=idx, vi_the=np.zeros(10))
        kq_bh = SimpleNamespace()
        cp = SimpleNamespace(do_tin="KHAI", canh_bao="chi phi chua do")
        so_sanh = {
            "he": {
                "tong_lai_pct": -1.0, "sharpe": -1.0, "calmar": -1.0,
                "phoi_nhiem": 0.0, "so_bar": 10,
            },
            "mua_giu_net": {
                "tong_lai_pct": 0.0, "sharpe": 0.0, "calmar": 0.0,
            },
            "alpha_vs_mua_giu": {"t_alpha": None, "alpha_nam_pct": None},
        }

        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh), \
                mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]), \
                mock.patch.object(CONG, "placebo",
                                  side_effect=AssertionError("khong duoc chay placebo")):
            ra = CONG.xet(
                None, kq_he, kq_bh, cp, da_dang_ky=True, tren_holdout=True,
                economic_plan_hash="economic-plan-fail-cheap",
                **self._epoch_kw())

        self.assertEqual(ra["verdict"], "FAIL")
        self.assertFalse(ra["da_chay_placebo"])
        self.assertEqual(ra["p_hop_thanh_fdr"], 1.0)
        self.assertEqual(ra["fdr"]["p_su_dung"], 1.0)
        self.assertEqual(SO.mot("SELECT COUNT(*) n FROM fdr")["n"], 1)

    def test_chuoi_fdr_chi_nhan_p_alpha_lien_tuc(self):
        idx = pd.date_range("2026-01-01", periods=100, freq="h")
        # loi DUONG nho chu khong phai 0 (sua 25/09/2026): tu TANG 2 KINH TE (18/09)
        # mot "he" loi 0 co rr thuc te = 0 -> truot re -> placebo khong chay -> FDR
        # nhan p=1, va bai nay khong con kiem duoc cai no muon kiem (so hoc FDR).
        kq_he = SimpleNamespace(
            so_lenh=100, loi=np.full(100, 1e-4), index=idx, vi_the=np.ones(100))
        kq_bh = SimpleNamespace()
        cp = SimpleNamespace(do_tin="DO", canh_bao=None)
        so_sanh = {
            "he": {
                "tong_lai_pct": 10.0, "sharpe": 1.0, "calmar": 1.0,
                "phoi_nhiem": 0.5, "so_bar": 100,
            },
            "mua_giu_net": {
                "tong_lai_pct": 1.0, "sharpe": 0.1, "calmar": 0.1,
            },
            "alpha_vs_mua_giu": {"t_alpha": 3.0, "alpha_nam_pct": 5.0},
        }
        placebo = {
            "p_xau_nhat": 0.04, "null_hop_le": True,
            "bootstrap_hop_le": True,
        }

        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh), \
                mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]), \
                mock.patch.object(CONG, "placebo", return_value=placebo):
            ra = CONG.xet(
                None, kq_he, kq_bh, cp, da_dang_ky=True, tren_holdout=True,
                economic_plan_hash="economic-plan-composite",
                **self._epoch_kw())

        # LUAT MOI (the he 4). Truoc day cho nay lay p XAU HON:
        #     p_hop_thanh = max(p_alpha, p_placebo) = 0,04
        # p_placebo co SAN 1/(n_boot+1) = 0,005, trong khi nguong LORD tut duoi
        # 0,005 tu phep thu thu 4 -> cong tu khoa cung lai vinh vien. Chuoi FDR
        # gio chi nhan p_alpha (thong ke lien tuc, xuong duoc tuy y sau).
        # `p_alpha` trong bao cao da lam tron 5 chu so; FDR dung ban day du.
        self.assertLess(ra["p_alpha"], 0.04)
        self.assertAlmostEqual(ra["p_hop_thanh_fdr"], ra["p_alpha"], places=5)
        self.assertAlmostEqual(ra["fdr"]["p_su_dung"], ra["p_alpha"], places=5)
        self.assertLess(ra["p_hop_thanh_fdr"], 0.005,
                        "p dua vao FDR phai xuong duoi duoc san cua placebo")
        # Placebo van la dieu kien bat buoc, khong bi bo.
        self.assertTrue(ra["dieu_kien"]["5_placebo"])

    def test_placebo_truot_thi_tieu_suat_voi_p_bang_1(self):
        """Bo placebo khoi so hoc FDR khong duoc bien no thanh do trang tri."""
        idx = pd.date_range("2026-01-01", periods=100, freq="h")
        # loi DUONG nho chu khong phai 0 (sua 25/09/2026): tu TANG 2 KINH TE (18/09)
        # mot "he" loi 0 co rr thuc te = 0 -> truot re -> placebo khong chay -> FDR
        # nhan p=1, va bai nay khong con kiem duoc cai no muon kiem (so hoc FDR).
        kq_he = SimpleNamespace(
            so_lenh=100, loi=np.full(100, 1e-4), index=idx, vi_the=np.ones(100))
        so_sanh = {
            "he": {"tong_lai_pct": 10.0, "sharpe": 1.0, "calmar": 1.0,
                   "phoi_nhiem": 0.5, "so_bar": 100},
            "mua_giu_net": {"tong_lai_pct": 1.0, "sharpe": 0.1, "calmar": 0.1},
            "alpha_vs_mua_giu": {"t_alpha": 3.0, "alpha_nam_pct": 5.0},
        }
        placebo_truot = {"p_xau_nhat": 0.80, "null_hop_le": True,
                         "bootstrap_hop_le": True}
        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh),                 mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]),                 mock.patch.object(CONG, "placebo", return_value=placebo_truot):
            ra = CONG.xet(
                None, kq_he, SimpleNamespace(), SimpleNamespace(do_tin="DO", canh_bao=None),
                da_dang_ky=True, tren_holdout=True,
                economic_plan_hash="economic-plan-placebo-truot",
                **self._epoch_kw())
        self.assertFalse(ra["dieu_kien"]["5_placebo"])
        self.assertEqual(ra["p_hop_thanh_fdr"], 1.0)
        # Tu 12/09/2026 placebo la NHAN CANH BAO chu khong chan (che do "nhan",
        # `config/nguong.json`). Nen cai phai kiem la: no VAN tieu mot suat FDR
        # voi p=1, VAN hien ra thanh nhan, va ban doc cu VAN tra FAIL.
        self.assertIn("placebo yeu - co the la ngau nhien", ra["nhan"])
        self.assertEqual(ra["verdict_chan"], "FAIL")
        self.assertEqual(ra["verdict"], "PASS")

    def test_che_do_CHAN_van_tra_FAIL_khi_placebo_truot(self):
        """Duong quay lai phai con: dat che_do_cong='chan' la ve y nguyen ban cu."""
        idx = pd.date_range("2026-01-01", periods=100, freq="h")
        # loi DUONG nho chu khong phai 0 (sua 25/09/2026): tu TANG 2 KINH TE (18/09)
        # mot "he" loi 0 co rr thuc te = 0 -> truot re -> placebo khong chay -> FDR
        # nhan p=1, va bai nay khong con kiem duoc cai no muon kiem (so hoc FDR).
        kq_he = SimpleNamespace(
            so_lenh=100, loi=np.full(100, 1e-4), index=idx, vi_the=np.ones(100))
        so_sanh = {
            "he": {"tong_lai_pct": 10.0, "sharpe": 1.0, "calmar": 1.0,
                   "phoi_nhiem": 0.5, "so_bar": 100},
            "mua_giu_net": {"tong_lai_pct": 1.0, "sharpe": 0.1, "calmar": 0.1},
            "alpha_vs_mua_giu": {"t_alpha": 3.0, "alpha_nam_pct": 5.0},
        }
        placebo_truot = {"p_xau_nhat": 0.80, "null_hop_le": True,
                         "bootstrap_hop_le": True}
        with mock.patch.object(CONG.DO, "so_sanh", return_value=so_sanh),                 mock.patch.object(CONG.DO, "hieu_qua_giai_doan", return_value=[]),                 mock.patch.object(CONG, "placebo", return_value=placebo_truot),                 mock.patch.object(CONG, "che_do_cong", return_value="chan"):
            ra = CONG.xet(
                None, kq_he, SimpleNamespace(), SimpleNamespace(do_tin="DO", canh_bao=None),
                da_dang_ky=True, tren_holdout=True,
                economic_plan_hash="economic-plan-placebo-chan",
                **self._epoch_kw())
        self.assertEqual(ra["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
