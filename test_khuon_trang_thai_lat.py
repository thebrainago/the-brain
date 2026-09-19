# -*- coding: utf-8 -*-
"""DON HANG MAU: khuon `che_do_lat` cho `nhan/hephaestus.py`.

Bai test nay la DAC TA. No duoc viet TRUOC phan cai dat, va phan cai dat la
thu giao cho mot mo hinh re go (xem `qwen/tho_code.py`).

`trang_thai_lat` la mot trong nam toan hang ngu phap noi duoc ma may de chua
dung toi. No la mot co NHO TRANG THAI: bat len khi mot dieu kien xay ra, va chi
tat khi mot dieu kien KHAC xay ra - khac han mot bo loc khong nho gi.

Luan diem giao dich: che do thi truong khong doi tung bar, no doi tung doan.
Mot bo loc khong nho se nhay vao nhay ra o vung ranh gioi va dong lenh o dung
luc te nhat; mot co trang thai thi giu nguyen cho den khi co bang chung nguoc.
"""
from __future__ import annotations

import unittest

from nhan import hephaestus as HP
from nhan import ngu_phap as NP


class KhuonCheDoLat(unittest.TestCase):

    def setUp(self):
        self.ds = HP.duc(han_ngach=100000, khuon="che_do_lat")

    def test_co_khuon_trong_danh_sach(self):
        self.assertIn("che_do_lat", [t for t, _ in HP.KHUON])

    def test_de_ra_duoc_co_che(self):
        self.assertGreaterEqual(len(self.ds), 2)

    def test_deu_dung_toan_hang_trang_thai_lat(self):
        for s in self.ds:
            t = set()
            HP._chi_bao_trong(s["vao"], t)
            self.assertIn("trang_thai_lat", t, s["ten"])

    def test_qua_duoc_cong_cu_phap(self):
        for s in self.ds:
            self.assertEqual(NP.kiem_khai_bao(s), [], s["ten"])

    def test_hai_nguong_bat_va_tat_PHAI_KHAC_NHAU(self):
        """Co trang thai ma bat/tat cung mot nguong thi no chi la mot bo loc
        thong thuong doi ten - khong nho gi ca, va vao ra lien tuc o ranh gioi.
        """
        for s in self.ds:
            for d in s["vao"]:
                t = d.get("trai") or {}
                if t.get("chi_bao") != "trang_thai_lat":
                    continue
                self.assertNotEqual(t.get("len"), t.get("xuong"), s["ten"])

    def test_chay_that_khong_nem_loi(self):
        import numpy as np
        import pandas as pd
        rng = np.random.default_rng(5)
        n = 3000
        c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
        op = np.r_[c[0], c[:-1]]
        df = pd.DataFrame(
            {"open": op, "high": np.maximum(c, op) * 1.002,
             "low": np.minimum(c, op) * 0.998, "close": c,
             "tick_volume": np.full(n, 100.0)},
            index=pd.date_range("2020-01-01", periods=n, freq="h"))
        for s in self.ds:
            th = NP.sinh_tu_spec(s, df)
            self.assertEqual(len(th), n, s["ten"])
            # Mot co NHO TRANG THAI phai co ca luc bat lan luc tat tren mot
            # chuoi 3.000 bar. Toan 0 nghia la co khong bao gio bat; toan khac
            # 0 nghia la no bat tu bar dau va khong bao gio tat - ca hai deu
            # khong phai mot co trang thai.
            ty = float(np.mean(np.abs(th) > 1e-12))
            self.assertGreater(ty, 0.0, "%s: khong bao gio bat" % s["ten"])
            self.assertLess(ty, 1.0, "%s: bat roi khong bao gio tat" % s["ten"])

    def test_nam_trong_lo_chung_va_khong_trung(self):
        het = HP.duc(han_ngach=100000)
        ten = {s["ten"] for s in het}
        for s in self.ds:
            self.assertIn(s["ten"], ten)
        vt = [NP.van_tay_dieu_kien(s) for s in het]
        self.assertEqual(len(vt), len(set(vt)))
