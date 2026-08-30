# -*- coding: utf-8 -*-
"""Bo kiem du lieu: bat open BIA, bat bang thieu cot, va KHONG loai nham.

Ba loi that da tim thay ngay 21/08/2026:

1. `kiem()` doc thang `df["open"]` nen mot bang chi co cot `close` (ETF_SPY)
   hoac RONG hoan toan (VIX) lam ham NEM KeyError thay vi tra "khong dung duoc".
2. Nguong xet la trung binh TOAN CHUOI nen giau mat mang bi nhiem: SP500 co
   39,9% toan chuoi (dat) trong khi 1967-1999 la 93-97% bia; FTSE100 co 68%
   toan chuoi (dat) trong khi 2016-2024 la 100% bia.
3. Va o chieu nguoc lai, nguong dat qua thap (0,30) loai nham 18 chuoi FX/CFD
   hop le - voi thi truong LIEN TUC thi `open[i]==close[i-1]` 30-44% la binh
   thuong, khong phai bia.

Bo test khoa ca ba, va dac biet khoa chieu thu ba: mot bo kiem loai sach moi thu
khong phan biet duoc voi mot bo kiem dung.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import du_lieu as DL


def _bang(n=800, bat_dau="2010-01-04", open_bia=False, thieu=()):
    """Sinh mot bang OHLC gia. `open_bia` = open chep tu close hom truoc."""
    rng = np.random.default_rng(5)
    idx = pd.bdate_range(bat_dau, periods=n)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, n)))
    if open_bia:
        op = np.concatenate([[close[0]], close[:-1]])
    else:
        op = close * (1 + rng.normal(0, 0.004, n))
    df = pd.DataFrame({
        "open": op, "close": close,
        "high": np.maximum(op, close) * 1.004,
        "low": np.minimum(op, close) * 0.996,
    }, index=idx)
    return df.drop(columns=[c for c in thieu if c in df.columns])


class ThieuCot(unittest.TestCase):
    """Phai TRA VE ket qua, khong duoc nem."""

    def test_thieu_open_thi_bao_khong_dung_duoc(self):
        bc = DL.kiem(_bang(thieu=("open",)), "THIEU_OPEN")
        self.assertFalse(bc["dung_duoc"])
        self.assertIn("open", bc["cot_thieu"])

    def test_bang_rong_hoan_toan(self):
        bc = DL.kiem(pd.DataFrame(index=pd.bdate_range("2010-01-04", periods=500)),
                     "RONG")
        self.assertFalse(bc["dung_duoc"])

    def test_chi_co_close(self):
        bc = DL.kiem(_bang(thieu=("open", "high", "low")), "CHI_CLOSE")
        self.assertFalse(bc["dung_duoc"])
        self.assertEqual(sorted(bc["cot_thieu"]), ["high", "low", "open"])


class OpenBia(unittest.TestCase):

    def test_open_bia_toan_bo_bi_loai(self):
        bc = DL.kiem(_bang(open_bia=True), "BIA")
        self.assertFalse(bc["dung_duoc"])
        self.assertGreater(bc["ty_le_open_bang_close_truoc"], 0.9)

    def test_open_that_thi_dat(self):
        bc = DL.kiem(_bang(open_bia=False), "THAT")
        self.assertTrue(bc["dung_duoc"], bc["canh_bao"])
        self.assertLess(bc["ty_le_open_bang_close_truoc"], 0.1)

    def test_bat_duoc_MANG_bi_nhiem_du_trung_binh_van_dat(self):
        """SP500: 39,9% toan chuoi (dat) nhung 1967-1999 la 93-97% bia."""
        sach = _bang(500, "2000-01-03", open_bia=False)
        ban = _bang(500, "2010-01-04", open_bia=True)
        df = pd.concat([sach, ban])
        bc = DL.kiem(df, "MANG_NHIEM")
        nam_sach = set(bc["nam_open_that"])
        self.assertTrue({2000, 2001}.issubset(nam_sach), sorted(nam_sach))
        self.assertFalse(nam_sach & {2011, 2012}, sorted(nam_sach))
        self.assertTrue(any("phai CAT bo" in c for c in bc["canh_bao"]), bc["canh_bao"])


class KhongLoaiNham(unittest.TestCase):
    """BAI KIEM LUC. Mot bo kiem loai sach moi thu cung 'bat duoc open bia'."""

    def test_thi_truong_lien_tuc_khong_bi_loai(self):
        """FX H1/H4 co 30-44% open==close[t-1] va do la HOP LE."""
        rng = np.random.default_rng(11)
        n = 3000
        idx = pd.date_range("2015-01-01", periods=n, freq="4h")
        close = 1.3 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
        op = np.concatenate([[close[0]], close[:-1]]).copy()
        # 60% bar mo dung o close truoc, 40% co gap nho -> ty le ~0,60 la ranh gioi
        gap = rng.random(n) > 0.60
        op[gap] = close[gap] * (1 + rng.normal(0, 0.001, gap.sum()))
        df = pd.DataFrame({"open": op, "close": close,
                           "high": np.maximum(op, close) * 1.001,
                           "low": np.minimum(op, close) * 0.999}, index=idx)
        bc = DL.kiem(df, "FX_LIEN_TUC")
        self.assertLess(bc["ty_le_open_bang_close_truoc"], DL.NGUONG_OPEN_BIA + 0.05)
        self.assertTrue(bc["dung_duoc"], bc["canh_bao"])

    def test_nguong_khong_duoc_dat_thap(self):
        """0,30 tung loai nham 18 chuoi FX/CFD hop le."""
        self.assertGreaterEqual(DL.NGUONG_OPEN_BIA, 0.50)


class GomDoan(unittest.TestCase):

    def test_gom_nam_lien_tuc(self):
        self.assertEqual(DL._gom_doan([1927, 1928, 1929, 1935, 1936]),
                         [(1927, 1929), (1935, 1936)])

    def test_rong(self):
        self.assertEqual(DL._gom_doan([]), [])

    def test_doan_dai_nhat(self):
        self.assertEqual(DL.doan_dai_nhat([(1928, 1961), (2007, 2026)]), (1928, 1961))
        self.assertIsNone(DL.doan_dai_nhat([]))


class CatTheoChatLuong(unittest.TestCase):

    def test_cat_ve_doan_sach_dai_nhat(self):
        sach = _bang(600, "2000-01-03", open_bia=False)
        ban = _bang(600, "2010-01-04", open_bia=True)
        da_cat, bc = DL.cat_theo_chat_luong(pd.concat([sach, ban]), "CAT")
        self.assertGreater(len(da_cat), 0)
        self.assertLess(da_cat.index.max().year, 2010)
        self.assertEqual(bc["so_bar_sau_cat"], len(da_cat))

    def test_khong_co_doan_nao_sach_thi_tra_rong(self):
        da_cat, _ = DL.cat_theo_chat_luong(_bang(600, open_bia=True), "BIA")
        self.assertEqual(len(da_cat), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
