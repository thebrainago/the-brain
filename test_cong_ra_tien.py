# -*- coding: utf-8 -*-
"""Bai kiem cho `nhan/cong_ra_tien.py` - CONG THU HAI.

Cong nay hoi "co ra tien tren tai khoan CUA TA khong", khac han `nhan/cong.py`
hoi "co phai phat hien that khong". Cho de sai nhat khong phai o nguong ma o
**cach so voi mua-giu**: phai so o CUNG SUT GIAM, chu khong phai so voi mua-giu
don le. Va o phep noi suy tim muc mua-giu do, module tu ghi mot luat quan trong:
*"khong ngoai suy - ngoai suy o day se bia ra mot doi thu manh gia"*.

Neu ai do bo luat khong-ngoai-suy, moi he don bay cao bong nhien "thang mua-giu"
vi doi thu duoc suy ra ngoai bang. Do la kieu that bai im lang, nen no co bai
kiem rieng o day.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import cong_ra_tien as CRT        # noqa: E402


def _bang(*cap) -> list[dict]:
    """(don_bay, maxdd, cagr) -> bang mua-giu nhu `bang_mua_giu` sinh ra."""
    return [{"don_bay": L, "maxdd": -dd, "cagr": g, "sharpe": 1.0, "chay": False}
            for L, dd, g in cap]


class SutGiam(unittest.TestCase):

    def test_duong_von_di_len_khong_co_sut_giam(self):
        self.assertAlmostEqual(CRT._dd(np.array([1.0, 2.0, 3.0])), 0.0, places=12)

    def test_giam_mot_nua_la_am_50_phan_tram(self):
        self.assertAlmostEqual(CRT._dd(np.array([100.0, 50.0, 60.0])), -0.5, places=12)

    def test_lay_sut_giam_SAU_dinh_moi(self):
        """Dinh dat lai thi sut giam do tu dinh MOI. [[sut-giam-dinh-dat-lai]]."""
        von = np.array([100.0, 80.0, 200.0, 150.0])
        self.assertAlmostEqual(CRT._dd(von), -0.25, places=12)


class TraKhopSutGiam(unittest.TestCase):

    def test_noi_suy_giua_hai_moc(self):
        b = _bang((1.0, 0.10, 0.05), (2.0, 0.20, 0.10))
        r = CRT.tra_khop_dd(b, -0.15)
        self.assertFalse(r["ngoai_bang"])
        self.assertAlmostEqual(r["don_bay"], 1.5, places=6)
        self.assertAlmostEqual(r["cagr"], 0.075, places=6)

    def test_KHONG_NGOAI_SUY_khi_he_sut_sau_hon_ca_bang(self):
        """Luat quan trong nhat cua file nay - xem docstring dau file."""
        b = _bang((1.0, 0.10, 0.05), (2.0, 0.20, 0.10))
        r = CRT.tra_khop_dd(b, -0.90)
        self.assertTrue(r["ngoai_bang"])
        self.assertAlmostEqual(r["cagr"], 0.10, places=6,
                               msg="phai lay moc CAO NHAT co that, khong duoc "
                                   "ngoai suy ra mot doi thu manh gia")
        self.assertLessEqual(r["don_bay"], 2.0)

    def test_he_sut_nong_hon_ca_bang_cung_khong_ngoai_suy(self):
        b = _bang((1.0, 0.10, 0.05), (2.0, 0.20, 0.10))
        r = CRT.tra_khop_dd(b, -0.01)
        self.assertTrue(r["ngoai_bang"])
        self.assertAlmostEqual(r["cagr"], 0.05, places=6)

    def test_bo_qua_muc_da_CHAY_tai_khoan(self):
        b = _bang((1.0, 0.10, 0.05), (2.0, 0.20, 0.10))
        b.append({"don_bay": 5.0, "maxdd": -0.99, "cagr": 9.99,
                  "sharpe": 3.0, "chay": True})
        r = CRT.tra_khop_dd(b, -0.95)
        self.assertLess(r["cagr"], 1.0, "muc da chay tai khoan khong duoc lam doi thu")

    def test_bang_toan_muc_chay_thi_khong_co_doi_thu(self):
        b = [{"don_bay": 5.0, "maxdd": -0.99, "cagr": 9.9, "sharpe": 3.0, "chay": True}]
        r = CRT.tra_khop_dd(b, -0.5)
        self.assertIsNone(r["don_bay"])
        self.assertTrue(r["ngoai_bang"])


class NguongLaThamSo(unittest.TestCase):
    """Nguong phai doc duoc va sua duoc tu ngoai - khong duoc chon cung trong
    than ham, vi ban ghi ket qua phai kem theo nguong da dung."""

    def test_nguong_mac_dinh_hop_ly(self):
        # 25/09 chu du an: "chi can co lai va maxdd duoi 80%" -> nguong duyet lai = 0
        # (dieu kien 1_lai la CAGR > 0 nghiem ngat), tran DD doc tu cham_diem.
        self.assertGreaterEqual(CRT.MUC_CAGR, 0.0)
        self.assertGreater(CRT.TRAN_DD, CRT.MUC_CAGR)
        self.assertLess(CRT.TRAN_DD, 1.0, "tran 100% = khong co tran")
        self.assertGreaterEqual(CRT.MIN_LENH, 1)
        self.assertGreater(CRT.MIN_NAM, 0.0)

    def test_luoi_don_bay_tang_dan_va_bat_dau_duoi_1(self):
        self.assertEqual(list(CRT.LUOI_BH), sorted(CRT.LUOI_BH))
        self.assertLess(CRT.LUOI_BH[0], 1.0,
                        "phai co muc duoi 1 de khop duoc he sut giam rat nong")
        self.assertIn(1.0, CRT.LUOI_BH)


if __name__ == "__main__":
    unittest.main()
