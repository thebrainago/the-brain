# -*- coding: utf-8 -*-
"""DAY CHUYEN 03/09/2026: san -> doc -> boc, noi thanh mot cho goi.

Hom nay du an chay hon 10 tieng tren MOT muc tieu (US500CASH, 20-30 %/nam) va
lo ra ~15 van de. Cac manh sua nam rai o ~10 module; `nhan/day_chuyen.py` noi
chung lai theo dung quy trinh chu du an dat ra, va `b day-chuyen` la cua vao.

Bo test nay KHONG goi mang va KHONG goi LLM: no kiem PHAN NOI DAY - ham co
ton tai khong, chu ky co khop khong, `b` co goi den khong. Do la dung cai da
hong nhieu lan trong du an: ha tang co san nhung khong ai noi day.
"""
from __future__ import annotations

import inspect
import unittest
from unittest import mock

from nhan import day_chuyen as DC


class CoDuBaLuong(unittest.TestCase):
    def test_ba_luong_deu_co_ham(self):
        for ten in ("san", "boc", "mot_luot", "kiem_mang", "bat_warp"):
            self.assertTrue(callable(getattr(DC, ten, None)), ten)

    def test_san_goi_du_ba_nguon(self):
        """LUONG 1 phai gom: theo tai san, theo TEN HE THONG, va MQL5."""
        ma = inspect.getsource(DC.san)
        self.assertIn("MT.san(", ma)
        self.assertIn("san_he_pho_thong", ma)
        self.assertIn("MN.thu_thap", ma)

    def test_boc_goi_doc_song_song_TRUOC_roi_moi_boc(self):
        """San ve ma khong doc toan van thi bo boc khong thay gi - loi da mac
        03/09: san 229 tai lieu roi bao "0 co che" vi bo qua chang doc."""
        ma = inspect.getsource(DC.boc)
        self.assertLess(ma.index("DS.doc("), ma.index("BL.boc("))

    def test_mot_luot_kiem_mang_TRUOC_khi_san(self):
        ma = inspect.getsource(DC.mot_luot)
        self.assertLess(ma.index("kiem_mang"), ma.index("san("))

    def test_mot_luot_tu_bat_warp_khi_mql5_hong(self):
        ma = inspect.getsource(DC.mot_luot)
        self.assertIn("bat_warp", ma)


class NoiVaoB(unittest.TestCase):
    """Ha tang co san nhung khong ai noi day - loi lap lai nhieu lan trong
    du an (quant_plan, auto_follow, candidate_queue)."""

    def setUp(self):
        import importlib.util
        import pathlib
        d = pathlib.Path(__file__).resolve().parent / "b.py"
        spec = importlib.util.spec_from_file_location("_b_thu", d)
        self.b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.b)

    def test_moi_lenh_day_chuyen_deu_co_trong_bang_LENH(self):
        for ten in ("day-chuyen", "san-nguon", "boc", "noi-sinh", "pheu", "mang"):
            self.assertIn(ten, self.b.LENH, ten)

    def test_moi_lenh_deu_goi_duoc(self):
        for ten in ("day-chuyen", "san-nguon", "boc", "noi-sinh", "pheu", "mang"):
            self.assertTrue(callable(self.b.LENH[ten]), ten)

    def test_dc_la_loi_tat_cua_day_chuyen(self):
        self.assertIs(self.b.LENH["dc"], self.b.LENH["day-chuyen"])


class KiemMang(unittest.TestCase):
    def test_bao_cao_du_ba_nguon(self):
        class _R:
            status_code = 200
        with mock.patch("requests.get", return_value=_R()):
            r = DC.kiem_mang(in_ra=lambda *a: None)
        self.assertEqual(set(r), {"mql5", "tradingview", "github"})
        self.assertEqual(set(r.values()), {"OK"})

    def test_ngoai_le_KHONG_lam_no_ca_ham(self):
        """Mot nguon chet khong duoc lam mat bao cao cua hai nguon kia."""
        with mock.patch("requests.get", side_effect=ConnectionError("SNI")):
            r = DC.kiem_mang(in_ra=lambda *a: None)
        self.assertEqual(len(r), 3)
        self.assertTrue(all(v != "OK" for v in r.values()))

    def test_mql5_hong_thi_MACH_cach_sua(self):
        goi = []
        with mock.patch("requests.get", side_effect=TimeoutError("x")):
            DC.kiem_mang(in_ra=lambda *a: goi.append(" ".join(str(x) for x in a)))
        self.assertTrue(any("warp" in d.lower() for d in goi),
                        "bao hong ma khong mach cach sua thi nguoi doc phai tu mo lai")


if __name__ == "__main__":
    unittest.main()
