# -*- coding: utf-8 -*-
"""DAC TA: hai khuon cho `do_lech` va `doi` - hai trong nam toan hang con trong.

Bai test nay viet TRUOC phan cai dat, va phan cai dat giao cho mo hinh re.

## `do_lech` - DO LECH CHUAN, mot don vi GIA

Khong duoc so voi mot hang so: `do_lech(20) < 0,0034` la nguong cua dung mot ma
o dung mot thoi ky - dung cai bay `atr14 < 0,003472` da ghi trong `ngu_phap`
(kich hoat 1.719 lan o train, **0 lan** o holdout).

Hai duong dung duoc, ca hai deu co trong ngu phap:
  * so voi CHINH TRUNG BINH cua no - `do_lech(n) > tb(n2, cua=do_lech(n))`;
  * boc qua `phan_vi` de thanh mot ty le 0-1 roi moi so hang so.

## `doi` - THAY DOI TUYET DOI qua n bar, DAO QUANH 0

Cung don vi gia, nhung dau cua no thi khong thang do gi ca. Nen `doi(n) > 0`
hop le, con `doi(n) > 0,005` thi khong.

Luan diem giao dich cho ca hai: bien dong CO TU TUONG QUAN. Mot doan hep bat
thuong so voi chinh no thuong ket thuc bang mot cu dich manh, va do la luc phi
cua quyen chon re so voi bien dong sap toi.
"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from nhan import hephaestus as HP
from nhan import ngu_phap as NP


def _khung(n: int = 3000) -> pd.DataFrame:
    rng = np.random.default_rng(9)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    op = np.r_[c[0], c[:-1]]
    return pd.DataFrame(
        {"open": op, "high": np.maximum(c, op) * 1.002,
         "low": np.minimum(c, op) * 0.998, "close": c,
         "tick_volume": rng.integers(50, 500, n) * 1.0},
        index=pd.date_range("2020-01-01", periods=n, freq="h"))


class _Chung:
    """Doi hoi chung cho ca hai khuon - viet mot lan, dung hai lan."""

    khuon = ""
    toan_hang = ""

    def setUp(self):
        self.ds = HP.duc(han_ngach=100000, khuon=self.khuon)
        self.df = _khung()

    def test_co_trong_danh_sach_khuon(self):
        self.assertIn(self.khuon, [t for t, _ in HP.KHUON])

    def test_de_ra_duoc_co_che(self):
        self.assertGreaterEqual(len(self.ds), 2)

    def test_deu_dung_dung_toan_hang_do(self):
        for s in self.ds:
            t = set()
            HP._chi_bao_trong(s["vao"], t)
            self.assertIn(self.toan_hang, t, s["ten"])

    def test_qua_duoc_cong_cu_phap(self):
        for s in self.ds:
            self.assertEqual(NP.kiem_khai_bao(s), [], s["ten"])

    def test_qua_duoc_cong_THANG_DO_cua_may_de(self):
        for s in self.ds:
            for d in s["vao"]:
                self.assertTrue(HP._hop_thang(d), "%s: %s" % (s["ten"], d))

    def test_chay_that_va_RA_TIN_HIEU(self):
        for s in self.ds:
            th = NP.sinh_tu_spec(s, self.df)
            self.assertEqual(len(th), len(self.df), s["ten"])
            ty = float(np.mean(np.abs(th) > 1e-12))
            self.assertGreater(ty, 0.0, "%s: khong bao gio kich hoat" % s["ten"])
            self.assertLess(ty, 1.0, "%s: kich hoat 100%% so bar" % s["ten"])

    def test_nam_trong_lo_chung_va_khong_trung_van_tay(self):
        het = HP.duc(han_ngach=100000)
        ten = {s["ten"] for s in het}
        for s in self.ds:
            self.assertIn(s["ten"], ten)
        vt = [NP.van_tay_dieu_kien(s) for s in het]
        self.assertEqual(len(vt), len(set(vt)))


class KhuonDoLech(_Chung, unittest.TestCase):
    khuon = "bien_dong_do_lech"
    toan_hang = "do_lech"

    def test_KHONG_so_do_lech_voi_hang_so_khac_0(self):
        """Nguong theo don vi gia chi dung cho MOT ma o MOT thoi ky."""
        for s in self.ds:
            for d in s["vao"]:
                p = d.get("phai") or {}
                if "hang" not in p:
                    continue
                if HP.thang_do(d["trai"]) == HP.THANG_GIA:
                    self.assertEqual(float(p["hang"]), 0.0, s["ten"])


class KhuonDoi(_Chung, unittest.TestCase):
    khuon = "doi_tuyet_doi"
    toan_hang = "doi"

    def test_chi_dung_DAU_cua_doi(self):
        """`doi` dao quanh 0: `doi(n) > 0` hop le, `doi(n) > 0,005` thi khong."""
        for s in self.ds:
            for d in s["vao"]:
                p = d.get("phai") or {}
                t = d.get("trai") or {}
                if "hang" in p and str(t.get("chi_bao")) == "doi":
                    self.assertEqual(float(p["hang"]), 0.0, s["ten"])
