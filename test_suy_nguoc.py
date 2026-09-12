# -*- coding: utf-8 -*-
"""Kiem `nhan/suy_nguoc.py` - di tu KET CUC ve DAU HIEU.

Module nay co mot tinh chat de hong theo kieu im lang: no CO PHEP nhin ve tuong
lai o mot nua (dinh nghia su kien) va TUYET DOI KHONG o nua kia (dau hieu). Mot
dau hieu vo tinh nhin truoc se cho ra "phat hien" tuyet dep va hoan toan gia.

Nen bai kiem truc cot o day la mot cap doi nhau:

    DauHieuKhongDuocNHIN_TRUOC   doi bar tuong lai -> dau hieu qua khu KHONG doi
    SuKienPHAI_nhin_truoc        doi bar tuong lai -> mat na su kien PHAI doi

Neu bai thu hai xanh ma bai dau do, la ta da doi cho hai nua cho nhau.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import suy_nguoc as SN  # noqa: E402


def chuoi(n=400, hat=5):
    rng = np.random.default_rng(hat)
    c = 100 + np.cumsum(rng.normal(0, 0.4, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + np.abs(rng.normal(0, 0.2, n))
    l = np.minimum(o, c) - np.abs(rng.normal(0, 0.2, n))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                        index=pd.date_range("2018-01-01", periods=n, freq="D"))


class DauHieuKhongDuocNHIN_TRUOC(unittest.TestCase):
    def test_doi_bar_cuoi_khong_lam_doi_dau_hieu_truoc_do(self):
        df = chuoi()
        a = SN.dau_hieu(df)
        d2 = df.copy()
        for k in ("open", "high", "low", "close"):
            v = d2[k].to_numpy(float).copy()
            v[300:] *= 1.5          # doi han nua sau
            d2[k] = v
        b = SN.dau_hieu(d2)
        self.assertEqual(set(a), set(b))
        for ten in a:
            x, y = a[ten][:280], b[ten][:280]
            k = np.isfinite(x) & np.isfinite(y)
            np.testing.assert_allclose(
                x[k], y[k], atol=1e-9,
                err_msg="dau hieu '%s' doi khi bar TUONG LAI doi" % ten)

    def test_moi_dau_hieu_deu_cung_do_dai_voi_du_lieu(self):
        df = chuoi(200)
        for ten, v in SN.dau_hieu(df).items():
            self.assertEqual(len(v), len(df), ten)


class SuKienPHAI_nhin_truoc(unittest.TestCase):
    """Su kien la KET CUC ta muon du bao, nen no PHAI doc bar tuong lai. Neu bai
    nay do thi mat na dang duoc tinh sai - va moi phep do se so dau hieu voi mot
    'ket cuc' chua xay ra."""

    def test_doi_bar_tuong_lai_lam_doi_mat_na(self):
        df = chuoi()
        a = SN.su_kien(df)
        d2 = df.copy()
        c = d2["close"].to_numpy(float).copy()
        c[300:] *= 1.4
        d2["close"] = c
        b = SN.su_kien(d2)
        self.assertTrue(a and b)
        doi = any(not np.array_equal(a[k], b[k]) for k in a)
        self.assertTrue(doi, "doi han nua sau ma mat na su kien khong doi gi")

    def test_ba_loai_su_kien_va_khong_rong(self):
        sk = SN.su_kien(chuoi())
        self.assertEqual(set(sk), {"cu_tang", "cu_giam", "chay_thang"})
        for k, v in sk.items():
            self.assertGreater(int(v.sum()), 0, k)

    def test_bar_cuoi_khong_the_la_su_kien(self):
        """K bar cuoi khong du du lieu tuong lai -> khong duoc danh dau."""
        df = chuoi()
        sk = SN.su_kien(df, k_toi=SN.K_TOI)
        for k in ("cu_tang", "cu_giam"):
            self.assertEqual(int(sk[k][-SN.K_TOI:].sum()), 0,
                             "%s danh dau bar chua co tuong lai" % k)


class NullPhaiGIU_CUM(unittest.TestCase):
    def test_xoay_vong_giu_nguyen_so_su_kien(self):
        n = 500
        mat_na = np.zeros(n, dtype=bool)
        mat_na[100:160] = True          # mot CUM, khong rai deu
        x = np.random.default_rng(1).normal(size=n)
        rng = np.random.default_rng(2)
        # xoay khong duoc lam doi so luong su kien
        for k in (1, 7, 123, 499):
            self.assertEqual(int(np.roll(mat_na, k).sum()), int(mat_na.sum()))
        null = SN._xoay_null(mat_na, x, 50, rng)
        self.assertEqual(len(null), 50)
        self.assertTrue(np.all(np.isfinite(null)))

    def test_null_khong_phai_hang_so(self):
        n = 400
        mat_na = np.zeros(n, dtype=bool); mat_na[50:90] = True
        x = np.arange(n, dtype=float)
        null = SN._xoay_null(mat_na, x, 60, np.random.default_rng(3))
        self.assertGreater(float(np.std(null)), 0.0,
                           "null xoay vong ra hang so - phep xoay khong chay")


class DoMotPhaiTraVeDayDU(unittest.TestCase):
    def test_co_du_ba_su_kien_va_cac_truong(self):
        d = SN.do_mot(chuoi(600), so_xoay=60)
        self.assertNotIn("loi", d)
        for sk in ("cu_tang", "cu_giam", "chay_thang"):
            self.assertIn(sk, d)
            if not d[sk]:
                continue
            mot = next(iter(d[sk].values()))
            for k in ("tb_su_kien", "tb_chung", "lech_chuan", "p_xoay",
                      "so_su_kien"):
                self.assertIn(k, mot)

    def test_p_khong_bao_gio_bang_khong(self):
        d = SN.do_mot(chuoi(600), so_xoay=60)
        for sk, cua_no in d.items():
            if not isinstance(cua_no, dict):
                continue
            for dh, v in cua_no.items():
                self.assertGreater(v["p_xoay"], 0.0, "%s/%s" % (sk, dh))

    def test_chuoi_qua_ngan_thi_noi_ro_chu_khong_nem(self):
        d = SN.do_mot(chuoi(40), so_xoay=20)
        self.assertIn("loi", d)


class NguongPhaiLaDO_LON_KhongChiLaP(unittest.TestCase):
    def test_co_nguong_lech_chuan(self):
        """Voi 400 lan xoay, p nho nhat la 1/401 - nhieu dau hieu cham san do
        cung luc. Do LON cua chenh lech moi la thu hanh dong duoc."""
        self.assertGreater(SN.NGUONG_LECH, 0.0)
        self.assertLess(SN.NGUONG_P, 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
