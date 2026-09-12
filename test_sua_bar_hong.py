# -*- coding: utf-8 -*-
"""Kiem `du_lieu.sua_bar_hong` - cua duy nhat chan bar KHONG THE TON TAI.

## Vi sao co file nay

12/09/2026, truy mot ket qua vo ly trong bang xep hang quan tri:

    GBPZAR `chot_nhanh_sl1_tp1`:  CAGR 591%/nam,  maxDD -99,38%

Lan nguoc ra du lieu goc thi thay doan 09/2023-01/2024 cua GBPZAR co **ca cot
`high` bi nhan 10** (233,29 trong khi close 23,30), va rai rac ca `open`. Duong
von mua-giu vi the vot len 9,19 lan roi ve 0,787, va sut giam bao ra -91,67%
tren mot cap chi di tu 19,62 den 22,32 suot 11 nam.

Bay "rau nen hong" trong `kiem()` DA dem duoc 154 bar hong cua chinh ma nay tu
truoc. Khong co gi doc no. Nen bai kiem o day khong chi kiem phep sua - no kiem
rang phep sua NAM TREN DUONG CHAY (`nap()` goi no theo mac dinh).

## Ba dieu phai giu

  1. Chuoi SACH khong duoc dong vao. Mot bo "sua" gay hon benh no chua thi te
     hon la khong co.
  2. Bien dong THAT phai song. SNB 2015-01-15 lam CHF chay 30%, Brexit 10% -
     ca hai la that va da co ghi chu trong CLAUDE.md muc 48.
  3. Sua xong thi `open`/`close` phai nam trong `[low, high]`, khong ngoai le.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import du_lieu as DL  # noqa: E402


def khung(o, h, l, c):
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                        index=pd.date_range("2020-01-01", periods=len(o), freq="D"))


def sach(n=60, gia=23.0, hat=4):
    rng = np.random.default_rng(hat)
    c = gia + np.cumsum(rng.normal(0, 0.05, n))
    o = np.r_[c[0], c[:-1]]
    return khung(o, np.maximum(o, c) + 0.05, np.minimum(o, c) - 0.05, c)


class ChuoiSACH_KhongDuocDongVAO(unittest.TestCase):
    def test_khong_sua_gi(self):
        df = sach()
        ra, bc = DL.sua_bar_hong(df)
        self.assertEqual(bc, {}, "chuoi sach ma van bao da sua: %s" % bc)
        self.assertEqual(len(ra), len(df))
        for k in ("open", "high", "low", "close"):
            np.testing.assert_allclose(ra[k].to_numpy(), df[k].to_numpy())

    def test_bien_dong_THAT_30_phan_tram_van_song(self):
        """SNB 2015-01-15: CHF chay ~30% trong mot ngay. That, phai giu."""
        df = sach(n=40, gia=1.2)
        d = df.copy()
        c = d["close"].to_numpy(float).copy()
        c[20:] *= 0.70
        d["close"] = c
        o = d["open"].to_numpy(float).copy(); o[21:] *= 0.70; d["open"] = o
        d["high"] = np.maximum(d["open"], d["close"]) + 0.01
        d["low"] = np.minimum(d["open"], d["close"]) - 0.01
        ra, bc = DL.sua_bar_hong(d)
        self.assertEqual(len(ra), len(d), "cu chay 30%% that bi bo bar")
        self.assertNotIn("khoi_phuc_thang_x10", bc)


class LechThangThapPhanPhaiDuocKHOI_PHUC(unittest.TestCase):
    def test_high_nhan_muoi_duoc_chia_lai(self):
        df = sach()
        d = df.copy()
        h = d["high"].to_numpy(float).copy()
        h[10:30] *= 10.0
        d["high"] = h
        ra, bc = DL.sua_bar_hong(d)
        self.assertEqual(bc.get("khoi_phuc_thang_x10", {}).get("high"), 20)
        np.testing.assert_allclose(ra["high"].to_numpy(), df["high"].to_numpy(),
                                   rtol=1e-9)

    def test_open_nhan_muoi_duoc_chia_lai(self):
        df = sach()
        d = df.copy()
        o = d["open"].to_numpy(float).copy()
        o[[5, 17, 33]] *= 10.0
        d["open"] = o
        ra, bc = DL.sua_bar_hong(d)
        self.assertEqual(bc.get("khoi_phuc_thang_x10", {}).get("open"), 3)
        np.testing.assert_allclose(ra["open"].to_numpy(), df["open"].to_numpy(),
                                   rtol=1e-9)

    def test_chia_muoi_cung_duoc_khoi_phuc(self):
        df = sach()
        d = df.copy()
        l = d["low"].to_numpy(float).copy()
        l[[8, 9]] /= 10.0
        d["low"] = l
        ra, bc = DL.sua_bar_hong(d)
        self.assertEqual(bc.get("khoi_phuc_thang_x10", {}).get("low"), 2)


class SauKhiSuaBarPhaiNHAT_QUAN(unittest.TestCase):
    def test_open_va_close_luon_nam_trong_bien(self):
        df = sach()
        d = df.copy()
        o = d["open"].to_numpy(float).copy()
        o[7] = d["high"].iloc[7] * 1.05          # lech 5% - khong phai x10
        d["open"] = o
        ra, bc = DL.sua_bar_hong(d)
        self.assertGreaterEqual(bc.get("kep_ve_bien", 0), 1)
        self.assertTrue(np.all(ra["open"].to_numpy() <= ra["high"].to_numpy() + 1e-12))
        self.assertTrue(np.all(ra["open"].to_numpy() >= ra["low"].to_numpy() - 1e-12))
        self.assertTrue(np.all(ra["close"].to_numpy() <= ra["high"].to_numpy() + 1e-12))
        self.assertTrue(np.all(ra["high"].to_numpy() >= ra["low"].to_numpy()))

    def test_bang_thieu_cot_khong_lam_sap(self):
        d = pd.DataFrame({"close": [1.0, 2.0, 3.0]},
                         index=pd.date_range("2020-01-01", periods=3, freq="D"))
        ra, bc = DL.sua_bar_hong(d)
        self.assertEqual(bc, {})
        self.assertEqual(len(ra), 3)


class PhepSuaPhaiNAM_TREN_DUONG_CHAY(unittest.TestCase):
    """Bo do ton tai ma khong ai goi thi bang khong co - ho benh
    `noi-day-truoc-khi-xay-them`."""

    def test_nap_mac_dinh_co_sua(self):
        import inspect
        chu_ky = inspect.signature(DL.nap).parameters
        self.assertIn("sua_bar", chu_ky)
        self.assertIs(chu_ky["sua_bar"].default, True,
                      "nap() phai sua theo MAC DINH, khong phai khi duoc nho")

    def test_tat_duoc_de_DO_do_hong(self):
        """Phai tat duoc: do do hong ma do qua ban da sua thi bao cao se rong,
        va ta se ket luan 'khong co van de' tu chinh cai vua sua."""
        try:
            a = DL.nap("EURUSD", "D1", cache=False, sua_bar=False)
            b = DL.nap("EURUSD", "D1", cache=False, sua_bar=True)
        except Exception as e:
            self.skipTest("khong co du lieu EURUSD: %s" % e)
        self.assertEqual(len(a), len(b))


if __name__ == "__main__":
    unittest.main(verbosity=2)
