# -*- coding: utf-8 -*-
"""HIEU CHUAN HINH DANG — thong ke hinh dang chi co nghia khi biet phan bo NULL.

`do_on_dinh.py` do duoc "cao nguyen hay cai gai" nhung ba con so cua no chua
tung duoc hieu chuan: mot be mat hoan toan ngau nhien cung co o tot nhat, cung
co lan can duong neu tai san do di len. File nay kiem bo do so-voi-null.

Ba dieu phai nam trong bo kiem chu khong nam trong y dinh:
  1. **Khong tieu suat FDR** — moi loi goi cong phai co `ghi_so=False`.
  2. **p co san** — voi K chuoi null, p nho nhat la 1/(K+1). Khong duoc phep co
     mot duong nao tra ve p = 0.
  3. **Null phai la null** — chuoi sinh ra phai khac chuoi that, va hai phuong
     phap phai duoc dung luan phien (mot co che that phai vuot ca hai).
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

import hinh_dang_vs_null as HD   # noqa: E402


def _df_gia(n: int = 800, hat: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(hat)
    r = rng.normal(0.0002, 0.01, n)
    c = 100.0 * np.exp(np.cumsum(r))
    rong = np.abs(rng.normal(0, 0.006, n)) * c + 1e-6
    low = c - rng.uniform(0, 1, n) * rong
    return pd.DataFrame(
        {"open": low + rng.uniform(0, 1, n) * rong, "high": low + rong,
         "low": low, "close": c},
        index=pd.date_range("2015-01-01", periods=n, freq="D"))


class PhanViPhaiCoSAN(unittest.TestCase):

    def test_p_nho_nhat_la_mot_tren_K_cong_mot(self):
        """Khong duong nao duoc tra p = 0: 20 chuoi null khong do noi p<0,047."""
        ra = HD._phan_vi(1e9, list(range(20)))
        self.assertEqual(ra["p"], round(1 / 21, 4))
        self.assertGreater(ra["p"], 0.0)

    def test_dem_dung_so_null_dat_toi(self):
        ra = HD._phan_vi(5.0, [1.0, 4.0, 5.0, 9.0])      # 2 chuoi >= 5
        self.assertEqual(ra["p"], round(3 / 5, 4))
        self.assertEqual(ra["so_null"], 4)

    def test_boi_dinh_thap_moi_tot_nen_doi_chieu(self):
        """`boi_dinh` cang thap cang giong cao nguyen -> dem chieu NGUOC."""
        thap = HD._phan_vi(1.1, [1.0, 2.0, 3.0, 4.0], cao_la_tot=False)
        cao = HD._phan_vi(1.1, [1.0, 2.0, 3.0, 4.0], cao_la_tot=True)
        self.assertLess(thap["p"], cao["p"])

    def test_khong_co_null_thi_tra_None(self):
        self.assertIsNone(HD._phan_vi(1.0, []))
        self.assertIsNone(HD._phan_vi(None, [1.0, 2.0]))


class HinhDangPhaiDocDUOC(unittest.TestCase):

    def setUp(self):
        self.tam = {"n": 10}
        self.luoi = [{"n": v} for v in (6, 8, 10, 12, 14)]

    def test_cao_nguyen_va_cai_gai_khong_lan(self):
        cn = HD._hinh_dang(self.luoi, [3.0, 3.2, 3.1, 3.0, 2.9], self.tam)
        self.assertIn("CAO NGUYEN", cn["hinh_dang"])
        self.assertEqual(cn["ty_le_duong"], 100.0)
        gai = HD._hinh_dang(self.luoi, [0.1, 0.1, 9.0, 0.1, 0.1], self.tam)
        self.assertIn("CAI GAI", gai["hinh_dang"])

    def test_do_doc_do_tren_o_CACH_TAM_MOT_BUOC(self):
        # tam = 4,0; MOI o khac tam la "mot buoc" (luoi mot chieu) -> trung vi 1,5
        ra = HD._hinh_dang(self.luoi, [1.0, 2.0, 4.0, 2.0, 1.0], self.tam)
        self.assertAlmostEqual(ra["do_doc_mot_buoc_pct"], 62.5, places=6)

    def test_o_khong_chay_duoc_bi_bo_chu_khong_thanh_khong(self):
        """`None` la 'khong do duoc', khong phai alpha = 0."""
        ra = HD._hinh_dang(self.luoi, [None, None, 2.0, None, None], self.tam)
        self.assertEqual(ra["chay_duoc"], 1)
        self.assertEqual(ra["ty_le_duong"], 100.0)

    def test_khong_o_nao_chay_duoc_thi_noi_ro(self):
        self.assertFalse(HD._hinh_dang(self.luoi, [None] * 5, self.tam)["do_duoc"])


class NullPhaiLaNULL(unittest.TestCase):

    def test_sinh_du_so_chuoi_va_luan_phien_hai_phuong_phap(self):
        ds = list(HD._chuoi_null(_df_gia(), 6))
        self.assertEqual(len(ds), 6)
        self.assertEqual({pp for pp, _ in ds}, set(HD.PP_NULL))

    def test_chuoi_null_khac_chuoi_that(self):
        d = _df_gia()
        for _pp, dn in HD._chuoi_null(d, 4):
            # loi suat co n-1 phan tu nen chuoi null ngan hon dung mot bar
            self.assertGreaterEqual(len(dn), len(d) - 1)
            self.assertLessEqual(len(dn), len(d))
            self.assertFalse(np.allclose(dn["close"].to_numpy(),
                                         d["close"].to_numpy()[:len(dn)]))

    def test_chuoi_qua_ngan_thi_khong_sinh_null_gia(self):
        self.assertEqual(list(HD._chuoi_null(_df_gia(120), 4)), [])


class KhongDuocTieuSuatFDR(unittest.TestCase):

    def test_moi_loi_goi_cong_deu_ghi_so_False(self):
        """Bat bien 1. Bo do nay goi cong hang tram nghin lan trong mot dem."""
        from nhan import cong as CONG, mau as MAU, mo_phong as MP
        da_goi = []

        def gia_xet(*a, **kw):
            da_goi.append(kw)
            return {"so_sanh": {"alpha_vs_mua_giu": {"alpha_nam_pct": 1.0}}}

        goc = (CONG.xet, MAU.sinh, MP.chay, MP.mua_giu)
        CONG.xet = gia_xet
        MAU.sinh = lambda *a, **kw: None
        MP.chay = lambda *a, **kw: None
        MP.mua_giu = lambda *a, **kw: None
        try:
            HD._alpha_mot_o("mau_nao_do", {"n": 5}, _df_gia(), None, "X", "D1",
                            "giao_dich")
        finally:
            CONG.xet, MAU.sinh, MP.chay, MP.mua_giu = goc
        self.assertEqual(len(da_goi), 1)
        self.assertIs(da_goi[0].get("ghi_so"), False)
        self.assertIs(da_goi[0].get("chay_placebo"), False)


class AlphaAmKhongDuocTinhLaPHATHIEN(unittest.TestCase):
    """p nho tren mot he LO tien nghia la 'lo it hon null', khong phai edge.

    Do la cai bay do duoc trong luot 368 ung vien: XAUUSDM.H4.lap_gap mat
    7,7%/nam trong khi null mat 18,5%/nam -> p = 0,0198 va no leo len dau bang.
    """

    def _r(self, ma, alpha, p):
        return {"ma": ma, "do_duoc": True,
                "that": {"alpha_tam": alpha, "hinh_dang": "x"},
                "so_voi_null": {"alpha_tam": {"p": p, "null_p95": alpha - 1},
                                "ty_le_duong": {"p": p, "null_p95": 0},
                                "o_tot_nhat": {"p": p, "null_p95": 0},
                                "boi_dinh": {"p": p, "null_p95": 0}}}

    def test_dong_tong_ket_chi_dem_tren_alpha_duong(self):
        md = HD._bao_cao_md([self._r("AM", -7.7, 0.01), self._r("DUONG", 2.0, 0.5)])
        self.assertIn("alpha duong 1", md)
        self.assertIn("alpha am 1", md)
        self.assertIn("p<=0,05: **0/1**", md)

    def test_hai_bang_tach_roi_va_bang_am_duoc_ghi_chu(self):
        md = HD._bao_cao_md([self._r("AM", -7.7, 0.01), self._r("DUONG", 2.0, 0.5)])
        self.assertLess(md.index("## Alpha DUONG"), md.index("## Alpha AM"))
        self.assertIn("LO IT HON NULL", md)


if __name__ == "__main__":
    unittest.main()
