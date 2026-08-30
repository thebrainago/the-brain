# -*- coding: utf-8 -*-
"""Tang 3: tinh von va ket hop.

Hieu chuan hai chieu o day nghia la: ghep hai chien luoc DOC LAP phai cai thien
Sharpe, va ghep hai ban SAO CHEP cua cung mot chien luoc thi KHONG duoc cai
thien. Chi co ve dau khong phan biet duoc mot module dung voi mot module cong
so lai roi chia.
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

from nhan import danh_muc as DM


def _tp(ma: str, loi: np.ndarray, index) -> DM.ThanhPhan:
    from nhan import do_luong as DO
    return DM.ThanhPhan(ma=ma, tai_san="TEST", khung="D1", template="t", ho="h",
                        loi=loi, index=index, chi_so=DO.chi_so(loi, index))


def _chuoi(n=1000, muy=0.0006, sig=0.01, hat=0):
    rng = np.random.default_rng(hat)
    return rng.normal(muy, sig, n)


def _index(n=1000):
    return pd.date_range("2015-01-01", periods=n, freq="D")


class TuongQuanDuoi(unittest.TestCase):

    def test_bat_duoc_rui_ro_chung_ma_tuong_quan_thuong_giau(self):
        """Hai chuoi gan doc lap NHUNG cung sap trong cung nhung ngay xau."""
        n = 3000
        rng = np.random.default_rng(3)
        a = rng.normal(0.0005, 0.02, n)
        b = rng.normal(0.0005, 0.02, n)
        soc = rng.choice(n, size=int(n * 0.04), replace=False)
        a[soc] -= 0.05
        b[soc] -= 0.05
        bang = pd.DataFrame({"A": a, "B": b}, index=_index(n))

        chung = float(bang.corr().loc["A", "B"])
        duoi = float(DM.tuong_quan_duoi(bang).loc["A", "B"])
        self.assertGreater(duoi, chung,
                           "phu thuoc duoi phai lo ra rui ro ma corr thuong giau")
        self.assertGreaterEqual(duoi, DM.NGUONG_CUM, "phai du de gom vao mot cum")

    def test_thang_do_duoc_hieu_chuan(self):
        """Doc lap ~0,10; trung khop 1,00; nguoc pha 0,00.

        Thieu bai nay thi mot thuoc do luon tra 0,7 cho moi cap trong y het mot
        thuoc do dung - va do dung la loi da mac: loc theo TONG cua chinh hai
        chuoi (thien lech collider) cho hai chuoi doc lap ra 0,685.
        """
        n = 3000
        a = _chuoi(n, hat=101)
        b = _chuoi(n, hat=102)
        idx = _index(n)
        doc_lap = float(DM.tuong_quan_duoi(pd.DataFrame({"A": a, "B": b}, index=idx)).loc["A", "B"])
        y_het = float(DM.tuong_quan_duoi(pd.DataFrame({"A": a, "B": a.copy()}, index=idx)).loc["A", "B"])
        nguoc = float(DM.tuong_quan_duoi(pd.DataFrame({"A": a, "B": -a}, index=idx)).loc["A", "B"])
        self.assertLess(doc_lap, 0.25, "doc lap ma bao la tuong quan cao")
        self.assertAlmostEqual(y_het, 1.0, places=6)
        self.assertAlmostEqual(nguoc, 0.0, places=6)

    def test_chuoi_doc_lap_thi_tuong_quan_duoi_thap(self):
        """Bai kiem LUC: khong duoc bao cao tuong quan cao cho moi cap."""
        n = 1500
        bang = pd.DataFrame({"A": _chuoi(n, hat=1), "B": _chuoi(n, hat=2)},
                            index=_index(n))
        self.assertLess(abs(float(DM.tuong_quan_duoi(bang).loc["A", "B"])), 0.35)

    def test_bang_mot_cot_khong_lam_vo(self):
        bang = pd.DataFrame({"A": _chuoi(200)}, index=_index(200))
        self.assertTrue(DM.tuong_quan_duoi(bang).empty)


class GomCum(unittest.TestCase):

    def test_hai_ban_sao_vao_cung_mot_cum(self):
        loi = _chuoi(800, hat=5)
        bang = pd.DataFrame({"A": loi, "B": loi.copy()}, index=_index(800))
        cum = DM.gom_cum(DM.tuong_quan_duoi(bang))
        self.assertEqual(len(cum), 1)
        self.assertEqual(sorted(cum[0]), ["A", "B"])

    def test_chuoi_doc_lap_thanh_cac_cum_rieng(self):
        bang = pd.DataFrame({"A": _chuoi(1200, hat=7), "B": _chuoi(1200, hat=8)},
                            index=_index(1200))
        self.assertEqual(len(DM.gom_cum(DM.tuong_quan_duoi(bang))), 2)


class PhanBoVon(unittest.TestCase):

    def test_tong_ty_trong_khong_vuot_mot(self):
        tps = [_tp(f"S{i}", _chuoi(500, hat=i), _index(500)) for i in range(5)]
        cum = [[t.ma] for t in tps]
        self.assertLessEqual(sum(DM.phan_bo(tps, cum).values()), 1.0 + 1e-9)

    def test_cum_dong_nguoi_bi_ha_ty_trong_tung_thanh_phan(self):
        """Nam chien luoc cung mot cum khong duoc an nam suat rui ro."""
        tps = [_tp(f"S{i}", _chuoi(500, hat=i), _index(500)) for i in range(5)]
        mot_cum = [[t.ma for t in tps]]
        w = DM.phan_bo(tps, mot_cum)
        self.assertAlmostEqual(sum(w.values()), DM.TRAN_RUI_RO_CUM, places=6)
        for v in w.values():
            self.assertAlmostEqual(v, DM.TRAN_RUI_RO_CUM / 5, places=6)

    def test_chia_deu_trong_cum_khong_theo_sharpe(self):
        """Chia theo Sharpe quan sat duoc la tiep tuc toi uu tren du lieu da chon."""
        tot = _tp("TOT", _chuoi(800, muy=0.003, hat=11), _index(800))
        te = _tp("TE", _chuoi(800, muy=0.0001, hat=12), _index(800))
        w = DM.phan_bo([tot, te], [["TOT", "TE"]])
        self.assertAlmostEqual(w["TOT"], w["TE"], places=9)


class VonToiThieu(unittest.TestCase):

    def test_loi_cang_thap_thi_can_cang_nhieu_von(self):
        it = DM.von_toi_thieu(0.05)
        nhieu = DM.von_toi_thieu(0.20)
        self.assertGreater(it, nhieu)

    def test_loi_am_thi_khong_co_muc_von_nao_cuu_duoc(self):
        self.assertIsNone(DM.von_toi_thieu(-0.01))
        self.assertIsNone(DM.von_toi_thieu(0.0))


class Ghep(unittest.TestCase):

    def test_ghep_hai_chien_luoc_doc_lap_thi_sharpe_tot_hon(self):
        n = 2000
        a = _tp("A", _chuoi(n, muy=0.0004, hat=21), _index(n))
        b = _tp("B", _chuoi(n, muy=0.0004, hat=22), _index(n))
        ra = DM.ghep([a, b])
        self.assertEqual(ra["so_cum"], 2)
        self.assertTrue(ra["ghep_co_hon_cai_tot_nhat"],
                        f"{ra['danh_muc'].get('sharpe')} vs {ra['sharpe_tot_nhat_rieng_le']}")

    def test_ghep_hai_ban_sao_KHONG_cai_thien(self):
        """Bai kiem LUC nguoc: da dang hoa gia phai bi phat hien."""
        n = 2000
        loi = _chuoi(n, muy=0.0004, hat=31)
        a = _tp("A", loi, _index(n))
        b = _tp("B", loi.copy(), _index(n))
        ra = DM.ghep([a, b])
        self.assertEqual(ra["so_cum"], 1, "hai ban sao phai nam chung mot cum")
        self.assertFalse(ra["ghep_co_hon_cai_tot_nhat"],
                         "ghep ban sao ma bao la cai thien = da dang hoa gia")

    def test_thieu_moc_mua_giu_thi_phai_canh_bao(self):
        ra = DM.ghep([_tp("A", _chuoi(500, hat=41), _index(500))])
        self.assertIsNone(ra["hon_mua_giu"])
        self.assertIn("canh_bao", ra)

    def test_co_moc_mua_giu_thi_phan_xu_duoc(self):
        n = 1000
        idx = _index(n)
        he = _tp("A", _chuoi(n, muy=0.0008, hat=51), idx)
        moc_kem = _chuoi(n, muy=0.00001, hat=52)
        ra = DM.ghep([he], moc_mua_giu=moc_kem, index_moc=idx)
        self.assertIsNotNone(ra["mua_giu"])
        self.assertIsInstance(ra["hon_mua_giu"], bool)

    def test_danh_muc_rong_khong_lam_vo(self):
        ra = DM.ghep([])
        self.assertEqual(ra["n"], 0)
        self.assertIn("ly_do", ra)

    def test_bao_von_toi_thieu_khi_co_lai(self):
        n = 1500
        a = _tp("A", _chuoi(n, muy=0.0006, hat=61), _index(n))
        b = _tp("B", _chuoi(n, muy=0.0006, hat=62), _index(n))
        ra = DM.ghep([a, b])
        if (ra["danh_muc"].get("cagr_pct") or 0) > 0:
            self.assertIsNotNone(ra["von_toi_thieu_de_dang_chay"])
            self.assertGreater(ra["von_toi_thieu_de_dang_chay"], 0)


class GongChuoi(unittest.TestCase):

    def test_gong_theo_thoi_gian_khong_theo_vi_tri(self):
        """Hai chuoi khac moc bat dau: cat theo vi tri se lech hang gia."""
        a = _tp("A", _chuoi(500, hat=71), pd.date_range("2015-01-01", periods=500, freq="D"))
        b = _tp("B", _chuoi(500, hat=72), pd.date_range("2016-01-01", periods=500, freq="D"))
        bang = DM.gong_chuoi([a, b])
        self.assertEqual(list(bang.columns), ["A", "B"])
        self.assertEqual(bang.index.min(), pd.Timestamp("2015-01-01"))
        self.assertEqual(bang.index.max(), pd.Timestamp("2017-05-14"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
