# -*- coding: utf-8 -*-
"""Phep thu phan chung theo lop tai san.

Bai kiem hai chieu o day: mot co che that (chay o nhom da khai, hong o nhom doi
chung) phai duoc NHAN RA; va mot co che chay deu o moi lop phai bi TU CHOI la
KHONG_PHAN_BIET. Neu chi kiem chieu dau thi mot ham `return "CO_CO_CHE"` cung
xanh.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import chi_phi as CP
from nhan import ngu_phap as NP
from nhan import pham_vi as PV


def setUpModule():
    # Thu vien mau duoc nap tu kho DSL; khong nap thi moi ten mau deu "khong co".
    NP.nap_vao_mau()

#: Kho gia: 6 chi so, 6 FX, 6 vang - du de vuot TOI_THIEU_MOI_NHOM.
KHO_GIA = (["XM_US500CASH", "XM_US100CASH", "XM_US30CASH", "YH_DAX",
            "YH_NASDAQ", "ETF_SPY"] +
           ["EURUSD", "GBPUSD", "AUDCAD", "EURCAD", "NZDCAD", "USDCHF"] +
           ["XAUUSD", "XAUEURM", "XAUGBPM", "XAUAUDM", "XM_GOLD", "XM_SILVER"])


def _do_gia(theo_loai: dict, so_lenh: int = 100):
    """Sinh mot ham do gia: moi LOAI tai san tra ve mot Sharpe da dinh."""
    def do(ten_mau, ma, khung, tham_so):
        loai = PV.loai_cua(ma)
        if loai not in theo_loai:
            return None
        return {"tai_san": ma, "loai": loai, "so_lenh": so_lenh,
                "sharpe": theo_loai[loai], "tong_lai_pct": 10.0}
    return do


class PhanLoaiTaiSan(unittest.TestCase):
    """Nhom doi chung lan ETF/chi so vao thi ket luan hong tu goc."""

    def test_etf_va_chi_so_khong_bi_xep_nham_vao_fx(self):
        for ma in ("ETF_SPY", "ETF_QQQ", "YH_HANGSENG", "YH_FTSE100",
                   "YH_CAC40", "XM_US2000CASH"):
            self.assertEqual(CP._loai_tai_san(ma), "chi_so_my", ma)

    def test_kim_loai_khong_bi_xep_nham_vao_fx(self):
        for ma in ("XAUUSD", "XM_XAUEUR", "XM_SILVER", "XM_GOLD"):
            self.assertEqual(CP._loai_tai_san(ma), "vang", ma)

    def test_cap_tien_te_van_la_fx(self):
        for ma in ("EURUSD", "AUDCAD", "USDJPY", "NZDCAD", "EURCZK"):
            self.assertEqual(CP._loai_tai_san(ma), "fx", ma)

    def test_point_cua_bac_khac_point_cua_vang(self):
        """Bac ~19 USD/oz va vang ~2.000 USD/oz khong the cung mot point."""
        self.assertEqual(CP.point_cua("XM_SILVER", 18.8), 0.001)
        self.assertEqual(CP.point_cua("XAUUSD", 2000.0), 0.01)


class LayMauDaiDien(unittest.TestCase):

    def test_lay_trai_deu_khong_lay_dau_danh_sach(self):
        """171 cap FX sap theo ten thi 12 cai dau deu la AUD..."""
        fx = [f"AUD{x}" for x in ("CAD", "CHF", "DKK", "HKD", "JPY", "NZD")] + \
             ["EURUSD", "GBPUSD", "NZDCAD", "USDCHF", "USDJPY", "USDMXN"]
        lay = PV.tai_san_theo_loai(["fx"], tran=4, kho=fx)
        self.assertEqual(len(lay), 4)
        self.assertLess(sum(1 for m in lay if m.startswith("AUD")), 4,
                        f"chi lay toan AUD -> khong dai dien: {lay}")

    def test_it_hon_tran_thi_lay_het(self):
        self.assertEqual(len(PV.tai_san_theo_loai(["fx"], tran=99, kho=KHO_GIA)), 6)


class PhanXu(unittest.TestCase):

    def _chay(self, theo_loai, mau="rsi_dao_chieu"):
        return PV.kiem_pham_vi(mau, "H4", tran=6, kho=KHO_GIA,
                               do_ham=_do_gia(theo_loai))

    def test_co_che_that_duoc_nhan_ra(self):
        """Chay o nhom da khai, hong o nhom doi chung -> CO_CO_CHE."""
        ra = self._chay({"chi_so_my": 1.2, "fx": -0.3})
        self.assertEqual(ra["ket_luan"], "CO_CO_CHE")
        self.assertGreater(ra["cach_biet"], PV.CACH_BIET_TOI_THIEU)

    def test_chay_deu_moi_lop_bi_tu_choi(self):
        """BAI KIEM LUC nguoc: 'thang o dau cung' khong phai co che."""
        ra = self._chay({"chi_so_my": 0.9, "fx": 0.85})
        self.assertEqual(ra["ket_luan"], "KHONG_PHAN_BIET")
        self.assertIn("NEN HONG", ra["ly_do"])

    def test_chay_tot_hon_o_nhom_nen_hong_bi_tu_choi(self):
        ra = self._chay({"chi_so_my": 0.3, "fx": 0.9})
        self.assertEqual(ra["ket_luan"], "KHONG_PHAN_BIET")
        self.assertLess(ra["cach_biet"], 0)

    def test_am_o_nhom_hop_thi_khong_co_co_che(self):
        ra = self._chay({"chi_so_my": -0.5, "fx": -2.0})
        self.assertEqual(ra["ket_luan"], "KHONG_CO_CO_CHE")

    def test_thieu_mau_thi_noi_ro_chu_khong_ket_luan(self):
        ra = PV.kiem_pham_vi("rsi_dao_chieu", "H4", tran=6, kho=KHO_GIA,
                             do_ham=lambda *a: None)
        self.assertEqual(ra["ket_luan"], "CHUA_DU_MAU")
        self.assertNotIn("cach_biet", ra)

    def test_ho_khong_co_nhom_doi_chung_chi_ket_luan_mot_chieu(self):
        """`vi_mo` khai `khong_hop` rong -> phai noi ro la ket luan mot chieu."""
        ra = PV.kiem_pham_vi("bu_rui_ro_truoc_cong_bo_vi_mo", "H4", tran=6,
                             kho=KHO_GIA, do_ham=_do_gia({"fx": 0.8, "vang": 0.7}))
        self.assertIsNone(ra["cach_biet"])
        self.assertIn("mot chieu", ra["ly_do"])


class KhaiBao(unittest.TestCase):

    def test_moi_ho_trong_thu_vien_mau_deu_da_khai_pham_vi(self):
        from nhan import mau as MAU, ngu_phap as NP
        NP.nap_vao_mau()
        thieu = sorted({m.get("ho") for m in MAU.MAU.values()} - set(PV.PHAM_VI) - {None})
        self.assertEqual(thieu, [], f"ho chua khai pham vi: {thieu}")

    def test_moi_khai_bao_deu_co_ly_do_co_che(self):
        """Khai 'chay o day, hong o kia' ma khong noi VI SAO la doan mo."""
        for ho, khai in PV.PHAM_VI.items():
            self.assertTrue(khai.get("hop"), ho)
            self.assertGreater(len(khai.get("ly_do", "")), 60,
                               f"{ho}: ly_do qua ngan de goi la co che")

    def test_nhom_hop_va_nhom_doi_chung_khong_giao_nhau(self):
        for ho, khai in PV.PHAM_VI.items():
            self.assertEqual(set(khai["hop"]) & set(khai.get("khong_hop", [])), set(), ho)


if __name__ == "__main__":
    unittest.main(verbosity=2)
