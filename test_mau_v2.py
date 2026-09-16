# -*- coding: utf-8 -*-
"""Test thu vien mau chien luoc ban 2."""

import unittest

import numpy as np
import pandas as pd

from nhan import mau


class TestMocPhienKhongNhinTruoc(unittest.TestCase):
    def _du_lieu(self):
        idx = pd.date_range("2026-08-10", periods=72, freq="h")
        df = pd.DataFrame({
            "open": np.full(len(idx), 99.0),
            "high": np.full(len(idx), 99.5),
            "low": np.full(len(idx), 98.5),
            "close": np.full(len(idx), 99.0),
        }, index=idx)
        # Phien 8-16 ngay dau co dinh 100. Bar 07:00 ngay sau pha moc nay.
        df.loc["2026-08-10 08:00":"2026-08-10 15:00", "high"] = 100.0
        df.loc["2026-08-11 07:00", "close"] = 105.0
        # Cuc tri 120 chi xuat hien CUOI phien ngay sau; no khong duoc doi tin
        # hieu 07:00 da hinh thanh truoc khi phien 8-16 bat dau.
        df.loc["2026-08-11 15:00", "high"] = 120.0
        return df

    def test_them_tuong_lai_khong_doi_prefix(self):
        df = self._du_lieu()
        day_du = mau.m_moc_phien(df, gio_bd=8, gio_kt=16, chieu=1)
        cat = df.loc[:"2026-08-11 10:00"]
        prefix = mau.m_moc_phien(cat, gio_bd=8, gio_kt=16, chieu=1)
        np.testing.assert_array_equal(day_du[:len(prefix)], prefix)
        self.assertEqual(prefix[cat.index.get_loc("2026-08-11 07:00")], 1.0)


if __name__ == "__main__":
    unittest.main()
