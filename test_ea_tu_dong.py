# -*- coding: utf-8 -*-
"""Test cho `ea_tu_dong.py`.

Khong test phan cham mang hay goi MetaEditor. Test dung nhung cho DA SAP THAT:
duong dan `Report=`, mac dinh `Model`, va viec doc input cua tac gia.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import ea_tu_dong as EA


class TenSach(unittest.TestCase):
    def test_bo_ky_tu_pha_duong_dan(self):
        self.assertEqual(EA.ten_sach("[MQL5 mt5/experts] Sonic R v2.1!"),
                         "MQL5_mt5_experts_Sonic_R_v2_1")

    def test_khong_bao_gio_rong(self):
        self.assertTrue(EA.ten_sach("!!!"))

    def test_co_tran_do_dai(self):
        self.assertLessEqual(len(EA.ten_sach("x" * 200)), 40)


class VietIni(unittest.TestCase):
    def setUp(self):
        self.p = EA.viet_ini("thu_test", "abc.ex5", "abc.set", "US500m", "H1",
                             "2022.01.01", "2026.06.30")
        self.t = self.p.read_text(encoding="utf-16")

    def tearDown(self):
        try:
            self.p.unlink()
        except OSError:
            pass

    def test_report_la_duong_TUONG_DOI(self):
        """`Report=` tuyet doi bi tester lo di, khong bao loi (bai hoc 27/07)."""
        dong = [l for l in self.t.splitlines() if l.startswith("Report=")][0]
        gia_tri = dong.split("=", 1)[1]
        self.assertFalse(Path(gia_tri).is_absolute(), dong)
        self.assertNotIn(":", gia_tri)

    def test_mac_dinh_la_Model_4_tick_that(self):
        """`Model=1` noi doi khi TP/SL nho hon ~2x bien do nen M1 (bay 01/08)."""
        self.assertIn("Model=4", self.t)

    def test_tat_toi_uu_hoa(self):
        """MT5 optimization chon tham so = curve-fitting (luat cua du an)."""
        self.assertIn("Optimization=0", self.t)

    def test_tu_thoat_de_chay_hang_loat_duoc(self):
        self.assertIn("ShutdownTerminal=1", self.t)

    def test_ghi_bang_utf16(self):
        """MT5 chi doc .ini utf-16; utf-8 thi terminal mo roi khong chay gi."""
        with self.assertRaises(UnicodeDecodeError):
            self.p.read_text(encoding="utf-8")


class DocInputCuaTacGia(unittest.TestCase):
    MA = ("input int    InpPeriod = 14;   // chu ky\n"
          "input double InpRisk   = 2.0;  // rui ro %\n"
          "input bool   InpDung   = true;\n")

    def test_chi_lay_input_co_gia_tri_SO(self):
        from nhan import doc_ma as DM
        khai = DM.rut_input(self.MA)
        self.assertEqual(set(khai), {"InpPeriod", "InpRisk"})
        self.assertEqual(khai["InpPeriod"]["gia_tri"], 14.0)


class Duong(unittest.TestCase):
    def test_moi_terminal_deu_khai_du_ba_duong(self):
        for ten in EA.TERMINAL:
            mql5, me, term = EA._duong(ten)
            self.assertTrue(str(mql5).endswith("MQL5"))
            self.assertTrue(str(me).endswith("metaeditor64.exe"))
            self.assertTrue(str(term).endswith("terminal64.exe"))


if __name__ == "__main__":
    unittest.main()
