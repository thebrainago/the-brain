# -*- coding: utf-8 -*-
"""Kiem toan hang `mau_nen` - cac dang nen hop thanh.

## Vi sao no ra doi 12/09/2026

So do he thong co mot dong nguyen: *"Cac dang nen khac nhau"*. Ngu phap co
`than_nen`, `bien_do`, `ibs`, `dem_lien_tiep` - du de noi TUNG MANH cua mot mau
nen nhung khong noi duoc MAU NEN. Hau qua do duoc: 41 co che ten "nen" + 20
"candle" + 10 "engulf" trong kho deu la ban NHAP TU NGOAI, con bo sinh noi sinh
chua bao gio tu dat ra mot mau nen nao. Mot dong cua so do chua tung duoc quet.

## Hai tinh chat phai giu, va ca hai deu de mat

**1. KHONG NHIN TRUOC.** `nhan_chim` va `trong`/`ngoai` doc bar TRUOC (`shift(1)`).
Viet nham thanh `shift(-1)` thi mau nen se "biet" bar sau - va no se trong nhu
vang trong moi bang xep hang.

**2. CHUAN HOA THEO BIEN DO.** "Than nen dai" la dai so voi cai gi? Moi nguong
o day deu chia cho bien do cua chinh bar, nen mot mau nen dinh nghia tren EURUSD
dung y nguyen tren XAUUSD. Mot mau nen khai bang so pip la mau nen cua MOT tai
san, khong phai mot mau nen.
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


def bar(o, h, l, c):
    n = len(o)
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                        index=pd.date_range("2020-01-01", periods=n, freq="D"))


def lay(df, mau):
    return NP.toan_hang(df, {"chi_bao": "mau_nen", "mau": mau}).to_numpy(float)


class MauDUNG_NHU_TEN(unittest.TestCase):
    def test_nhan_chim_tang(self):
        # bar 0 giam nho, bar 1 tang TRUM len
        df = bar([10.0, 9.0], [10.2, 11.0], [9.3, 8.8], [9.5, 10.5])
        v = lay(df, "nhan_chim")
        self.assertGreater(v[1], 0, "khong nhan ra nhan chim TANG")

    def test_nhan_chim_giam_ra_dau_AM(self):
        df = bar([9.0, 10.5], [10.2, 10.8], [8.8, 8.5], [10.0, 8.8])
        v = lay(df, "nhan_chim")
        self.assertLess(v[1], 0, "nhan chim GIAM phai ra dau am")

    def test_khong_trum_thi_khong_phai_nhan_chim(self):
        df = bar([10.0, 9.6], [10.2, 9.9], [9.3, 9.5], [9.5, 9.8])
        self.assertEqual(lay(df, "nhan_chim")[1], 0.0)

    def test_bar_cung_chieu_khong_phai_nhan_chim(self):
        """Nhan chim phai DOI CHIEU. Hai bar cung tang ma bar sau to hon chi la
        mot bar to hon."""
        df = bar([9.0, 8.8], [10.2, 11.5], [8.8, 8.5], [10.0, 11.0])
        self.assertEqual(lay(df, "nhan_chim")[1], 0.0)

    def test_trong_va_ngoai_nguoc_nhau(self):
        trong_df = bar([10.0, 10.1], [11.0, 10.6], [9.0, 9.6], [10.5, 10.3])
        ngoai_df = bar([10.0, 10.1], [11.0, 12.0], [9.0, 8.0], [10.5, 11.5])
        self.assertGreater(lay(trong_df, "trong")[1], 0)
        self.assertEqual(lay(trong_df, "ngoai")[1], 0.0)
        self.assertNotEqual(lay(ngoai_df, "ngoai")[1], 0.0)
        self.assertEqual(lay(ngoai_df, "trong")[1], 0.0)

    def test_bua_co_rau_duoi_dai(self):
        # than nho o tren, rau duoi rat dai
        df = bar([10.0], [10.2], [8.0], [10.1])
        self.assertGreater(lay(df, "bua")[0], 0.5)

    def test_sao_bang_nguoc_voi_bua(self):
        df = bar([10.0], [12.0], [9.9], [10.1])
        self.assertGreater(lay(df, "sao_bang")[0], 0.5)
        self.assertLess(lay(df, "bua")[0], 0)

    def test_doji_than_cang_nho_diem_cang_cao(self):
        deo = bar([10.0], [10.5], [9.5], [10.01])
        day = bar([10.0], [10.5], [9.5], [10.45])
        self.assertGreater(lay(deo, "doji")[0], lay(day, "doji")[0])

    def test_ba_nen_can_dung_ba_bar_cung_chieu(self):
        tang = bar([10.0, 10.8, 11.6], [10.9, 11.7, 12.5], [9.9, 10.7, 11.5],
                   [10.8, 11.6, 12.4])
        self.assertGreater(lay(tang, "ba_nen")[2], 0)
        lat = bar([10.0, 10.8, 12.4], [10.9, 11.7, 12.5], [9.9, 10.7, 11.5],
                  [10.8, 11.6, 11.6])
        self.assertEqual(lay(lat, "ba_nen")[2], 0.0)


class ChuanHoaTheoBIEN_DO(unittest.TestCase):
    def test_doi_THANG_DO_gia_khong_lam_doi_mau(self):
        """Nhan ca bang gia len 100 lan = doi tai san. Mau nen phai y nguyen."""
        df = bar([10.0, 9.0], [10.2, 11.0], [9.3, 8.8], [9.5, 10.5])
        to = bar(*[[x * 137.0 for x in col] for col in
                   ([10.0, 9.0], [10.2, 11.0], [9.3, 8.8], [9.5, 10.5])])
        for mau in NP.MAU_NEN:
            a, b = lay(df, mau), lay(to, mau)
            k = np.isfinite(a) & np.isfinite(b)
            np.testing.assert_allclose(a[k], b[k], atol=1e-9,
                                       err_msg="mau '%s' phu thuoc THANG DO gia"
                                               % mau)


class KhongDuocNHIN_TRUOC(unittest.TestCase):
    def test_doi_bar_sau_khong_lam_doi_mau_truoc(self):
        rng = np.random.default_rng(4)
        n = 200
        c = 100 + np.cumsum(rng.normal(0, 0.5, n))
        o = np.r_[c[0], c[:-1]]
        h = np.maximum(o, c) + 0.3
        l = np.minimum(o, c) - 0.3
        df = bar(o, h, l, c)
        d2 = df.copy()
        for k in ("open", "high", "low", "close"):
            v = d2[k].to_numpy(float).copy(); v[150:] *= 1.7; d2[k] = v
        for mau in NP.MAU_NEN:
            a, b = lay(df, mau)[:140], lay(d2, mau)[:140]
            k = np.isfinite(a) & np.isfinite(b)
            np.testing.assert_allclose(a[k], b[k], atol=1e-9,
                                       err_msg="mau '%s' NHIN TRUOC" % mau)


class KhaiBaoSaiPhaiNEM(unittest.TestCase):
    def test_mau_la_bi_tu_choi(self):
        df = bar([10.0], [10.5], [9.5], [10.2])
        with self.assertRaises(KeyError):
            NP.toan_hang(df, {"chi_bao": "mau_nen", "mau": "khong_co_mau_nay"})

    def test_moi_mau_trong_danh_sach_deu_chay_duoc(self):
        rng = np.random.default_rng(9)
        n = 120
        c = 100 + np.cumsum(rng.normal(0, 0.4, n))
        o = np.r_[c[0], c[:-1]]
        df = bar(o, np.maximum(o, c) + 0.2, np.minimum(o, c) - 0.2, c)
        for mau in NP.MAU_NEN:
            v = lay(df, mau)
            self.assertEqual(len(v), n, mau)
            self.assertTrue(np.isfinite(v[5:]).any(), "mau '%s' toan NaN" % mau)


if __name__ == "__main__":
    unittest.main(verbosity=2)
