# -*- coding: utf-8 -*-
"""Kiem nam chi bao them 12/09/2026: supertrend · keltner · donchian ·
ichimoku · heiken.

## Vi sao chung ra doi

Do 12/09: **72 co che trong kho nhac ten cac chi bao ma ngu phap KHONG noi
duoc** - supertrend 16, keltner 12, donchian 12, ichimoku 10, renko 9, vwap 6,
heiken 5. Chung hoac bi dich gan dung, hoac nam im trong kho.

Va mot chuyen dang noi: cong cu ngoai `streaming_indicators` duoc cham **90
diem** cho nhu cau `toan_tu_co_nho` - mot nhu cau KHONG CO trong so 13 nhu cau
da dang ky, va cau tim ra no la "supertrend indicator python". Tuc cai thieu
that su khong phai mot thu vien, ma la **tu vung cua chinh ngu phap**.

## Hai tinh chat de mat

**1. TOAN TU CO NHO.** `supertrend` va `heiken` phu thuoc gia tri cua CHINH
CHUNG o bar truoc, khong phai mot cua so co dinh. Viet nham thanh ham cua cua
so se ra mot chi bao khac han ma van "chay duoc".

**2. DONCHIAN PHAI DICH MOT BAR.** Kenh tinh tren n bar TRUOC bar hien tai.
Khong dich thi `close >= donchian_tren` gan nhu khong bao gio dung (vi chinh bar
do da nam trong phep max) - mot cach nhin truoc rat kin, va no lam co che pha
vo trong nhu khong bao gio kich hoat.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import ngu_phap as NP  # noqa: E402

MOI = [
    {"chi_bao": "supertrend", "n": 10, "k": 3.0, "lay": "chieu"},
    {"chi_bao": "supertrend", "n": 10, "k": 3.0, "lay": "khoang_cach"},
    {"chi_bao": "keltner", "n": 20, "k": 2.0, "lay": "phan_tram_b"},
    {"chi_bao": "donchian", "n": 20, "lay": "tren"},
    {"chi_bao": "donchian", "n": 20, "lay": "vi_tri"},
    {"chi_bao": "ichimoku", "lay": "kijun"},
    {"chi_bao": "ichimoku", "lay": "day_may"},
    {"chi_bao": "ichimoku", "lay": "chikou"},
    {"chi_bao": "heiken", "lay": "chieu"},
    {"chi_bao": "heiken", "lay": "than"},
]


def chuoi(n=600, hat=5, xu_huong=0.0):
    rng = np.random.default_rng(hat)
    c = 100 + np.cumsum(rng.normal(xu_huong, 0.5, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + np.abs(rng.normal(0, 0.3, n))
    l = np.minimum(o, c) - np.abs(rng.normal(0, 0.3, n))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                        index=pd.date_range("2018-01-01", periods=n, freq="D"))


class KhongCaiNaoNHIN_TRUOC(unittest.TestCase):
    def test_doi_nua_sau_khong_lam_doi_nua_dau(self):
        df = chuoi()
        d2 = df.copy()
        for k in ("open", "high", "low", "close"):
            v = d2[k].to_numpy(float).copy()
            v[400:] *= 1.6
            d2[k] = v
        for t in MOI:
            a = NP.toan_hang(df, t).to_numpy(float)[:380]
            b = NP.toan_hang(d2, t).to_numpy(float)[:380]
            m = np.isfinite(a) & np.isfinite(b)
            np.testing.assert_allclose(
                a[m], b[m], atol=1e-9,
                err_msg="%s NHIN TRUOC" % t)


class DonchianPhaiDICH_MOT_BAR(unittest.TestCase):
    def test_gia_co_the_VUOT_kenh(self):
        """Khong dich thi `close > donchian_tren` gan nhu khong bao gio dung -
        va moi co che pha vo se trong nhu khong bao gio kich hoat."""
        df = chuoi(800, hat=3)
        tren = NP.toan_hang(df, {"chi_bao": "donchian", "n": 20,
                                 "lay": "tren"}).to_numpy(float)
        c = df["close"].to_numpy(float)
        k = np.isfinite(tren)
        ty = float(np.mean(c[k] > tren[k]))
        self.assertGreater(ty, 0.01,
                           "chi %.2f%% bar vuot kenh - kenh chua duoc dich" % (ty * 100))

    def test_tren_luon_lon_hon_duoi(self):
        df = chuoi()
        a = NP.toan_hang(df, {"chi_bao": "donchian", "n": 20, "lay": "tren"}).to_numpy(float)
        b = NP.toan_hang(df, {"chi_bao": "donchian", "n": 20, "lay": "duoi"}).to_numpy(float)
        k = np.isfinite(a) & np.isfinite(b)
        self.assertTrue(np.all(a[k] >= b[k]))


class ToanTuCO_NHO(unittest.TestCase):
    def test_supertrend_LAT_theo_xu_huong(self):
        len_ = 300
        lentr = chuoi(len_, hat=2, xu_huong=0.25)
        xuong = chuoi(len_, hat=2, xu_huong=-0.25)
        a = NP.toan_hang(lentr, {"chi_bao": "supertrend", "n": 10, "k": 3.0,
                                 "lay": "chieu"}).to_numpy(float)
        b = NP.toan_hang(xuong, {"chi_bao": "supertrend", "n": 10, "k": 3.0,
                                 "lay": "chieu"}).to_numpy(float)
        self.assertGreater(np.nanmean(a[50:]), 0.5, "chuoi TANG ma chieu khong duong")
        self.assertLess(np.nanmean(b[50:]), -0.5, "chuoi GIAM ma chieu khong am")

    def test_supertrend_khong_dinh_mot_gia_tri(self):
        df = chuoi(800, hat=8)
        ch = NP.toan_hang(df, {"chi_bao": "supertrend", "n": 10, "k": 3.0,
                               "lay": "chieu"}).to_numpy(float)
        self.assertGreater(int(np.sum(np.diff(ch) != 0)), 3,
                           "supertrend khong lat lan nao - mat trang thai")

    def test_heiken_open_phu_thuoc_bar_TRUOC(self):
        """Neu ai viet lai `ha_open` thanh mot ham cua cua so thi chuoi chieu se
        doi - bai kiem nay chot gia tri that tren mot chuoi dung san."""
        df = pd.DataFrame(
            {"open": [10.0, 11.0, 12.0], "high": [11.0, 12.0, 13.0],
             "low": [9.5, 10.5, 11.5], "close": [10.8, 11.8, 12.8]},
            index=pd.date_range("2020-01-01", periods=3, freq="D"))
        than = NP.toan_hang(df, {"chi_bao": "heiken", "lay": "than"}).to_numpy(float)
        # ha_c0 = (10+11+9.5+10.8)/4 = 10.325 ; ha_o0 = (10+10.8)/2 = 10.4
        self.assertLess(than[0], 0, "bar 0 phai la nen HA giam")
        # ha_o1 = (10.4 + 10.325)/2 = 10.3625 ; ha_c1 = (11+12+10.5+11.8)/4 = 11.325
        self.assertGreater(than[1], 0, "bar 1 phai la nen HA tang")


class VwapKhongDuocLANG_LE_THANH_SMA(unittest.TestCase):
    def test_khong_co_khoi_luong_thi_tra_NaN(self):
        """Mot 'vwap' that ra la SMA se trong nhu mot chi bao khac han, va khong
        ai biet. Tha tra NaN."""
        df = chuoi(200)
        v = NP.toan_hang(df, {"chi_bao": "vwap", "n": 20}).to_numpy(float)
        self.assertTrue(np.all(~np.isfinite(v)))

    def test_co_khoi_luong_thi_tinh_duoc(self):
        df = chuoi(200)
        df["tick_volume"] = np.random.default_rng(1).integers(50, 500, len(df))
        v = NP.toan_hang(df, {"chi_bao": "vwap", "n": 20}).to_numpy(float)
        self.assertTrue(np.isfinite(v[-50:]).all())


class KhaiBaoSaiPhaiNEM(unittest.TestCase):
    def test_lay_la_bi_tu_choi(self):
        df = chuoi(120)
        for cb in ("supertrend", "keltner", "donchian", "ichimoku", "heiken",
                   "vwap"):
            with self.assertRaises(KeyError, msg=cb):
                NP.toan_hang(df, {"chi_bao": cb, "n": 10, "lay": "khong_co"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
