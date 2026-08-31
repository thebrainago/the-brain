# -*- coding: utf-8 -*-
"""KHE GIA O MOC DAO NGAY — hien vat da suyt tro thanh mot phat hien.

Do 30/08/2026 tren FX H4 cua kho nay, khe gia giua bar truoc va bar nay:

      gio   EURGBP   EURCAD   AUDCAD
        0   -3,158   -2,474   -4,609      <- bar 00:00
        4   +0,009   -0,001   -0,005
        8   +0,010   +0,011   -0,003
       12   -0,018   -0,016   -0,010
       16   +0,008   +0,007   +0,005
       20   +0,001   +0,001   -0,012      (don vi: bps)

Bar 00:00 MO THAP gia tao roi "hoi" trong than bar. Moi gio khac ~0. Do la
bao gia luc dao ngay: thanh khoan mong, chenh mua/ban gian rong.

Ai om dung bar do thi MUA O GIA MO BIA va BAN O GIA DONG THAT: +5,78 bps moi
ngay ~ **14%/nam hien vat thuan**, lon hon moi edge that trong du an nay.

`EURGBP.H4.mua_qua_dem` dat **t_alpha = 14,52**, qua het cong re, va la mot
trong hai ung vien duy nhat song sot sau khi sua cong 1. **Khong mot cong nao
trong muoi cong nhin thay no.** Luat cua du an ("t_alpha > 5 = nghi nhin
truoc") la thu duy nhat bao dong, va no chi bao dong cho NGUOI doc.

Cai bay o day khong phai nhin truoc va khong phai qua khop: du lieu that,
engine dung, khong mot dong ma nao sai. Chi la gia MO cua mot bar khong phai
gia ai giao dich duoc.
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

from nhan import du_lieu as DL   # noqa: E402


def _khung(n_ngay=400, khe_gio=None, khe_bps=0.0, hat=3):
    """Chuoi H4 sach, tuy chon nhet mot khe gia vao dung mot gio."""
    rng = np.random.default_rng(hat)
    idx = pd.date_range("2021-01-01", periods=n_ngay * 6, freq="4h", tz="UTC")
    c = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.0015, len(idx))))
    o = np.concatenate([[100.0], c[:-1]]).copy()
    if khe_gio is not None:
        m = idx.hour == khe_gio
        o[m] = o[m] * (1.0 + khe_bps / 1e4)
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.0005,
                         "low": np.minimum(o, c) * 0.9995, "close": c}, index=idx)


def _khung_ngay(n_ngay=600, khe_thu=None, khe_bps=0.0, hat=5):
    """Chuoi D1 sach, tuy chon nhet mot khe gia vao dung mot THU trong tuan."""
    rng = np.random.default_rng(hat)
    idx = pd.date_range("2019-01-01", periods=n_ngay, freq="D", tz="UTC")
    c = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.004, len(idx))))
    o = np.concatenate([[100.0], c[:-1]]).copy()
    if khe_thu is not None:
        m = idx.dayofweek == khe_thu
        o[m] = o[m] * (1.0 + khe_bps / 1e4)
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.0005,
                         "low": np.minimum(o, c) * 0.9995, "close": c}, index=idx)


class KhungNgayDoTheoTHU(unittest.TestCase):
    """Truoc 31/08/2026 ham chi biet nhom theo GIO, nen tren D1 no thay dung mot
    gio va tra `do_duoc=False`: moi ung vien khung ngay di qua cong 11 ma khong
    bi kiem hien vat nao. Tren khung ngay o thoi gian tuong duong la THU."""

    def test_khung_ngay_DO_DUOC(self):
        r = DL.khe_gio_bat_thuong(_khung_ngay())
        self.assertTrue(r["do_duoc"], "khung ngay van bao 'chua do duoc'")
        self.assertEqual(r["theo"], "thu")

    def test_bat_duoc_khe_cuoi_tuan(self):
        r = DL.khe_gio_bat_thuong(_khung_ngay(khe_thu=0, khe_bps=-4.0))
        self.assertEqual(r["theo"], "thu")
        self.assertEqual(r["gio"], [0])
        self.assertLess(r["khe_bps"][0], -3.0)

    def test_chuoi_ngay_SACH_khong_bi_gan_co(self):
        for hat in range(6):
            r = DL.khe_gio_bat_thuong(_khung_ngay(hat=hat))
            self.assertEqual(r["gio"], [], f"bao dong gia o hat {hat}")

    def test_khung_gio_van_do_theo_GIO(self):
        r = DL.khe_gio_bat_thuong(_khung(khe_gio=0, khe_bps=-3.0))
        self.assertEqual(r["theo"], "gio")


class CongChanDungTHUTrenKhungNgay(unittest.TestCase):
    """Cong 11 phai lay dung truc thoi gian ma phep do da dung. Lay nham
    `index.hour` tren D1 thi mat na toan True -> khong bao gio chan duoc."""

    def setUp(self):
        from nhan import chi_phi as CP, mo_phong as MP
        self.df = _khung_ngay(khe_thu=0, khe_bps=-6.0)
        self.cp = CP.MoHinhChiPhi(ma="T", spread_frac_chung=0.0,
                                  truot_gia_frac=0.0, phi_nam_mua=0.0,
                                  phi_nam_ban=0.0, do_tin="SAN")
        self.MP = MP

    def _xet(self, v):
        from nhan import cong as CONG
        kq = self.MP.chay(self.df, v, self.cp, ma="T", khung="D1")
        bh = self.MP.mua_giu(self.df, self.cp, ma="T", khung="D1")
        return CONG.xet(self.df, kq, bh, self.cp, gt_ma="T.d1", ho="kiem",
                        da_dang_ky=True, tren_holdout=True,
                        chay_placebo=False, ghi_so=False)

    def test_om_dung_bar_co_khe_bi_loai(self):
        # giu tu thu 6 (index.dayofweek == 4) sang -> vi the nam o bar thu 2
        v = (np.asarray(self.df.index.dayofweek) == 6).astype(float)
        kt = self._xet(v)
        self.assertFalse(kt["dieu_kien"]["11_khong_an_khe_dao_ngay"],
                         "chien luoc om dung bar co khe cuoi tuan van di qua")

    def test_trai_deu_khong_bi_loai(self):
        kt = self._xet(np.ones(len(self.df)))
        self.assertTrue(kt["dieu_kien"]["11_khong_an_khe_dao_ngay"],
                        "chan ca nguon thay vi chan chien luoc an khe")

class BatDuocKheThat(unittest.TestCase):

    def test_bat_duoc_khe_am_o_dung_mot_gio(self):
        r = DL.khe_gio_bat_thuong(_khung(khe_gio=0, khe_bps=-3.0))
        self.assertTrue(r["do_duoc"])
        self.assertEqual(r["gio"], [0])

    def test_bat_duoc_ca_khe_DUONG(self):
        """Khe duong cung bia y het khe am - dau khong quan trong."""
        r = DL.khe_gio_bat_thuong(_khung(khe_gio=12, khe_bps=+4.0))
        self.assertEqual(r["gio"], [12])

    def test_do_lon_khe_duoc_ghi_lai_de_nguoi_doc_kiem(self):
        r = DL.khe_gio_bat_thuong(_khung(khe_gio=8, khe_bps=-5.0))
        self.assertIn(8, r["khe_bps"])
        self.assertLess(r["khe_bps"][8], -3.0)


class KHONGBaoDongTrenChuoiSACH(unittest.TestCase):
    """Chieu nguoc lai. Mot bo do luon keu la mot bo do vo dung."""

    def test_chuoi_sach_khong_bi_gan_co_nao(self):
        for hat in range(6):
            with self.subTest(hat=hat):
                r = DL.khe_gio_bat_thuong(_khung(hat=hat))
                self.assertEqual(r["gio"], [],
                                 f"bao dong gia tren chuoi sach: {r['khe_bps']}")

    def test_khe_NHO_hon_san_tuyet_doi_thi_bo_qua(self):
        """0,3 bps gap 10 lan cac gio khac nhung khong du de che ra edge."""
        r = DL.khe_gio_bat_thuong(_khung(khe_gio=4, khe_bps=-0.3))
        self.assertNotIn(4, r["gio"])


class ChuaDoDuocKHONGPhaiLaSach(unittest.TestCase):
    """Bai hoc dat nhat cua du an: `n=0` la 'chua do', khong phai 'khong co'."""

    def test_khung_NGAY_do_duoc_nho_nhom_theo_THU(self):
        """Da doi 31/08/2026. Truoc do khung ngay tra `do_duoc=False` - dung nghia
        la "chua do duoc", nhung KHONG AI doc dong do, nen moi ung vien D1 thuc te
        di qua cong 11 khong bi kiem gi. Gio no nhom theo THU va do duoc that."""
        idx = pd.date_range("2020-01-01", periods=800, freq="D", tz="UTC")
        c = 100.0 * np.exp(np.cumsum(np.random.default_rng(1).normal(0, .01, 800)))
        o = np.concatenate([[100.0], c[:-1]])
        df = pd.DataFrame({"open": o, "high": c * 1.01, "low": c * .99,
                           "close": c}, index=idx)
        r = DL.khe_gio_bat_thuong(df)
        self.assertTrue(r["do_duoc"])
        self.assertEqual(r["theo"], "thu")
        self.assertEqual(r["gio"], [], "chuoi sach ma bi gan co")

    def test_QUA_IT_BAR_van_la_chua_do_duoc(self):
        """Chieu con lai cua cung mot cau: thieu bar thi van phai noi 'chua do
        duoc', khong duoc im lang thanh 'sach'."""
        idx = pd.date_range("2020-01-01", periods=120, freq="D", tz="UTC")
        c = 100.0 + np.arange(120) * 0.01
        df = pd.DataFrame({"open": c, "high": c * 1.01, "low": c * .99,
                           "close": c}, index=idx)
        r = DL.khe_gio_bat_thuong(df)
        self.assertFalse(r["do_duoc"])
        self.assertEqual(r["gio"], [])
        self.assertEqual(r["gio"], [])

    def test_qua_it_bar_tra_do_duoc_False(self):
        r = DL.khe_gio_bat_thuong(_khung(n_ngay=10))
        self.assertFalse(r["do_duoc"])


class CongChanDUNGChienLuocAnKhe(unittest.TestCase):
    """Chan CHINH XAC, khong chan ca nguon."""

    def setUp(self):
        from nhan import chi_phi as CP, mo_phong as MP
        self.df = _khung(khe_gio=0, khe_bps=-4.0)
        self.cp = CP.MoHinhChiPhi(ma="T", spread_frac_chung=0.00002,
                                  truot_gia_frac=0.0, phi_nam_mua=0.0,
                                  phi_nam_ban=0.0, do_tin="SAN")
        self.MP = MP

    def _xet(self, v):
        from nhan import cong as CONG
        kq = self.MP.chay(self.df, v, self.cp, ma="T", khung="H4")
        bh = self.MP.mua_giu(self.df, self.cp, ma="T", khung="H4")
        return CONG.xet(self.df, kq, bh, self.cp, gt_ma="T.x", ho="kiem",
                        da_dang_ky=True, tren_holdout=True,
                        chay_placebo=False, ghi_so=False)

    def test_chien_luoc_DON_vao_gio_ban_bi_loai(self):
        v = (np.asarray(self.df.index.hour) == 20).astype(float)  # -> giu gio 0
        kt = self._xet(v)
        self.assertFalse(kt["dieu_kien"]["11_khong_an_khe_dao_ngay"],
                         "chien luoc om dung bar co khe van di qua")

    def test_chien_luoc_TRAI_DEU_khong_bi_loai(self):
        v = np.ones(len(self.df))
        kt = self._xet(v)
        self.assertTrue(kt["dieu_kien"]["11_khong_an_khe_dao_ngay"],
                        "chan ca nguon thay vi chan chien luoc an khe")

    def test_chien_luoc_NE_gio_ban_khong_bi_loai(self):
        g = np.asarray(self.df.index.hour)
        v = (g != 20).astype(float)
        kt = self._xet(v)
        self.assertTrue(kt["dieu_kien"]["11_khong_an_khe_dao_ngay"])

    def test_chuoi_SACH_thi_dieu_kien_11_luon_dat(self):
        self.df = _khung()
        for v in (np.ones(len(self.df)),
                  (np.asarray(self.df.index.hour) == 0).astype(float)):
            kt = self._xet(v)
            self.assertTrue(kt["dieu_kien"]["11_khong_an_khe_dao_ngay"],
                            "loai oan tren chuoi khong co khe")


if __name__ == "__main__":
    unittest.main()
