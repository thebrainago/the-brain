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


GIA_H = {"chi_bao": "gia", "cot": "high"}

MOI = {
    "wma": {"chi_bao": "wma", "n": 10, "cot": "close"},
    "smma": {"chi_bao": "smma", "n": 14, "cot": "close"},
    "phuong_sai": {"chi_bao": "phuong_sai", "cua": GIA, "n": 20},
    "cci": {"chi_bao": "cci", "n": 20},
    "stochastic": {"chi_bao": "stochastic", "n": 14},
    "obv": {"chi_bao": "obv"},
    "adx": {"chi_bao": "adx", "n": 14},
    "tuong_quan": {"chi_bao": "tuong_quan", "n": 50,
                   "toan_hang": [GIA, {"chi_bao": "ema", "n": 20, "cot": "close"}]},
}


class ToanHangMoi(unittest.TestCase):
    """Chin toan hang them 01/09, chon theo SO LAN do duoc trong ma that."""

    def setUp(self):
        self.df = _khung(600)

    def test_tat_ca_tinh_duoc_va_dung_do_dai(self):
        for ten, t in MOI.items():
            x = NP.toan_hang(self.df, t)
            self.assertEqual(len(x), len(self.df), ten)
            self.assertTrue(x.notna().any(), ten)

    def test_adx_trong_khoang_0_100(self):
        x = NP.toan_hang(self.df, MOI["adx"]).dropna()
        self.assertTrue((x >= -1e-9).all() and (x <= 100 + 1e-9).all())

    def test_stochastic_trong_khoang_0_100(self):
        x = NP.toan_hang(self.df, MOI["stochastic"]).dropna()
        self.assertTrue((x >= -1e-9).all() and (x <= 100 + 1e-9).all())

    def test_tuong_quan_trong_khoang_am1_1(self):
        x = NP.toan_hang(self.df, MOI["tuong_quan"]).dropna()
        self.assertTrue((x >= -1.000001).all() and (x <= 1.000001).all())

    def test_phuong_sai_bang_binh_phuong_do_lech(self):
        a = NP.toan_hang(self.df, MOI["phuong_sai"])
        b = NP.toan_hang(self.df, {"chi_bao": "do_lech", "cua": GIA, "n": 20})
        np.testing.assert_allclose(a.dropna(), (b ** 2).dropna(), rtol=1e-10)

    def test_wma_khop_cong_thuc_trong_so(self):
        x = NP.toan_hang(self.df, MOI["wma"])
        c = self.df["close"].astype(float)
        w = np.arange(1, 11, dtype=float)
        mong = c.rolling(10).apply(lambda v: float(np.dot(v, w) / w.sum()), raw=True)
        np.testing.assert_allclose(x.dropna(), mong.dropna(), rtol=1e-12)

    def test_tuong_quan_doi_HAI_toan_hang(self):
        with self.assertRaises(KeyError):
            NP.toan_hang(self.df, {"chi_bao": "tuong_quan", "n": 20,
                                   "toan_hang": [GIA]})

    def test_KHONG_toan_hang_moi_nao_nhin_truoc(self):
        """Rang buoc thoi gian cua ca ngu phap - kiem tung cai mot."""
        d2 = self.df.copy()
        d2.iloc[-1, :] = d2.iloc[-1, :] * 1.5
        for ten, t in MOI.items():
            a = NP.toan_hang(self.df, t).iloc[:-1]
            b = NP.toan_hang(d2, t).iloc[:-1]
            m = a.notna() & b.notna()
            np.testing.assert_allclose(a[m], b[m], rtol=1e-9,
                                       err_msg=f"{ten} nhin truoc")
