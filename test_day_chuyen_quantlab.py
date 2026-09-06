# -*- coding: utf-8 -*-
"""Bai kiem cho `nhan/day_chuyen_quantlab.py` - quy trinh 5 buoc da chuan hoa.

Module nay chu yeu la DIEU HUONG: no goi `quan_tri`, `ho_so_symbol`,
`cham_diem`. Nen bai kiem o day khong lap lai bai kiem cua cac module do, ma
chan hai thu rieng cua no:

1. **`_luong` phai chua lai nhan.** Luat trong `lab/CLAUDE.md`: khi chay 16
   tien trinh quet, `mt5.initialize()` het 60 giay roi bao IPC timeout - va cai
   do hien ra nhu mot cong TU CHOI PASS, tuc mot ket luan am gia. Mac dinh phai
   la `so_nhan - 4`.

2. **Bon buoc phai goi duoc DOC LAP.** `chay()` noi ca bon, nhung buoc 4 nhan
   ho so tu ngoai vao duoc - neu khong thi khong ai thu duoc mot buoc rieng ma
   khong chay lai ca day chuyen (buoc 3 mat 92 giay).
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import day_chuyen_quantlab as DCQ        # noqa: E402


class ChuaLaiNhan(unittest.TestCase):

    def test_mac_dinh_chua_4_nhan(self):
        self.assertEqual(DCQ._luong(), max(1, (os.cpu_count() or 8) - 4))

    def test_khong_bao_gio_tra_0_hoac_am(self):
        """May it nhan ma tra 0 thi pool nem ngay luc khoi tao."""
        self.assertGreaterEqual(DCQ._luong(chua=9999), 1)

    def test_chua_it_hon_thi_duoc_nhieu_luong_hon(self):
        self.assertGreaterEqual(DCQ._luong(chua=0), DCQ._luong(chua=4))


class BuocGoiDocLapDuoc(unittest.TestCase):

    def test_buoc4_nhan_ho_so_tu_ngoai_khong_phai_doc_dia(self):
        """Truyen ho so vao thang -> khong cham `ho_so_symbol.doc()`."""
        hs = [{"ma": "EURUSD", "hurst": 0.55, "nhan_tinh_cach": "HOI_QUY",
               "spread_bps": 1.6, "chi_phi_do_tin": "SAN", "so_nam": 20.0,
               "atr_pct_bar": 0.6, "vong_quay_toi_da": 500.0}]
        g = DCQ.buoc4_ghep(hs, {}, kieu="hoi_quy", in_ra=lambda *a: None)
        self.assertEqual([h["ma"] for h in g["ung_vien"]], ["EURUSD"])
        self.assertIn("kho_gia_tri", g)

    def test_buoc4_khong_co_ung_vien_thi_tra_rong_chu_khong_no(self):
        hs = [{"ma": "X", "hurst": 0.55, "nhan_tinh_cach": "HOI_QUY",
               "spread_bps": 99.0, "chi_phi_do_tin": "KHAI", "so_nam": 1.0}]
        g = DCQ.buoc4_ghep(hs, {}, kieu="hoi_quy", in_ra=lambda *a: None)
        self.assertEqual(g["ung_vien"], [])

    def test_buoc2_loc_tra_ve_hai_thu_va_khong_no_tren_danh_sach_rong(self):
        giu, kho = DCQ.buoc2_loc([], in_ra=lambda *a: None)
        self.assertEqual(giu, [])
        self.assertIsInstance(kho, dict)


class ThuMucBaoCaoTonTai(unittest.TestCase):
    """`buoc2_loc` ghi `reports/quan_tri_da_loc.json`. Thu muc khong co thi ca
    day chuyen chet o buoc 2 - sau khi da chay xong buoc 1."""

    def test_thu_muc_reports_co_that(self):
        self.assertTrue(DCQ.BC.exists(), f"thieu thu muc {DCQ.BC}")
        self.assertTrue(DCQ.BC.is_dir())

    def test_lab_tro_dung_goc_du_an(self):
        self.assertTrue((DCQ.LAB / "nhan").is_dir())
        self.assertTrue((DCQ.LAB / "b.py").exists())


if __name__ == "__main__":
    unittest.main()
