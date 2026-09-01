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


class LamMuotToanHangBatKy(unittest.TestCase):
    """`ema`/`sma`/`wma`/`smma` phai lam muot duoc MOT TOAN HANG, khong chi mot cot gia.

    Do that: `SmoothedADX1 = ema(DX, input(6))` lam ca mot chien luoc ADX rot o
    buoc dich, chi vi khong lam muot duoc mot chuoi khong-phai-gia. `tb`/`do_lech`
    da nhan `cua` tu truoc nen day chi la lam cho nhat quan.
    """

    def setUp(self):
        self.df = _khung(500)

    def test_ema_cua_mot_chi_bao(self):
        t = {"chi_bao": "ema", "n": 6, "cua": {"chi_bao": "adx", "n": 14}}
        self.assertEqual(NP._kiem_toan_hang(t), [])
        x = NP.toan_hang(self.df, t)
        self.assertTrue(x.notna().any())

    def test_bon_duong_trung_binh_deu_nhan_cua(self):
        for cb in ("ema", "sma", "wma", "smma"):
            t = {"chi_bao": cb, "n": 5, "cua": {"chi_bao": "rsi", "n": 14}}
            x = NP.toan_hang(self.df, t)
            self.assertTrue(x.notna().any(), cb)

    def test_khong_co_cua_thi_van_dung_cot_nhu_cu(self):
        a = NP.toan_hang(self.df, {"chi_bao": "ema", "n": 10, "cot": "close"})
        b = NP.toan_hang(self.df, {"chi_bao": "ema", "n": 10,
                                   "cua": {"chi_bao": "gia", "cot": "close"}})
        np.testing.assert_allclose(a.dropna(), b.dropna(), rtol=1e-12)

    def test_lam_muot_khong_nhin_truoc(self):
        t = {"chi_bao": "ema", "n": 6, "cua": {"chi_bao": "adx", "n": 14}}
        d2 = self.df.copy()
        d2.iloc[-1, :] = d2.iloc[-1, :] * 1.5
        a, b = NP.toan_hang(self.df, t).iloc[:-1], NP.toan_hang(d2, t).iloc[:-1]
        m = a.notna() & b.notna()
        np.testing.assert_allclose(a[m], b[m], rtol=1e-9)


class ToanTuCoNho(unittest.TestCase):
    """Toan tu CO NHO TRANG THAI - `direction`, supertrend, chuoi lien tiep.

    11/18 chien luoc Pine con lai deu chan o cung mot loai bieu thuc: gia tri hom
    nay phu thuoc gia tri hom qua theo mot quy tac re nhanh. Ngu phap truoc do
    chi co toan tu KHONG NHO nen khong phat bieu duoc.
    """

    def setUp(self):
        self.df = _khung(500)
        tren = {"chi_bao": "tuyen_tinh", "he_so": [1.0, 2.0],
                "toan_hang": [{"chi_bao": "ema", "n": 20, "cot": "close"},
                              {"chi_bao": "atr", "n": 14}]}
        duoi = dict(tren, he_so=[1.0, -2.0])
        self.st = {"chi_bao": "trang_thai_lat",
                   "len": {"trai": GIA, "phep": ">", "phai": tren},
                   "xuong": {"trai": GIA, "phep": "<", "phai": duoi}}
        self.dem = {"chi_bao": "dem_lien_tiep",
                    "khi": {"trai": GIA, "phep": ">",
                            "phai": {"chi_bao": "ema", "n": 50, "cot": "close"}}}

    def test_trang_thai_chi_nhan_ba_gia_tri(self):
        x = set(NP.toan_hang(self.df, self.st).unique())
        self.assertTrue(x <= {-1.0, 0.0, 1.0}, x)

    def test_trang_thai_GIU_NGUYEN_khi_khong_co_tin_hieu_lat(self):
        """Do la ban chat cua 'co nho': khong lat thi giu, khong ve 0."""
        x = NP.toan_hang(self.df, self.st).to_numpy()
        doi = (x[1:] != x[:-1]).sum()
        self.assertLess(doi, len(x) / 2, "trang thai lat qua nhieu - khong con la trang thai")

    def test_dem_lien_tiep_ve_0_khi_dieu_kien_sai(self):
        y = NP.toan_hang(self.df, self.dem).to_numpy()
        self.assertIn(0.0, set(y))
        self.assertGreater(y.max(), 1)

    def test_dem_tang_dung_mot_moi_bar(self):
        y = NP.toan_hang(self.df, self.dem).to_numpy()
        for i in range(1, len(y)):
            if y[i] > 0:
                self.assertAlmostEqual(y[i], y[i - 1] + 1, places=9)

    def test_KHONG_nhin_truoc(self):
        """Quan trong nhat: co nho van phai nhan qua."""
        d2 = self.df.copy()
        d2.iloc[-1, :] = d2.iloc[-1, :] * 1.5
        for ten, t in (("trang_thai_lat", self.st), ("dem_lien_tiep", self.dem)):
            a = NP.toan_hang(self.df, t).iloc[:-1]
            b = NP.toan_hang(d2, t).iloc[:-1]
            np.testing.assert_allclose(a, b, rtol=1e-12, err_msg=ten)

    def test_cu_phap_bat_thieu_dieu_kien(self):
        self.assertTrue(NP._kiem_toan_hang({"chi_bao": "trang_thai_lat"}))
        self.assertTrue(NP._kiem_toan_hang({"chi_bao": "dem_lien_tiep"}))

    def test_cu_phap_dat_khi_khai_du(self):
        self.assertEqual(NP._kiem_toan_hang(self.st), [])
        self.assertEqual(NP._kiem_toan_hang(self.dem), [])

    def test_dung_duoc_trong_mot_co_che_that(self):
        spec = {"ten": "thu_co_nho", "ho": "xu_huong", "chieu": 1, "giu": 1,
                "co_che": "Chi mua khi che do dang len - mot cau du dai cho cong.",
                "vao": [{"trai": self.st, "phep": ">", "phai": {"hang": 0}}]}
        self.assertEqual(NP.kiem_khai_bao(spec), [])
