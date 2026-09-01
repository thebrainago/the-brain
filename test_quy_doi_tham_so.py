# -*- coding: utf-8 -*-
"""Test cho `nhan/quy_doi_tham_so.py`.

Moc doi chieu la ca do that: `GDS Renko Fast Demo EA` chay tren EURUSDmicro voi
tham so mac dinh cua tac gia cho **0 lenh** tren 30,8 trieu tick, vi
`InpFastBrickSize = 21.0` don vi gia la vien gach lon gap hai muoi lan bien do
cua mot cap tien te.
"""
from __future__ import annotations

import unittest

from nhan import quy_doi_tham_so as QD

MA = """
input double InpFastBrickSize    = 21.0;  // Fast Renko brick size in price units
input double InpSlowBrickSize    = 39.0;  // Slow Renko brick size in price units
input int    InpEntryRunBricks   = 1;     // Fast bricks required for entry
input double InpTakeProfitBricks = 1.4;   // Take profit in fast bricks
input double InpStopLossBricks   = 2.1;   // Stop loss in fast bricks
input int    InpMaxHoldMinutes   = 200;   // Maximum holding time
input double InpMaxSpreadFraction= 0.57;  // Max spread as fraction of fast brick
input double InpLots             = 0.01;  // Fixed lot size
input int    InpSlPoints         = 300;   // Stop loss in points
input double InpRiskPercent      = 2.0;   // Risk percent of balance
input bool   InpDung             = true;
"""


class PhanLoai(unittest.TestCase):
    def setUp(self):
        self.k = {x["ten"]: x for x in QD.rut_khai_bao(MA)}

    def test_don_vi_gia_nhan_ra_tu_chu_thich(self):
        self.assertEqual(self.k["InpFastBrickSize"]["don_vi"], "gia")
        self.assertEqual(self.k["InpSlowBrickSize"]["don_vi"], "gia")

    def test_boi_so_khong_phai_gia(self):
        """'in fast bricks' la BOI SO cua vien gach, khong phai mot muc gia."""
        for t in ("InpTakeProfitBricks", "InpStopLossBricks",
                  "InpMaxSpreadFraction"):
            self.assertEqual(self.k[t]["don_vi"], "boi_so", t)

    def test_dem_so_vien_KHAC_kich_thuoc_vien(self):
        """`EntryRunBricks` la DEM. Ten chua 'brick' nhung khong phai gia.

        Da sap that: xep nham thanh `gia` thi quy doi bien 'cho 1 vien' thanh
        mot so thap phan vo nghia.
        """
        self.assertEqual(self.k["InpEntryRunBricks"]["don_vi"], "dem")

    def test_diem_va_phan_tram(self):
        self.assertEqual(self.k["InpSlPoints"]["don_vi"], "diem")
        self.assertEqual(self.k["InpRiskPercent"]["don_vi"], "phan_tram")

    def test_lot(self):
        self.assertEqual(self.k["InpLots"]["don_vi"], "lot")

    def test_bo_qua_input_khong_phai_so(self):
        self.assertNotIn("InpDung", self.k)

    def test_int_khong_chu_thich_thi_la_dem(self):
        self.assertEqual(QD.phan_loai("XyzAbc", "", "int"), "dem")

    def test_khong_doan_khi_khong_co_dau_hieu(self):
        """Khong doc duoc thi phai noi khong biet, khong duoc doan."""
        self.assertEqual(QD.phan_loai("Xyz", "", "double"), "khong_ro")


class QuyDoi(unittest.TestCase):
    def setUp(self):
        self.khai = QD.rut_khai_bao(MA)
        # ATR that do duoc: XAUUSD H1 ~3,44 · EURUSD H1 ~0,00187
        self.r = QD.quy_doi(self.khai, 3.4417, 0.0018705)

    def test_chi_don_vi_gia_bi_doi(self):
        doi = {d["ten"] for d in self.r["da_doi"]}
        self.assertEqual(doi, {"InpFastBrickSize", "InpSlowBrickSize",
                               "InpSlPoints"})

    def test_giu_nguyen_so_lan_ATR(self):
        """21 don vi gia tren vang = bao nhieu ATR thi tren EURUSD cung the."""
        k_cu = 21.0 / 3.4417
        k_moi = self.r["tham_so"]["InpFastBrickSize"] / 0.0018705
        self.assertAlmostEqual(k_cu, k_moi, places=6)

    def test_boi_so_va_dem_va_lot_KHONG_doi(self):
        for t, v in (("InpTakeProfitBricks", 1.4), ("InpStopLossBricks", 2.1),
                     ("InpEntryRunBricks", 1.0), ("InpMaxHoldMinutes", 200.0),
                     ("InpLots", 0.01), ("InpRiskPercent", 2.0)):
            self.assertEqual(self.r["tham_so"][t], v, t)

    def test_ty_le_point_duoc_dung_cho_don_vi_diem_khi_biet(self):
        r = QD.quy_doi(self.khai, 3.4417, 0.0018705,
                       diem_goc=0.01, diem_dich=0.00001)
        self.assertNotEqual(r["tham_so"]["InpSlPoints"],
                            self.r["tham_so"]["InpSlPoints"])

    def test_atr_khong_duong_thi_nem(self):
        for a, b in ((0, 1.0), (1.0, 0), (-1.0, 1.0)):
            with self.assertRaises(ValueError):
                QD.quy_doi(self.khai, a, b)

    def test_khong_ro_duoc_bao_ra_chu_khong_im_lang(self):
        khai = [{"ten": "La", "kieu": "double", "gia_tri": 5.0,
                 "chu_thich": "", "don_vi": "khong_ro"}]
        r = QD.quy_doi(khai, 1.0, 2.0)
        self.assertEqual(r["khong_ro"], ["La"])
        self.assertEqual(r["tham_so"]["La"], 5.0)


if __name__ == "__main__":
    unittest.main()
