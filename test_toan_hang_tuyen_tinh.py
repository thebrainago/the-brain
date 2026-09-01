# -*- coding: utf-8 -*-
"""Toan hang TUYEN TINH - mo ho "so gia voi mot MUC DUOC TINH RA".

Vi sao co: bo doc ma rut duoc guard cua `strategy.entry` roi nhung phan lon dieu
kien Pine that so gia voi mot muc tinh toan (`crossover(source, BBlower)` voi
`BBlower = basis - mult*dev`, kenh Keltner, pivot). Ngu phap co `tb` va `do_lech`
nhung khong co phep cong/nhan nen khong viet noi `tb + 2*do_lech`.
"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from nhan import ngu_phap as NP


def _khung(n: int = 400, hat: int = 3) -> pd.DataFrame:
    r = np.random.default_rng(hat)
    c = 100 + np.cumsum(r.normal(0, 1, n))
    return pd.DataFrame(
        {"open": c + r.normal(0, .2, n), "high": c + abs(r.normal(0, .5, n)),
         "low": c - abs(r.normal(0, .5, n)), "close": c},
        index=pd.date_range("2020-01-01", periods=n, freq="h"))


GIA = {"chi_bao": "gia", "cot": "close"}
BB_DUOI = {"chi_bao": "tuyen_tinh",
           "toan_hang": [{"chi_bao": "tb", "cua": GIA, "n": 20},
                         {"chi_bao": "do_lech", "cua": GIA, "n": 20}],
           "he_so": [1.0, -2.0]}


class TinhDung(unittest.TestCase):
    def setUp(self):
        self.df = _khung()

    def test_tai_lap_dung_cong_thuc_bollinger(self):
        x = NP.toan_hang(self.df, BB_DUOI)
        c = self.df["close"].astype(float)
        mong = c.rolling(20).mean() - 2.0 * c.rolling(20).std()
        np.testing.assert_allclose(x.dropna(), mong.dropna(), rtol=1e-12)

    def test_keltner_tren_bang_ema_cong_atr(self):
        kelt = {"chi_bao": "tuyen_tinh",
                "toan_hang": [{"chi_bao": "ema", "n": 20, "cot": "close"},
                              {"chi_bao": "atr", "n": 14}],
                "he_so": [1.0, 2.0]}
        x = NP.toan_hang(self.df, kelt)
        self.assertEqual(len(x), len(self.df))
        self.assertTrue(x.notna().any())

    def test_cong_them_la_do_lech_khong_doi(self):
        a = NP.toan_hang(self.df, BB_DUOI)
        b = NP.toan_hang(self.df, dict(BB_DUOI, cong_them=5.0))
        np.testing.assert_allclose((b - a).dropna(), 5.0, rtol=1e-12)


class KhongNhinTruoc(unittest.TestCase):
    def test_sua_bar_cuoi_khong_doi_gia_tri_truoc(self):
        """Rang buoc thoi gian cua ca ngu phap phai giu nguyen o toan tu moi."""
        df = _khung()
        a = NP.toan_hang(df, BB_DUOI)
        d2 = df.copy()
        d2.iloc[-1, :] = d2.iloc[-1, :] * 2
        b = NP.toan_hang(d2, BB_DUOI)
        np.testing.assert_allclose(a.iloc[:-1].dropna(), b.iloc[:-1].dropna(),
                                   rtol=1e-12)


class KiemKhaiBao(unittest.TestCase):
    def _spec(self, phai):
        return {"ten": "thu_tt", "ho": "quay_ve_trung_binh", "chieu": 1, "giu": 1,
                "co_che": "Mot cau du dai de qua duoc bai kiem do dai cua cong.",
                "vao": [{"trai": GIA, "phep": "<", "phai": phai}]}

    def test_khai_bao_dung_thi_dat(self):
        self.assertEqual(NP.kiem_khai_bao(self._spec(BB_DUOI)), [])

    def test_he_so_lech_do_dai_bi_bat_o_CU_PHAP(self):
        """Phai bat TRUOC khi cham du lieu, khong doi toi luc chay backtest."""
        xau = dict(BB_DUOI, he_so=[1.0])
        loi = NP.kiem_khai_bao(self._spec(xau))
        self.assertTrue(any("he_so" in x for x in loi), loi)

    def test_he_so_khong_phai_so_thi_bi_bat(self):
        xau = dict(BB_DUOI, he_so=[1.0, "hai"])
        loi = NP.kiem_khai_bao(self._spec(xau))
        self.assertTrue(any("he_so" in x for x in loi), loi)

    def test_toan_hang_rong_thi_bi_bat(self):
        xau = dict(BB_DUOI, toan_hang=[], he_so=[])
        self.assertTrue(NP.kiem_khai_bao(self._spec(xau)))


if __name__ == "__main__":
    unittest.main()
