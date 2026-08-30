# -*- coding: utf-8 -*-
"""BA MAU BO SUNG 30/08/2026 — SuperTrend, Stochastic, do doc duong trung binh.

VI SAO THEM. Do 24/08 tren 52 file `.mq5` tai ve tu MQL5 Code Base: 18 la
chien luoc that (con lai la tien ich va chi bao), va trong 18 do **12 khong co
template tuong ung trong `nhan/mau.py`**. Khong co template thi khong co duong
vao QUANTLAB - tuc 12 con bot da nam san tren dia nhung he khong doc duoc chung.
Ba co che duoi day la thu xuat hien nhieu nhat trong 12 file do.

BAI KIEM QUAN TRONG NHAT O DAY LA CHONG NHIN TRUOC. `THIET_KE` va AGENTS.md
deu noi ro: template chi duoc tra ve phoi nhiem MONG MUON tinh tu thong tin
biet TAI `close[i]`, va **template khong duoc tu dich** - engine lo viec do.
Mot dong `.shift(-1)` lot vao la du che ra CAGR 115% (da sap that 15/08 voi
`m_lap_gap`).

Phep do dung o day: cat duoi chuoi roi so phan dau. Neu them du lieu tuong lai
ma tin hieu qua khu DOI, nghia la tin hieu do dang doc tuong lai.

`supertrend` co trang thai noi tiep (dai chi siet, khong noi ra) nen no la mau
DE SAI nhat trong ba - va cung la mau can bai kiem nay nhat.
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

from nhan import mau as MAU   # noqa: E402

BA_MAU = ("supertrend", "stoch_qua_ban", "do_doc_ma")


def _gia(n: int = 1200, hat: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(hat)
    c = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.006, n)))
    o = np.concatenate([[100.0], c[:-1]])
    b = np.abs(rng.normal(0.0, 0.003, n)) * c
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c) + b,
         "low": np.minimum(o, c) - b, "close": c},
        index=pd.date_range("2019-01-01", periods=n, freq="D", tz="UTC"))


class KhongNhinTruoc(unittest.TestCase):

    def test_them_du_lieu_tuong_lai_khong_lam_doi_tin_hieu_qua_khu(self):
        df = _gia()
        cat = 900
        for ten in BA_MAU:
            with self.subTest(mau=ten):
                ham = MAU.MAU[ten]["ham"]
                tham = MAU.MAU[ten]["luoi"][0]
                day = np.asarray(ham(df, **tham), dtype=float)
                ngan = np.asarray(ham(df.iloc[:cat], **tham), dtype=float)
                lech = np.nanmax(np.abs(day[:cat] - ngan))
                self.assertLess(
                    lech, 1e-12,
                    f"'{ten}': them bar tuong lai lam doi tin hieu qua khu "
                    f"(lech toi da {lech}) - dang doc tuong lai")

    def test_moi_bo_tham_so_trong_luoi_deu_khong_nhin_truoc(self):
        """Khong chi bo dau tien: mot bo khac co the di duong code khac."""
        df = _gia(hat=5)
        cat = 800
        for ten in BA_MAU:
            ham = MAU.MAU[ten]["ham"]
            for tham in MAU.MAU[ten]["luoi"]:
                with self.subTest(mau=ten, tham_so=tham):
                    day = np.asarray(ham(df, **tham), dtype=float)
                    ngan = np.asarray(ham(df.iloc[:cat], **tham), dtype=float)
                    self.assertLess(np.nanmax(np.abs(day[:cat] - ngan)), 1e-12)


class HopDongTinHieu(unittest.TestCase):

    def test_tra_ve_dung_do_dai_va_khong_co_NaN(self):
        df = _gia()
        for ten in BA_MAU:
            with self.subTest(mau=ten):
                v = np.asarray(MAU.MAU[ten]["ham"](df, **MAU.MAU[ten]["luoi"][0]),
                               dtype=float)
                self.assertEqual(len(v), len(df))
                self.assertFalse(np.isnan(v).any(), "tin hieu con NaN")

    def test_phoi_nhiem_nam_trong_khoang_cho_phep(self):
        df = _gia()
        for ten in BA_MAU:
            with self.subTest(mau=ten):
                v = np.asarray(MAU.MAU[ten]["ham"](df, **MAU.MAU[ten]["luoi"][0]),
                               dtype=float)
                self.assertLessEqual(np.nanmax(np.abs(v)), 1.0 + 1e-9)

    def test_co_thuc_su_giao_dich_chu_khong_dung_yen(self):
        """Mot mau khong bao gio doi tin hieu la mau vo dung, va no van 'chay'."""
        df = _gia()
        for ten in BA_MAU:
            with self.subTest(mau=ten):
                v = np.asarray(MAU.MAU[ten]["ham"](df, **MAU.MAU[ten]["luoi"][0]),
                               dtype=float)
                self.assertGreater(int((np.diff(v) != 0).sum()), 5,
                                   "tin hieu gan nhu khong bao gio doi")


class ChiMuaThiKhongDuocBAN(unittest.TestCase):

    def test_supertrend_chi_mua_khong_sinh_phoi_nhiem_am(self):
        df = _gia()
        v = np.asarray(MAU.m_supertrend(df, n=10, he_so=3.0, chi_mua=True),
                       dtype=float)
        self.assertGreaterEqual(float(np.nanmin(v)), 0.0,
                                "chi_mua=True ma van co vi the ban")


class SuperTrendDungCoChe(unittest.TestCase):
    """Cai lam nen co che la 'dai chi siet, khong noi ra'. Phai kiem dieu do."""

    def test_dai_tren_chi_siet_xuong_khi_chua_bi_xuyen(self):
        df = _gia(hat=3)
        h = MAU.supertrend(df, n=10, he_so=3.0)
        self.assertEqual(len(h), len(df))
        # huong chi nhan 3 gia tri, va phai co ca hai chieu tren chuoi nay
        gia_tri = set(np.unique(np.asarray(h, dtype=float)))
        self.assertTrue(gia_tri <= {-1.0, 0.0, 1.0}, f"huong la {gia_tri}")
        self.assertIn(1.0, gia_tri)
        self.assertIn(-1.0, gia_tri)

    def test_gia_tang_deu_thi_huong_phai_la_MUA(self):
        n = 400
        c = np.linspace(100.0, 200.0, n)
        df = pd.DataFrame(
            {"open": c, "high": c * 1.001, "low": c * 0.999, "close": c},
            index=pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC"))
        h = np.asarray(MAU.supertrend(df, n=10, he_so=3.0), dtype=float)
        self.assertEqual(h[-1], 1.0, "gia tang deu suot ma khong bao xu huong tang")


class StochDungCoChe(unittest.TestCase):

    def test_dong_cua_sat_day_bien_do_thi_K_gan_0(self):
        n = 200
        rng = np.random.default_rng(2)
        cao = np.full(n, 110.0)
        thap = np.full(n, 90.0)
        c = np.full(n, 90.2)          # luon sat DAY bien do
        df = pd.DataFrame({"open": c, "high": cao, "low": thap, "close": c},
                          index=pd.date_range("2020-01-01", periods=n, freq="D",
                                              tz="UTC"))
        k = MAU.stoch(df, n=14, lam_muot=3).dropna()
        self.assertLess(float(k.mean()), 10.0, "K khong phan anh vi tri sat day")

    def test_dong_cua_sat_dinh_bien_do_thi_K_gan_100(self):
        n = 200
        c = np.full(n, 109.8)
        df = pd.DataFrame({"open": c, "high": np.full(n, 110.0),
                           "low": np.full(n, 90.0), "close": c},
                          index=pd.date_range("2020-01-01", periods=n, freq="D",
                                              tz="UTC"))
        k = MAU.stoch(df, n=14, lam_muot=3).dropna()
        self.assertGreater(float(k.mean()), 90.0)


class DoDocMaKhacMomentum(unittest.TestCase):
    """Neu no chi lap lai `momentum_ema` thi khong dang mot suat kiem dinh."""

    def test_gia_duoi_MA_nhung_MA_van_doc_len_thi_van_bao_MUA(self):
        n = 400
        c = np.linspace(100.0, 160.0, n)
        c[-1] = c[-2] * 0.90          # mot cu sut manh o bar cuoi
        df = pd.DataFrame({"open": c, "high": c * 1.001, "low": c * 0.999,
                           "close": c},
                          index=pd.date_range("2020-01-01", periods=n, freq="D",
                                              tz="UTC"))
        doc = np.asarray(MAU.m_do_doc_ma(df, n=50, cua_so=10), dtype=float)
        mom = np.asarray(MAU.m_momentum_ema(df, n=50), dtype=float)
        self.assertEqual(doc[-1], 1.0,
                         "MA van doc len ma do_doc_ma khong bao mua")
        self.assertNotEqual(
            doc[-1], mom[-1],
            "do_doc_ma cho ket qua y het momentum_ema tren chinh ca phan biet "
            "hai co che - vay no khong them thong tin gi")


if __name__ == "__main__":
    unittest.main()
