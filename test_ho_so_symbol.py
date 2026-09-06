# -*- coding: utf-8 -*-
"""Bai kiem cho `nhan/ho_so_symbol.py` - "co gia thuyet nay thi thu tren cai gi".

Bay da sap that trong chinh module nay: ban dau `chon_ung_vien` xep hang THUAN
theo Hurst, va no day GBPPLN (98,5 bps) va GBPZAR (20,8 bps) len dau bang - hai
cap ma phi giet moi luoi truoc khi co che kip chay. Tinh cach ma khong tra noi
phi thi vo dung.

Nen thu tu la BAT BUOC: **loc chi phi truoc, xep tinh cach sau**. Cac bai kiem
duoi day dung dat mot symbol "tinh cach hoan hao nhung phi cat co" vao va doi
no bi loai - neu ai do doi lai thu tu, no lot len hang dau ngay.

Va mot luat nua: `chi_phi_do_tin` phai la DO/SAN. `KHAI` thi khong bao gio PASS
duoc cong - de no vao danh sach ung vien la hua mot dieu khong the giu.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from nhan import ho_so_symbol as HS        # noqa: E402


def _hs(ma, hurst=0.60, nhan="XU_HUONG", spread=1.0, do_tin="SAN",
        so_nam=15.0, vong_quay=None):
    return {"ma": ma, "hurst": hurst, "nhan_tinh_cach": nhan,
            "spread_bps": spread, "chi_phi_do_tin": do_tin, "so_nam": so_nam,
            "vong_quay_toi_da": vong_quay, "atr_pct_bar": 1.0}


def _khung_gia(n=600, hat=7):
    g = np.random.default_rng(hat)
    c = 100.0 * np.exp(np.cumsum(g.normal(0, 0.01, n)))
    bd = np.abs(g.normal(0, 0.005, n)) * c
    return pd.DataFrame(
        {"open": c, "high": c + bd, "low": c - bd, "close": c},
        index=pd.date_range("2015-01-01", periods=n, freq="D"))


class LocChiPhiTruocXepTinhCachSau(unittest.TestCase):

    def test_symbol_phi_cat_co_bi_loai_du_tinh_cach_dep_nhat(self):
        """Day la ca GBPPLN. Xem docstring dau file."""
        ds = [_hs("GBPPLN", hurst=0.99, spread=98.5),
              _hs("EURUSD", hurst=0.60, spread=1.6)]
        uv = HS.chon_ung_vien(kieu="xu_huong", ho_so=ds)
        self.assertEqual([h["ma"] for h in uv], ["EURUSD"])

    def test_tran_spread_mac_dinh_chat_hon_10_bps(self):
        self.assertLessEqual(HS.TRAN_SPREAD_BPS, 10.0)
        self.assertGreater(HS.TRAN_SPREAD_BPS, 0.0)

    def test_spread_khong_biet_thi_LOAI_chu_khong_cho_qua(self):
        """None khong duoc doc thanh 're'."""
        ds = [_hs("BIETGI", spread=None)]
        self.assertEqual(HS.chon_ung_vien(kieu="bat_ky", ho_so=ds), [])

    def test_chi_phi_KHAI_bi_loai(self):
        ds = [_hs("A", do_tin="KHAI"), _hs("B", do_tin="SAN")]
        uv = HS.chon_ung_vien(kieu="bat_ky", ho_so=ds)
        self.assertEqual([h["ma"] for h in uv], ["B"])

    def test_co_the_tat_yeu_cau_chi_phi_do_duoc_khi_chi_di_tham_do(self):
        ds = [_hs("A", do_tin="KHAI")]
        uv = HS.chon_ung_vien(kieu="bat_ky", ho_so=ds, chi_phi_do_duoc=False)
        self.assertEqual([h["ma"] for h in uv], ["A"])

    def test_chuoi_qua_ngan_bi_loai(self):
        ds = [_hs("NGAN", so_nam=2.0), _hs("DAI", so_nam=20.0)]
        uv = HS.chon_ung_vien(kieu="bat_ky", ho_so=ds, so_nam_min=8.0)
        self.assertEqual([h["ma"] for h in uv], ["DAI"])

    def test_vong_quay_khong_du_thi_loai(self):
        ds = [_hs("CHAM", vong_quay=5.0), _hs("NHANH", vong_quay=500.0)]
        uv = HS.chon_ung_vien(kieu="bat_ky", ho_so=ds, vong_quay_can=100.0)
        self.assertEqual([h["ma"] for h in uv], ["NHANH"])


class XepHangTheoKieu(unittest.TestCase):

    def test_xu_huong_lay_hurst_CAO_truoc(self):
        ds = [_hs("THAP", hurst=0.55), _hs("CAO", hurst=0.70)]
        uv = HS.chon_ung_vien(kieu="xu_huong", ho_so=ds)
        self.assertEqual([h["ma"] for h in uv], ["CAO", "THAP"])

    def test_hoi_quy_lay_hurst_THAP_truoc(self):
        ds = [_hs("THAP", hurst=0.52, nhan="HOI_QUY"),
              _hs("CAO", hurst=0.70, nhan="HOI_QUY")]
        uv = HS.chon_ung_vien(kieu="hoi_quy", ho_so=ds)
        self.assertEqual([h["ma"] for h in uv], ["THAP", "CAO"])

    def test_loc_dung_nhan_tinh_cach(self):
        ds = [_hs("X", nhan="XU_HUONG"), _hs("H", nhan="HOI_QUY")]
        self.assertEqual([h["ma"] for h in HS.chon_ung_vien("hoi_quy", ho_so=ds)], ["H"])
        self.assertEqual([h["ma"] for h in HS.chon_ung_vien("xu_huong", ho_so=ds)], ["X"])

    def test_bat_ky_khong_loc_tinh_cach(self):
        ds = [_hs("X", nhan="XU_HUONG"), _hs("H", nhan="HOI_QUY")]
        self.assertEqual(len(HS.chon_ung_vien("bat_ky", ho_so=ds)), 2)

    def test_ton_trong_tran(self):
        ds = [_hs("M%02d" % i, hurst=0.6 + i / 1000) for i in range(30)]
        self.assertEqual(len(HS.chon_ung_vien("bat_ky", ho_so=ds, tran=5)), 5)


class BienDo(unittest.TestCase):

    def test_bien_do_deu_duong_va_don_vi_phan_tram(self):
        b = HS._bien_do(_khung_gia())
        for k in ("bien_dong_nam_pct", "atr_pct_bar", "bien_do_bar_pct"):
            self.assertGreater(b[k], 0.0, f"'{k}' phai duong")
            self.assertLess(b[k], 500.0, f"'{k}' co ve khong phai don vi %")

    def test_buoc_luoi_goi_y_bang_ATR(self):
        """Mot buoc luoi nen om duoc ~1 ATR - neu khong se nap tang lien tuc."""
        b = HS._bien_do(_khung_gia())
        self.assertAlmostEqual(b["buoc_goi_y_pct"], round(b["atr_pct_bar"], 4),
                               places=4)

    def test_bien_dong_nam_lon_hon_bien_dong_bar(self):
        b = HS._bien_do(_khung_gia())
        self.assertGreater(b["bien_dong_nam_pct"], b["atr_pct_bar"])


if __name__ == "__main__":
    unittest.main()
