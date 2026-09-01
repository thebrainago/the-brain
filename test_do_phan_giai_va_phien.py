# -*- coding: utf-8 -*-
"""Hai bay o TANG DU LIEU, phat hien 01/09/2026.

1. DOAN DAU DO PHAN GIAI THO. `khung_that()` lay TRUNG VI khoang cach bar tren
   ca chuoi, nen mot chuoi lai tap - vai nam dau la bar NGAY duoc terminal don
   vao, phan con lai la bar gio that - van qua duoc cua. Do tren kho nay: 5 ma
   dinh (EURUSD/USDJPY 1971-1998, GBPUSD 1993-1998, US500CASH 2011-2015,
   XAUUSDM 2014-2016), tuc ba cap FX duoc quet nhieu nhat cua du an.

2. BAR NGAY CUA CFD KHONG PHAI BAR PHIEN. Bar D1 cua mot CFD chi so om gan 23
   gio; bar phien tien mat My chi 6,5 gio. `ibs` la vi tri gia dong cua TRONG
   BIEN DO BAR nen hai cai do khong cung mot dai luong.

Bo test khoa HINH DANG cua hai luat, tren du lieu tu dung - khong phu thuoc
kho that (kho co the doi, luat thi khong duoc doi lang le).
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

from nhan import du_lieu as DL


def _khung(index) -> pd.DataFrame:
    n = len(index)
    gia = 100.0 + np.cumsum(np.full(n, 0.01))
    return pd.DataFrame({"open": gia, "high": gia + 0.5,
                         "low": gia - 0.5, "close": gia}, index=index)


def _lai_tap(so_ngay_tho: int = 400, so_gio_that: int = 3000) -> pd.DataFrame:
    """Doan dau: 1 bar/ngay. Doan sau: bar gio that. Dung hinh dang da gap."""
    tho = pd.date_range("2011-01-03", periods=so_ngay_tho, freq="B", tz="UTC")
    that = pd.date_range("2016-01-04", periods=so_gio_that, freq="h", tz="UTC")
    return _khung(tho.append(that))


class DoanDauDoPhanGiaiTho(unittest.TestCase):

    def test_bat_duoc_doan_bar_ngay_deo_nhan_bar_gio(self):
        df = _lai_tap()
        moc = DL.doan_do_phan_giai_that(df, "H1")
        self.assertIsNotNone(moc, "khong bat duoc doan dau do phan giai tho")
        self.assertEqual(moc.year, 2016)

    def test_cat_dung_doan_dau_va_bao_lai_da_cat_gi(self):
        df = _lai_tap(so_ngay_tho=400)
        ra, ghi_chu = DL.cat_doan_tho(df, "H1")
        self.assertIsNotNone(ghi_chu)
        self.assertEqual(ghi_chu["bo_bar"], 400)
        self.assertEqual(len(ra), len(df) - 400)
        self.assertGreaterEqual(ra.index.min().year, 2016)

    def test_chuoi_sach_thi_khong_cat_gi(self):
        df = _khung(pd.date_range("2016-01-04", periods=3000, freq="h", tz="UTC"))
        self.assertIsNone(DL.doan_do_phan_giai_that(df, "H1"))
        ra, ghi_chu = DL.cat_doan_tho(df, "H1")
        self.assertIsNone(ghi_chu)
        self.assertIs(ra, df)

    def test_ca_chuoi_deu_tho_thi_khong_cat(self):
        """Neu ca chuoi la bar ngay thi day la van de CHON BAN, khong phai cat.
        Cat het se tra ve bang rong va bao 'khong co du lieu' - sai nguyen nhan."""
        df = _khung(pd.date_range("2011-01-03", periods=800, freq="B", tz="UTC"))
        self.assertIsNone(DL.doan_do_phan_giai_that(df, "H1"))

    def test_D1_khong_bao_gio_bi_cat(self):
        """Luat nay chi noi ve khung TRONG NGAY. Ap len D1 thi mot chuoi ngay
        binh thuong (1 bar/ngay) se bi coi la tho va bi cat sach."""
        df = _khung(pd.date_range("2011-01-03", periods=800, freq="B", tz="UTC"))
        self.assertIsNone(DL.doan_do_phan_giai_that(df, "D1"))

    def test_khong_no_khi_tz_aware_va_khi_naive(self):
        for tz in (None, "UTC"):
            tho = pd.date_range("2011-01-03", periods=400, freq="B", tz=tz)
            that = pd.date_range("2016-01-04", periods=3000, freq="h", tz=tz)
            df = _khung(tho.append(that))
            ra, ghi_chu = DL.cat_doan_tho(df, "H1")
            self.assertIsNotNone(ghi_chu, f"tz={tz}")
            self.assertEqual(len(ra), 3000)

    def test_ten_cache_mang_dau_ban_de_khong_dung_lai_ban_cu(self):
        """Bump ten cache la phan KHONG duoc quen: cache cu van moi hon file goc
        nen se duoc dung tiep, va ban se tin la sua khong anh huong gi."""
        goc = Path(DL.__file__).read_text(encoding="utf-8")
        self.assertIn("__v2.parquet", goc)


class BarTheoPhien(unittest.TestCase):

    def _ngay_my(self, so_ngay=20, khung_phut=30):
        """Bar 24/24 UTC cho `so_ngay` ngay lam viec."""
        bd = pd.date_range("2020-06-01", periods=so_ngay, freq="B", tz="UTC")
        moc = []
        for d in bd:
            moc.append(pd.date_range(d, periods=int(1440 / khung_phut),
                                     freq=f"{khung_phut}min", tz="UTC"))
        return pd.DatetimeIndex(np.concatenate([m.to_numpy() for m in moc]))

    def test_cua_so_my_chi_giu_13_bar_M30(self):
        """09:30-16:00 = 6,5 gio = 13 bar M30. Khong hon, khong kem."""
        df = _khung(self._ngay_my())
        ra, ghi_chu = DL.gop_theo_phien(df, "my", "M30")
        self.assertEqual(ghi_chu["bar_mot_phien"], 13)
        self.assertFalse(ghi_chu["xap_xi_moc_mo"])
        self.assertEqual(len(ra), 20)

    def test_H1_khong_bat_dau_duoc_luc_0930_va_phai_noi_ra(self):
        """H1 khong chia dung 09:30. Duoc phep xap xi, KHONG duoc im lang."""
        df = _khung(self._ngay_my(khung_phut=60))
        _, ghi_chu = DL.gop_theo_phien(df, "my", "H1")
        self.assertTrue(ghi_chu["xap_xi_moc_mo"],
                        "xap xi ma khong khai bao thi bao cao doc thanh chinh xac")

    def test_ngay_qua_it_bar_bi_bo(self):
        """Mot ngay chi con vai bar thi bien do cua no khong phai bien do phien."""
        df = _khung(self._ngay_my(so_ngay=10))
        gio_my = pd.DatetimeIndex(df.index).tz_convert("America/New_York")
        phut = gio_my.hour * 60 + gio_my.minute
        ngay = pd.DatetimeIndex(gio_my).normalize()
        bo = (ngay == ngay.unique()[3]) & (phut >= 660)     # cat ngay thu 4 luc 11:00
        ra, ghi_chu = DL.gop_theo_phien(df[~bo], "my", "M30")
        self.assertEqual(ghi_chu["ngay_bo_thieu_bar"], 1)
        self.assertEqual(len(ra), 9)

    def test_mua_he_va_mua_dong_lech_mot_gio_UTC(self):
        """Cua so phien khai bao theo gio New York. Neu ai do doi sang gio UTC
        cung thi mot nua nam se lech mot tieng ma khong bao gi."""
        ph = DL.PHIEN["my"]
        self.assertEqual(ph["mui"], "America/New_York")
        he = pd.Timestamp("2020-07-01 13:30", tz="UTC").tz_convert(ph["mui"])
        dong = pd.Timestamp("2020-01-02 14:30", tz="UTC").tz_convert(ph["mui"])
        self.assertEqual((he.hour, he.minute), ph["mo"])
        self.assertEqual((dong.hour, dong.minute), ph["mo"])

    def test_bien_do_phien_hep_hon_bien_do_ca_ngay(self):
        """Ly do co ca ham nay: hai bar khong cung mot dai luong."""
        idx = self._ngay_my(so_ngay=60)
        rng = np.random.default_rng(7)
        gia = pd.Series(100 + np.cumsum(rng.normal(0, 0.05, len(idx))), index=idx)
        df = pd.DataFrame({"open": gia, "high": gia + 0.02,
                           "low": gia - 0.02, "close": gia})
        ngay = df.groupby(pd.DatetimeIndex(df.index).normalize()).agg(
            {"high": "max", "low": "min"})
        gio_my = pd.DatetimeIndex(df.index).tz_convert("America/New_York")
        phut = gio_my.hour * 60 + gio_my.minute
        trong = df[(phut >= 570) & (phut < 960)]
        phien = trong.groupby(pd.DatetimeIndex(trong.index).normalize()).agg(
            {"high": "max", "low": "min"})
        self.assertLess(float((phien["high"] - phien["low"]).median()),
                        float((ngay["high"] - ngay["low"]).median()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
