# -*- coding: utf-8 -*-
"""Kiem `nhan/vao_lenh.py` va bo tinh tien open-to-open cua no.

Vi sao file nay ton tai: trong DUNG mot buoi chieu viet module do toi tu tim ra
BA loi nang bang cach doc lai, khong phai bang cach chay:

  1. DCA dat lenh STOP trong khi mua them o gia thap hon la lenh LIMIT -> moi
     bac thang khop het ngay bar dau, "DCA" thanh "vao het mot lan".
  2. OCO khop ca hai chan trong cung mot bar roi `cho.remove` lan thu hai no.
  3. Lenh cho chi song tu bar i+2 trong khi no dat duoc tu close[i].

Ba loi do khong cai nao lam chuong trinh sap. Ca ba deu chi lam con so sai -
dang hong dat nhat cua du an. Nen o day kiem CO CHE, khong kiem "chay duoc".
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import vao_lenh as VL  # noqa: E402


def khung(o, h, l, c) -> pd.DataFrame:
    n = len(o)
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                        index=pd.date_range("2020-01-01", periods=n, freq="D"))


def deu(n=60, gia=100.0, bien=1.0, hat=7):
    """Chuoi co bien do that (ATR > 0) - ATR = 0 thi `dap_cau_truc` bo qua het."""
    rng = np.random.default_rng(hat)
    c = gia + np.cumsum(rng.normal(0, bien * 0.3, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + bien * 0.5
    l = np.minimum(o, c) - bien * 0.5
    return khung(o, h, l, c)


class LenhChoPhaiKhopDungLoai(unittest.TestCase):
    def test_stop_mua_khop_khi_gia_VUOT_LEN(self):
        self.assertEqual(VL._khop_stop(1, 105, o=100, h=106, l=99), 105)
        self.assertIsNone(VL._khop_stop(1, 105, o=100, h=104, l=99))

    def test_stop_khop_o_OPEN_khi_co_khe_gia(self):
        # Bar mo 107 trong khi buy stop o 105: khop o 107, KHONG phai 105.
        self.assertEqual(VL._khop_stop(1, 105, o=107, h=108, l=106), 107)

    def test_limit_mua_khop_khi_gia_TUT_XUONG(self):
        self.assertEqual(VL._khop_limit(1, 95, o=100, h=101, l=94), 95)
        self.assertIsNone(VL._khop_limit(1, 95, o=100, h=101, l=96))

    def test_limit_va_stop_NGUOC_NHAU(self):
        """Loi da mac: dung `_khop_stop` cho bac DCA nam DUOI gia hien tai thi
        `high >= muc` luon dung -> khop ngay lap tuc."""
        self.assertIsNotNone(VL._khop_stop(1, 95, o=100, h=101, l=99))
        self.assertIsNone(VL._khop_limit(1, 95, o=100, h=101, l=99))


class ThangDCA_KhongDuocKhopHetMotLuc(unittest.TestCase):
    def test_ba_bac_khong_cung_mot_bar_khi_gia_di_LEN(self):
        # Gia chi di LEN -> khong bac DCA mua nao duoi gia vao duoc cham.
        n = 40
        c = 100 + np.arange(n) * 0.5
        o = np.r_[c[0], c[:-1]]
        df = khung(o, c + 0.3, o - 0.05, c)
        th = np.zeros(n); th[5] = 1.0
        r = VL.dap_cau_truc(df, th, "dca_deu", giu_toi_da=20)
        self.assertEqual(r["so_lenh"], 1, "chi bac dau tien duoc vao")

    def test_tong_trong_so_bang_mot(self):
        for ct in ("dca_deu", "dca_von"):
            w = VL._trong_so_nac(ct, 4, 1.5)
            self.assertAlmostEqual(float(w.sum()), 1.0, places=12,
                                   msg="%s: tong phoi nhiem phai la 1,0" % ct)

    def test_dca_von_nang_dan_chu_khong_deu(self):
        w = VL._trong_so_nac("dca_von", 3, 1.5)
        self.assertLess(w[0], w[1])
        self.assertLess(w[1], w[2])


class HedgePhaiTraTien(unittest.TestCase):
    """Loi nang nhat neu bo sot: hai chan nguoc chieu lam phoi nhiem RONG = 0,
    nen he thu 0 dong phi cho hai lenh THAT."""

    def test_khoi_luong_lon_hon_bien_thien_cua_vi_the_rong(self):
        df = deu(120)
        th = np.zeros(len(df)); th[10] = 1.0; th[40] = -1.0; th[70] = 1.0
        r = VL.dap_cau_truc(df, th, "tt_hedge", giu_toi_da=40)
        if r["so_lenh"] < 2:
            self.skipTest("chuoi nay khong kich hoat du chan")
        doi_rong = float(np.sum(np.abs(np.diff(np.concatenate(
            ([0.0], r["vi_the"]))))))
        self.assertGreater(float(r["khoi_luong"].sum()), doi_rong * 0.999,
                           "khoi luong GOP phai >= bien thien cua phoi nhiem RONG")

    def test_hai_dau_giu_co_luc_giu_ca_hai_chan(self):
        """Chuoi chu V dung san: vot LEN xuyen chan mua roi lao XUONG xuyen chan
        ban -> dung hinh dang ma cau truc hai dau bi ket ca hai."""
        n = 30
        c = np.full(n, 100.0)
        c[10:14] = [104.0, 108.0, 106.0, 103.0]
        c[14:18] = [96.0, 92.0, 95.0, 99.0]
        o = np.r_[c[0], c[:-1]]
        df = khung(o, np.maximum(o, c) + 1.0, np.minimum(o, c) - 1.0, c)
        th = np.zeros(n); th[9] = 1.0
        r = VL.dap_cau_truc(df, th, "hai_dau_giu",
                            tham={"sl_atr": 99.0, "tp_atr": 99.0, "han_bar": 10},
                            giu_toi_da=18)
        ca_hai = int(np.sum((r["dai"] > 0) & (r["ngan"] > 0)))
        self.assertGreater(ca_hai, 0, "hai_dau_giu phai co luc hedge that")


class KhongDuocNHIN_TRUOC(unittest.TestCase):
    def test_doi_tin_hieu_o_bar_CUOI_khong_lam_doi_qua_khu(self):
        df = deu(120)
        th = np.zeros(len(df)); th[20] = 1.0; th[60] = -1.0
        for ct in VL.CAU_TRUC:
            a = VL.dap_cau_truc(df, th, ct, giu_toi_da=30)
            th2 = th.copy(); th2[110] = 1.0
            b = VL.dap_cau_truc(df, th2, ct, giu_toi_da=30)
            np.testing.assert_allclose(
                a["loi_tho"][:105], b["loi_tho"][:105], atol=1e-12,
                err_msg="%s: tin hieu tuong lai lam doi qua khu" % ct)

    def test_tin_hieu_o_bar_i_khong_sinh_giao_dich_o_bar_i(self):
        df = deu(80)
        th = np.zeros(len(df)); th[30] = 1.0
        for ct in VL.CAU_TRUC:
            r = VL.dap_cau_truc(df, th, ct, giu_toi_da=20)
            self.assertEqual(float(r["khoi_luong"][:31].sum()), 0.0,
                             "%s: giao dich truoc hoac dung bar tin hieu" % ct)


class TinhTienPhaiDungTUNG_DONG(unittest.TestCase):
    def test_mot_lenh_thi_truong_giu_mot_bar(self):
        """Vao open[i+1], thoat open[i+2] -> loi phai dung bang log(o2/o1)."""
        df = deu(40)
        o = df["open"].to_numpy(float)
        th = np.zeros(len(df)); th[10] = 1.0
        r = VL.dap_cau_truc(df, th, "thi_truong",
                            tham={"sl_atr": 99.0, "tp_atr": 99.0}, giu_toi_da=1)
        self.assertAlmostEqual(float(r["loi_tho"].sum()),
                               float(np.log(o[12] / o[11])), places=10)

    def test_chieu_ban_doi_dau(self):
        df = deu(40)
        o = df["open"].to_numpy(float)
        th = np.zeros(len(df)); th[10] = -1.0
        r = VL.dap_cau_truc(df, th, "thi_truong",
                            tham={"sl_atr": 99.0, "tp_atr": 99.0}, giu_toi_da=1)
        self.assertAlmostEqual(float(r["loi_tho"].sum()),
                               -float(np.log(o[12] / o[11])), places=10)


class KhaiBaoPhaiDuocKIEM(unittest.TestCase):
    def test_cau_truc_la_phai_bao_loi(self):
        df = deu(30)
        with self.assertRaises(ValueError):
            VL.dap_cau_truc(df, np.zeros(len(df)), "khong_co_cai_nay")

    def test_tham_so_la_phai_bao_loi(self):
        df = deu(30)
        with self.assertRaises(KeyError):
            VL.dap_cau_truc(df, np.zeros(len(df)), "thi_truong",
                            tham={"go_sai_ten": 1.0})

    def test_tin_hieu_lech_do_dai_phai_bao_loi(self):
        df = deu(30)
        with self.assertRaises(ValueError):
            VL.dap_cau_truc(df, np.zeros(10), "thi_truong")


class PhiThemTrongMoPhongPhaiAnToan(unittest.TestCase):
    def test_phi_them_am_bi_tu_choi(self):
        from nhan import chi_phi as CP
        from nhan import mo_phong as MP
        df = deu(60)
        cp = CP.MoHinhChiPhi(ma="THU", spread_frac_chung=1e-4)
        with self.assertRaises(ValueError):
            MP.chay(df, np.zeros(len(df)), cp, phi_them=-np.ones(len(df)))

    def test_phi_them_lam_giam_lai(self):
        from nhan import chi_phi as CP
        from nhan import mo_phong as MP
        df = deu(60)
        cp = CP.MoHinhChiPhi(ma="THU")
        v = np.ones(len(df))
        a = MP.chay(df, v, cp)
        b = MP.chay(df, v, cp, phi_them=np.full(len(df), 1e-4))
        self.assertLess(float(np.sum(b.loi)), float(np.sum(a.loi)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
