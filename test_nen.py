# -*- coding: utf-8 -*-
"""Test cho `nhan/nen.py`.

Bai kiem quan trong nhat o day khong phai cong thuc HA (ai cung tra cuu duoc) ma
la RANH GIOI: nen bien doi chi duoc cham vao TIN HIEU, khong duoc cham vao gia
khop lenh. Vi pham ranh gioi do la che ra lai tu cho khong co - cung ho voi bay
`Model=1`.
"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from nhan import nen as NEN


def _khung(n: int = 200, hat: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(hat)
    c = 100 + np.cumsum(rng.normal(0, 1, n))
    o = c + rng.normal(0, 0.3, n)
    h = np.maximum(o, c) + np.abs(rng.normal(0, 0.4, n))
    l = np.minimum(o, c) - np.abs(rng.normal(0, 0.4, n))
    return pd.DataFrame(
        {"open": o, "high": h, "low": l, "close": c},
        index=pd.date_range("2020-01-01", periods=n, freq="h"))


class CongThuc(unittest.TestCase):
    def setUp(self):
        self.df = _khung()
        self.ha = NEN.heikin_ashi(self.df)

    def test_cung_chi_so_va_so_dong(self):
        self.assertEqual(len(self.ha), len(self.df))
        self.assertTrue(self.ha.index.equals(self.df.index))

    def test_ha_close_la_trung_binh_ohlc(self):
        mong = self.df[["open", "high", "low", "close"]].mean(axis=1)
        np.testing.assert_allclose(self.ha["close"].to_numpy(),
                                   mong.to_numpy(), rtol=1e-12)

    def test_ha_open_de_quy_tren_qua_khu(self):
        o, c = self.ha["open"].to_numpy(), self.ha["close"].to_numpy()
        for i in range(1, 20):
            self.assertAlmostEqual(o[i], (o[i - 1] + c[i - 1]) / 2.0, places=10)

    def test_high_low_bao_ca_than_nen(self):
        self.assertTrue((self.ha["high"] >= self.ha[["open", "close"]].max(axis=1)).all())
        self.assertTrue((self.ha["low"] <= self.ha[["open", "close"]].min(axis=1)).all())


class NhanQua(unittest.TestCase):
    """Doi mot bar o TUONG LAI khong duoc lam doi bat ky gia tri HA nao truoc do."""

    def test_khong_nhin_truoc(self):
        df = _khung()
        ha1 = NEN.heikin_ashi(df)
        d2 = df.copy()
        d2.iloc[150:, :] = d2.iloc[150:, :] * 1.5      # pha toan bo phan sau
        ha2 = NEN.heikin_ashi(d2)
        np.testing.assert_allclose(ha1.iloc[:150].to_numpy(),
                                   ha2.iloc[:150].to_numpy(), rtol=1e-12)


class RanhGioi(unittest.TestCase):
    def test_thuong_tra_ve_chinh_no(self):
        df = _khung()
        self.assertIs(NEN.bien_doi(df, NEN.THUONG), df)

    def test_bien_doi_KHONG_sua_khung_goc(self):
        """Khung that phai nguyen ven - do la khung se dung de khop lenh."""
        df = _khung()
        goc = df.copy()
        NEN.bien_doi(df, NEN.HA)
        pd.testing.assert_frame_equal(df, goc)

    def test_sinh_tren_nen_tra_mang_theo_khung_that(self):
        df = _khung()
        th = NEN.sinh_tren_nen(lambda d: (d["close"] > d["open"]).to_numpy(float),
                               df, NEN.HA)
        self.assertEqual(len(th), len(df))

    def test_tin_hieu_HA_khac_tin_hieu_thuong(self):
        """Neu giong het thi lop nen nay khong lam gi ca - phai do duoc."""
        df = _khung()
        f = lambda d: (d["close"] > d["open"]).to_numpy(float)   # noqa: E731
        a = NEN.sinh_tren_nen(f, df, NEN.THUONG)
        b = NEN.sinh_tren_nen(f, df, NEN.HA)
        self.assertFalse(np.array_equal(a, b))

    def test_tin_hieu_lech_do_dai_thi_nem(self):
        df = _khung()
        with self.assertRaises(ValueError):
            NEN.sinh_tren_nen(lambda d: np.ones(len(d) - 3), df, NEN.HA)

    def test_loai_la_thi_nem(self):
        with self.assertRaises(KeyError):
            NEN.bien_doi(_khung(), "renko")

    def test_khong_co_renko(self):
        """Renko khong tai lap duoc tren thi truong that - xem SONIC_R muc 3.4."""
        self.assertNotIn("renko", NEN.LOAI)

    def test_thieu_cot_thi_nem(self):
        df = _khung().drop(columns=["high"])
        with self.assertRaises(KeyError):
            NEN.bien_doi(df, NEN.HA)


if __name__ == "__main__":
    unittest.main()
