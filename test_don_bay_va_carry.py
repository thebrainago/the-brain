# -*- coding: utf-8 -*-
"""Bai kiem cho hai lo hong tim ra 03/09/2026, ngay khi du an quay sang don bay.

1. `mo_phong.chay(don_bay=L)` gop bang LOG -> cho (S_T/S_0)^L: khong co luc can
   bien dong, khong bao gio chay tai khoan duoc.
2. `tai_tro`: lai suat tai tro va co tuc chua he duoc cap vao engine.
"""
import unittest

import numpy as np
import pandas as pd

from nhan import bien_don_bay as B
from nhan import chi_phi as CP
from nhan import mo_phong as MP
from nhan import tai_tro as TT


def _khung(r: np.ndarray, bd: float = 100.0) -> pd.DataFrame:
    gia = bd * np.exp(np.cumsum(np.concatenate(([0.0], r))))
    i = pd.date_range("2000-01-03", periods=len(gia), freq="B")
    return pd.DataFrame({"open": gia, "high": gia, "low": gia, "close": gia,
                         "volume": 1.0}, index=i)


def _rong(ma="T"):
    return CP.MoHinhChiPhi(ma=ma, do_tin="KHAI")


class GopSoHoc(unittest.TestCase):
    def test_L1_giu_nguyen_moi_con_so_cu(self):
        """Chan hoi quy: don bay 1 phai cho Y HET ban log truoc 03/09."""
        rng = np.random.default_rng(0)
        df = _khung(rng.normal(0.0003, 0.01, 3000))
        v = np.ones(len(df))
        a = MP.chay(df, v, _rong(), don_bay=1.0, da_dich=True, gop="log")
        b = MP.chay(df, v, _rong(), don_bay=1.0, da_dich=True, gop="so_hoc")
        self.assertAlmostEqual(a.von[-1], b.von[-1], places=9)

    def test_tu_dong_chon_so_hoc_khi_co_don_bay(self):
        df = _khung(np.random.default_rng(1).normal(0, 0.01, 500))
        v = np.ones(len(df))
        self.assertEqual(MP.chay(df, v, _rong(), don_bay=1.0, da_dich=True).che_do_gop, "log")
        self.assertEqual(MP.chay(df, v, _rong(), don_bay=2.0, da_dich=True).che_do_gop, "so_hoc")

    def test_luc_can_bien_dong_khong_duoc_bien_mat(self):
        """Loi goc: exp(sum(L*r)) = (S_T/S_0)^L. Phai NHO hon the."""
        rng = np.random.default_rng(2)
        df = _khung(rng.normal(0.0002, 0.015, 5000))
        v = np.ones(len(df))
        L = 3.0
        that = MP.chay(df, v, _rong(), don_bay=L, da_dich=True, gop="so_hoc").von[-1]
        luy_thua = (df["open"].iloc[-1] / df["open"].iloc[0]) ** L
        self.assertLess(that, luy_thua * 0.5,
                        "gop so hoc phai an luc can bien dong, khong duoc bang luy thua")

    def test_luc_can_khop_cong_thuc_giai_tich(self):
        """drag ~ 0,5*L*(L-1)*sigma^2 mot nam."""
        rng = np.random.default_rng(3)
        sig_ngay = 0.01
        df = _khung(rng.normal(0.0, sig_ngay, 60000))
        v = np.ones(len(df))
        L = 3.0
        n = len(df) - 1
        g1 = np.log(MP.chay(df, v, _rong(), don_bay=1.0, da_dich=True, gop="so_hoc").von[-1]) / n
        gL = np.log(MP.chay(df, v, _rong(), don_bay=L, da_dich=True, gop="so_hoc").von[-1]) / n
        drag_do = L * g1 - gL
        drag_ly = 0.5 * L * (L - 1) * sig_ngay ** 2
        self.assertAlmostEqual(drag_do, drag_ly, delta=drag_ly * 0.15)

    def test_chay_tai_khoan_duoc_phat_hien(self):
        """Mot ngay -40% o don bay 3 la chay sach. Ban log khong bao gio thay."""
        r = np.zeros(400)
        r[200] = np.log(0.60)          # -40%
        df = _khung(r)
        v = np.ones(len(df))
        k = MP.chay(df, v, _rong(), don_bay=3.0, da_dich=True, gop="so_hoc")
        self.assertTrue(k.chay_tai_khoan)
        self.assertEqual(k.von[-1], 0.0)
        self.assertTrue(any("CHAY TAI KHOAN" in c for c in k.canh_bao))
        cu = MP.chay(df, v, _rong(), don_bay=3.0, da_dich=True, gop="log")
        self.assertGreater(cu.von[-1], 0.0)   # bang cu KHONG thay - day la lo hong

    def test_phi_van_thu_theo_phoi_nhiem_o_ban_so_hoc(self):
        df = _khung(np.zeros(800))
        cp = CP.MoHinhChiPhi(ma="T", phi_nam_mua=0.05, do_tin="KHAI")
        v = np.ones(len(df))
        a = MP.chay(df, v, cp, don_bay=1.0, da_dich=True, gop="so_hoc")
        b = MP.chay(df, v, cp, don_bay=2.0, da_dich=True, gop="so_hoc")
        self.assertAlmostEqual(b.chi_phi_giu / a.chi_phi_giu, 2.0, places=6)

    def test_gop_sai_ten_thi_bao_loi(self):
        df = _khung(np.zeros(50))
        with self.assertRaises(ValueError):
            MP.chay(df, np.ones(len(df)), _rong(), gop="linh_tinh")


class DangThucTran(unittest.TestCase):
    def test_tran_va_sharpe_can_la_ham_nguoc_nhau(self):
        for s in (0.4, 0.8, 1.2):
            for k in (1.0, 0.5, 0.25):
                self.assertAlmostEqual(B.sharpe_can(B.tran_cagr(s, k), k), s, places=9)

    def test_tran_khop_engine_tren_chuoi_iid(self):
        """0,5*S^2 phai xap xi CAGR tot nhat do duoc tren chuoi i.i.d."""
        rng = np.random.default_rng(11)
        sig, muy = 0.01, 0.0004
        df = _khung(rng.normal(muy, sig, 80000))
        v = np.ones(len(df))
        hang, _ = B.do_bien(df, v, _rong(), cac_don_bay=np.arange(0.5, 8.1, 0.5),
                            co_tuc=False, da_dich=True)
        s = hang[0]["sharpe"]
        tot = max(h["cagr"] for h in hang)
        self.assertAlmostEqual(tot, B.tran_cagr(s), delta=0.25 * B.tran_cagr(s))


class Carry(unittest.TestCase):
    def test_lai_suat_lap_duoc_ca_doan_truoc_1954(self):
        """Loi 03/09: bfill chay SAU reindex -> ca doan truoc DFF ra toan NaN."""
        i = pd.date_range("1930-01-01", "1940-01-01", freq="D")
        v, tin = TT.lai_suat_nam(i)
        self.assertEqual(int(np.isnan(v).sum()), 0)
        self.assertEqual(tin, "KHAI")          # ngoai khoang do duoc

    def test_lai_suat_trong_khoang_thi_do_duoc(self):
        i = pd.date_range("2015-01-01", "2020-01-01", freq="B")
        v, tin = TT.lai_suat_nam(i)
        self.assertEqual(tin, "DO")
        self.assertTrue(0.0 <= np.nanmean(v) <= 0.10)

    def test_co_tuc_khop_muc_lich_su(self):
        """Suat co tuc SP500 theo thap ky - moc ngoai de bat thien lech."""
        d = TT.do_co_tuc()
        tb = d["suat_nam_365"].groupby((d.index.year // 10) * 10).mean()
        self.assertAlmostEqual(tb.loc[1990], 0.0258, delta=0.006)
        self.assertAlmostEqual(tb.loc[2010], 0.0209, delta=0.006)
        self.assertAlmostEqual(tb.loc[2020], 0.0156, delta=0.006)

    def test_co_tuc_khong_bi_cat_mot_chieu(self):
        """Cat tung ngay ve 0 bom thien lech DUONG - da sap that 03/09."""
        d = TT.do_co_tuc()
        self.assertLess(d["suat_nam_365"].mean(), 0.030)

    def test_carry_rong_am_khi_san_dat(self):
        i = pd.date_range("2015-01-01", "2020-01-01", freq="B")
        re, _ = TT.carry_rong_nam(i, markup_nam=0.005)
        dat, _ = TT.carry_rong_nam(i, markup_nam=0.040)
        self.assertGreater(np.nanmean(re), np.nanmean(dat))
        self.assertLess(np.nanmean(dat), 0.0)


if __name__ == "__main__":
    unittest.main()
