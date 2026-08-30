# -*- coding: utf-8 -*-
"""DON BAY trong engine — va vi sao truoc do KHONG lam duoc.

Do 30/08/2026 khi tra loi cau hoi "cong co loai bo phung phi khong".

Cong 1 doi he THANG TONG LAI cua mua-giu. Nhung he chon loc (V6/IBS) chi o
trong thi truong **16,6%** thoi gian, con moc o **100%**. So tong lai cua hai
thu do khong phai so cung don vi — va tren mot tai san co xu huong tang, cong
1 tro thanh BAT KHA voi moi chien luoc chon loc.

Cau hoi dung la: *cung mot muc rui ro thi ben nao lai hon?* De hoi duoc cau do
phai dua duoc he len dung do bien dong cua moc. Truoc hom nay **khong lam
duoc**: `chay()` cat tin hieu ve [-1, 1] ngay dau ham, nen nhan tin hieu len
1,55 lan roi chay lai cho ket qua **GIONG HET** ban goc (41,26% = 41,26%) —
khong mot canh bao nao. Trieu chung nhin tu ngoai la "khop rui ro khong doi gi
ca", trong khi that ra phep nhan chua bao gio ton tai.

Tran +-1 GIU NGUYEN va van la tam chan: mot template loi tra ve 50 se che ra
loi suat 50 lan. Vi vay don bay la tham so NGUOI GOI khai ro, ap SAU khi cat.
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

from nhan import chi_phi as CP      # noqa: E402
from nhan import mo_phong as MP     # noqa: E402


def _gia(n: int = 900, hat: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(hat)
    c = 100.0 * np.exp(np.cumsum(rng.normal(0.0004, 0.008, n)))
    o = np.concatenate([[100.0], c[:-1]])
    b = np.abs(rng.normal(0.0, 0.003, n)) * c
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c) + b,
         "low": np.minimum(o, c) - b, "close": c},
        index=pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC"))


def _cp() -> CP.MoHinhChiPhi:
    return CP.MoHinhChiPhi(ma="TEST", spread_frac_chung=0.00008,
                           truot_gia_frac=0.00002, phi_nam_mua=0.04,
                           phi_nam_ban=0.0, do_tin="KHAI")


class TranVanLaTamChan(unittest.TestCase):
    """Tran +-1 khong duoc go: no chan template tra ve so bay."""

    def test_template_tra_ve_50_van_bi_cat_ve_1(self):
        df, cp = _gia(), _cp()
        v = np.zeros(len(df)); v[10:200] = 50.0
        w = np.zeros(len(df)); w[10:200] = 1.0
        self.assertAlmostEqual(
            float(np.nansum(MP.chay(df, v, cp).loi)),
            float(np.nansum(MP.chay(df, w, cp).loi)),
            places=12,
            msg="tin hieu 50 khong bi cat ve 1 -> template loi che ra loi suat 50 lan")

    def test_don_bay_khong_phai_thu_template_tu_gianh_duoc(self):
        """Cat TRUOC roi nhan SAU: 50 x don_bay 1 van la 1, khong phai 50."""
        df, cp = _gia(), _cp()
        v = np.zeros(len(df)); v[10:200] = 50.0
        a = MP.chay(df, v, cp, don_bay=1.0)
        b = MP.chay(df, np.clip(v, -1, 1), cp, don_bay=1.0)
        self.assertAlmostEqual(float(np.nansum(a.loi)), float(np.nansum(b.loi)),
                               places=12)


class DonBayThucSuDOIKetQua(unittest.TestCase):
    """Chinh ca bai da sap: nhan len ma ket qua y het la loi im lang."""

    def test_don_bay_2_cho_ket_qua_KHAC_don_bay_1(self):
        df, cp = _gia(), _cp()
        v = np.zeros(len(df)); v[10:400] = 1.0
        a = np.nansum(MP.chay(df, v, cp, don_bay=1.0).loi)
        b = np.nansum(MP.chay(df, v, cp, don_bay=2.0).loi)
        self.assertNotAlmostEqual(
            float(a), float(b), places=6,
            msg="don bay 2 cho ket qua y het don bay 1 - phep nhan khong ton tai")

    def test_phoi_nhiem_TB_tang_dung_ty_le(self):
        df, cp = _gia(), _cp()
        v = np.zeros(len(df)); v[10:400] = 1.0
        p1 = float(np.mean(np.abs(MP.chay(df, v, cp, don_bay=1.0).vi_the)))
        p2 = float(np.mean(np.abs(MP.chay(df, v, cp, don_bay=2.0).vi_the)))
        self.assertAlmostEqual(p2, 2.0 * p1, places=9)

    def test_don_bay_1_giu_nguyen_hanh_vi_cu(self):
        """Chong hoi quy: mac dinh phai y het truoc khi co tham so nay."""
        df, cp = _gia(), _cp()
        v = np.zeros(len(df)); v[5:300] = 1.0; v[400:500] = -1.0
        a = MP.chay(df, v, cp)
        b = MP.chay(df, v, cp, don_bay=1.0)
        self.assertAlmostEqual(float(np.nansum(a.loi)), float(np.nansum(b.loi)),
                               places=12)


class PhiCuaPhanDONBAYPhaiBiThU(unittest.TestCase):
    """Don bay khong duoc la bua an tien: phi phai tang theo."""

    def test_phi_qua_dem_tang_khi_don_bay_tang(self):
        df, cp = _gia(), _cp()
        v = np.zeros(len(df)); v[10:600] = 1.0
        a = MP.chay(df, v, cp, don_bay=1.0)
        b = MP.chay(df, v, cp, don_bay=2.0)
        self.assertGreater(
            float(np.nansum(b.chi_phi_giu)), float(np.nansum(a.chi_phi_giu)) * 1.5,
            "phi qua dem khong tang theo don bay -> don bay thanh tien mien phi")

    def test_spread_tang_khi_don_bay_tang(self):
        df, cp = _gia(), _cp()
        v = np.zeros(len(df)); v[10:600] = 1.0
        a = MP.chay(df, v, cp, don_bay=1.0)
        b = MP.chay(df, v, cp, don_bay=2.0)
        self.assertGreater(float(np.nansum(b.chi_phi_spread)),
                           float(np.nansum(a.chi_phi_spread)) * 1.5)

    def test_lai_KHONG_tang_dung_gap_doi_vi_phi_an_bot(self):
        """Neu lai x2 chinh xac thi phi dang khong duoc thu."""
        df, cp = _gia(), _cp()
        v = np.zeros(len(df)); v[10:600] = 1.0
        a = float(np.nansum(MP.chay(df, v, cp, don_bay=1.0).loi))
        b = float(np.nansum(MP.chay(df, v, cp, don_bay=2.0).loi))
        if a > 0:
            self.assertLess(b, 2.0 * a, "don bay x2 cho lai dung x2 - phi bi bo qua")


class TuChoiDonBayVoNghia(unittest.TestCase):

    def test_don_bay_am_hoac_0_hoac_NaN_thi_bao_loi(self):
        df, cp = _gia(), _cp()
        v = np.zeros(len(df)); v[10:100] = 1.0
        for x in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(don_bay=x):
                with self.assertRaises(ValueError):
                    MP.chay(df, v, cp, don_bay=x)


if __name__ == "__main__":
    unittest.main()


class PhiGiuPhaiTheoDOLONKhongChiTheoCHIEU(unittest.TestCase):
    """`phi_giu_mang` tung cat phoi nhiem ve <=1 truoc khi tinh phi.

    Do that 30/08/2026 ngay khi them `don_bay`: don bay x2 tra phi qua dem
    **y het** x1 (0,0647 ca hai). Khong ai thay truoc do vi `chay()` cung cat
    tin hieu ve [-1, 1] — hai cai chan chong len nhau, va cai thu hai chi lo ra
    khi cai thu nhat duoc go.

    Neu de nguyen thi don bay tro thanh TIEN MIEN PHI: nhan phoi nhiem len bao
    nhieu cung duoc ma phan tra lai san khong doi. Do la dung hinh dang cua moi
    ket qua backtest gia ma du an nay da gap.
    """

    def test_phi_giu_ty_le_thuan_voi_do_lon_phoi_nhiem(self):
        from nhan import chi_phi as CP2
        idx = pd.date_range("2021-01-01", periods=300, freq="D", tz="UTC")
        cp = _cp()
        v1 = np.ones(len(idx)); v2 = np.ones(len(idx)) * 2.0
        a = float(np.nansum(cp.phi_giu_mang(idx, v1)))
        b = float(np.nansum(cp.phi_giu_mang(idx, v2)))
        self.assertAlmostEqual(b, 2.0 * a, places=12,
                               msg="phi giu khong ty le voi do lon vi the")

    def test_phoi_nhiem_trong_khoang_cu_KHONG_doi_mot_chut_nao(self):
        """Chong hoi quy: |v| <= 1 phai cho ket qua y het ban truoc."""
        from nhan import chi_phi as CP2
        rng = np.random.default_rng(9)
        idx = pd.date_range("2021-01-01", periods=400, freq="D", tz="UTC")
        cp = _cp()
        v = rng.uniform(-1.0, 1.0, len(idx))
        moi = cp.phi_giu_mang(idx, v)
        cu = (np.clip(v, 0, 1) * cp.phi_nam_mua
              + np.clip(-v, 0, 1) * cp.phi_nam_ban)
        from nhan.chi_phi import hinh_hoc
        cu = cu * hinh_hoc(idx)[0] / 365.0
        self.assertTrue(np.allclose(moi, cu, atol=1e-15),
                        "doi hanh vi o vung |v| <= 1 - day la hoi quy")
