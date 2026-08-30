# -*- coding: utf-8 -*-
"""KHOP RUI RO o cong 1 — va bai kiem chieu nguoc lai.

Cong 1 tung so TONG LAI cua he voi mua-giu. He chon loc chi o trong thi truong
16-18% thoi gian con moc o 100%: khong phai so cung don vi. Do that 30/08/2026
tren US500M.D1 — chan IBS cua V6 co Sharpe 0,992 / Calmar 0,961 (moc 0,885 /
0,756), qua cong 2 va 3, chet o cong 1 vi 33,2% < 48,5%.

**Nhung noi long mot cong la huong nguy hiem nhat co the di.** Vi vay phan lon
file nay khong kiem "V6 qua duoc" — no kiem **cong van tu choi nhung thu dang
bi tu choi**, va kiem rang phep nhan khong tro thanh mot cach de bien mot he
te thanh mot he tot.

Ba duong lach da duoc bit, moi duong mot lop:
  1. He co bien dong thap nhung duoi trai day -> `min(k_bien_dong, k_sut_giam)`
  2. He khong the nhan len ma khong chay tai khoan -> `k = None`
  3. He thua tien -> nhan len chi lam thua nhieu hon (phep nhan khong doi dau)
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

from nhan import cong as CONG   # noqa: E402


def _gop(r, k=1.0):
    r = np.asarray(r, dtype=float)
    return float(np.prod(1.0 + k * r) - 1.0)


def _dd(r, k=1.0):
    e = np.cumprod(1.0 + k * np.asarray(r, dtype=float))
    return float((e / np.maximum.accumulate(e) - 1.0).min())


class HeSoKhongDuocVUOTRuiRoCuaMOC(unittest.TestCase):

    def test_k_khong_lam_sut_giam_vuot_qua_moc(self):
        rng = np.random.default_rng(1)
        he = rng.normal(0.0004, 0.003, 1500)
        moc = rng.normal(0.0003, 0.010, 1500)
        k, _ = CONG.he_so_khop_rui_ro(he, moc)
        self.assertIsNotNone(k)
        self.assertLessEqual(
            abs(_dd(he, k)), abs(_dd(moc)) * 1.02,
            "khop xong ma sut giam con sau hon moc - dang cho phep chiu rui ro hon")

    def test_duoi_trai_day_KHONG_duoc_huong_he_so_lon(self):
        """Bien dong thap + mot cu sup = dang du an nay da gap BON lan.

        Neu chi khop theo bien dong thi chuoi nay duoc nhan len rat cao. Chot
        sut giam phai keo he so xuong.
        """
        rng = np.random.default_rng(2)
        he = rng.normal(0.0006, 0.0015, 1200)
        # Sut giam KEO DAI bang nhung buoc nho: bien dong van thap (mot cu sup
        # don le se tu day bien dong len va lam chot bien dong thanh chot chat).
        he[600:760] -= 0.0035
        moc = rng.normal(0.0003, 0.008, 1200)
        k_min, _ = CONG.he_so_khop_rui_ro(he, moc)
        a = np.asarray(he); b = np.asarray(moc)
        k_chi_bien_dong = b.std(ddof=1) / a.std(ddof=1)
        self.assertIsNotNone(k_min)
        self.assertLess(k_min, k_chi_bien_dong,
                        "chot sut giam khong keo he so xuong")

    def test_he_khong_the_nhan_len_ma_khong_chay_tai_khoan_thi_k_None(self):
        """1 + k*r <= 0 o mot bar nao do = pha san. Khong duoc huong phep nhan."""
        moc = np.random.default_rng(3).normal(0.0003, 0.02, 900)
        he = np.full(900, 0.001); he[400] = -0.45
        k, gc = CONG.he_so_khop_rui_ro(he, moc)
        if k is not None:
            self.assertGreater(float((1.0 + k * np.asarray(he)).min()), 0.0)
        else:
            self.assertIn("chay tai khoan", gc)


class PhepNhanKhongBienHeTEThanhHeTOT(unittest.TestCase):
    """Chot quan trong nhat cua ca file."""

    def test_he_THUA_tien_thi_khop_xong_van_thua(self):
        rng = np.random.default_rng(5)
        he = rng.normal(-0.0004, 0.004, 1500)     # ky vong AM
        moc = rng.normal(0.0004, 0.009, 1500)
        k, _ = CONG.he_so_khop_rui_ro(he, moc)
        if k is None:
            self.skipTest("khong khop duoc")
        self.assertLess(_gop(he, k), _gop(moc),
                        "he ky vong am ma khop xong lai thang moc")

    def test_nhan_len_lam_lo_NANG_them_chu_khong_nhe_di(self):
        he = np.full(500, -0.001)
        self.assertLess(_gop(he, 2.0), _gop(he, 1.0))

    def test_khop_KHONG_doi_dau_ket_qua(self):
        rng = np.random.default_rng(7)
        for hat in range(6):
            r = np.random.default_rng(hat).normal(0.0, 0.006, 800)
            moc = rng.normal(0.0002, 0.012, 800)
            k, _ = CONG.he_so_khop_rui_ro(r, moc)
            if k is None:
                continue
            with self.subTest(hat=hat):
                self.assertEqual(_gop(r, k) > 0, _gop(r, 1.0) > 0,
                                 "phep nhan doi dau lai/lo")


class TuChoiKhiKhongKhopDuoc(unittest.TestCase):

    def test_bien_dong_0_tra_None(self):
        k, gc = CONG.he_so_khop_rui_ro(np.zeros(600),
                                       np.random.default_rng(1).normal(0, .01, 600))
        self.assertIsNone(k)
        self.assertIn("bien dong", gc)

    def test_chuoi_qua_ngan_tra_None(self):
        k, gc = CONG.he_so_khop_rui_ro(np.ones(10) * 0.001, np.ones(10) * 0.002)
        self.assertIsNone(k)
        self.assertIn("ngan", gc)

    def test_NaN_khong_lam_hong_phep_do(self):
        rng = np.random.default_rng(11)
        he = rng.normal(0.0003, 0.004, 900); he[:5] = np.nan
        moc = rng.normal(0.0003, 0.009, 900); moc[:5] = np.nan
        k, _ = CONG.he_so_khop_rui_ro(he, moc)
        self.assertTrue(k is None or np.isfinite(k))


class MocRONGThiSIET(unittest.TestCase):
    """Moc khong co phan bu rui ro -> ba cong so-voi-moc khong loc duoc gi."""

    class _KQ:
        def __init__(self, loi, sharpe=None):
            self.loi = np.asarray(loi, dtype=float); self.sharpe = sharpe

    def test_moc_FX_phang_bi_coi_la_RONG(self):
        r = np.random.default_rng(4).normal(0.0, 0.006, 2000)   # drift ~0
        self.assertTrue(CONG.khong_co_phan_bu_rui_ro(self._KQ(r)))

    def test_moc_CHI_SO_co_xu_huong_KHONG_bi_coi_la_rong(self):
        r = np.random.default_rng(4).normal(0.0004, 0.009, 2000)
        self.assertFalse(CONG.khong_co_phan_bu_rui_ro(self._KQ(r)),
                         "moc chi so bi coi la rong -> siet oan moi ung vien")

    def test_moc_AM_cung_la_rong(self):
        r = np.random.default_rng(4).normal(-0.0003, 0.007, 2000)
        self.assertTrue(CONG.khong_co_phan_bu_rui_ro(self._KQ(r)))


class TheHeCongDaTang(unittest.TestCase):
    """Doi dieu kien cong ma khong tang the he = tron ket qua hai luat khac nhau."""

    def test_the_he_cong_it_nhat_la_5(self):
        self.assertGreaterEqual(
            CONG.THE_HE_CONG, 5,
            "doi cong 1 sang khop rui ro ma khong tang THE_HE_CONG -> ket qua "
            "cu va moi nam chung mot ho FDR trong khi luat da khac")


if __name__ == "__main__":
    unittest.main()
