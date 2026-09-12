# -*- coding: utf-8 -*-
"""Kiem `nhan/dap_quan_tri.py` - ho co che THU HAI (quan li lenh).

Bai kiem quan trong nhat o day la `TinhTienPhaiDungTUNG_DONG`. Ly do:

12/09/2026 do duoc rang `dap()` TRE MOT BAR. No tinh SL/TP tu `open[i+1]` roi
tra ve `vi_the[i+1]`, con `mo_phong.chay` TU DICH THEM mot bar nua
(`v[1:] = th[:-1]`). Ket qua: vi the that su an loi suat cua bar **i+2**.

Do bang chuoi dung san - cu nhay +9,3% o bar 5, tin hieu o bar 3, giu 1 bar:
he an dung cu nhay do, trong khi phan dung cua no la -0,14% cua bar 4. Tuc mot
he vao dung truoc mot cu no duoc cong diem cho cu no ma no khong kip vao.

Loi do khong lam gi sap va khong bao gi. No chi lam **moi con so quan tri sai**.
Nen tu day `dap()` tu tinh tien open-to-open va `so_luat` di qua
`vao_lenh.tinh_tien`, khong qua `mo_phong.chay` nua.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import dap_quan_tri as DQ  # noqa: E402


def chuoi(n=40, hat=7, nhay_o=None, nhay=0.0):
    rng = np.random.default_rng(hat)
    c = 100 + np.cumsum(rng.normal(0, 0.3, n))
    if nhay_o is not None:
        c[nhay_o:] += nhay
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c) + 0.2,
         "low": np.minimum(o, c) - 0.2, "close": c},
        index=pd.date_range("2020-01-01", periods=n, freq="D"))


class TinhTienPhaiDungTUNG_DONG(unittest.TestCase):
    def test_giu_mot_bar_an_dung_loi_suat_open_to_open(self):
        df = chuoi()
        o = df["open"].to_numpy(float)
        th = np.zeros(len(df)); th[3] = 1.0
        r = DQ.dap(df, th, {"thoat_bar": 1}, giu_toi_da=1)
        self.assertAlmostEqual(float(r["loi_tho"].sum()),
                               float(np.log(o[5] / o[4])), places=10,
                               msg="vao open[4] giu 1 bar ma khong an log(o5/o4)")

    def test_KHONG_an_cu_nhay_cua_bar_ke_tiep(self):
        """Chot chan cua loi TRE MOT BAR: cu nhay dat o bar 5, tin hieu bar 3,
        giu 1 bar -> he KHONG duoc cong cu nhay do."""
        df = chuoi(nhay_o=5, nhay=10.0)
        th = np.zeros(len(df)); th[3] = 1.0
        r = DQ.dap(df, th, {"thoat_bar": 1}, giu_toi_da=1)
        self.assertLess(abs(float(r["loi_tho"].sum())), 0.02,
                        "he an cu nhay +10%% cua bar ma no chua vao")

    def test_chieu_ban_doi_dau(self):
        df = chuoi()
        o = df["open"].to_numpy(float)
        th = np.zeros(len(df)); th[3] = -1.0
        r = DQ.dap(df, th, {"thoat_bar": 1}, giu_toi_da=1)
        self.assertAlmostEqual(float(r["loi_tho"].sum()),
                               -float(np.log(o[5] / o[4])), places=10)


class SoBarGiuPhaiDungNHU_KHAI(unittest.TestCase):
    def test_thoat_bar_N_giu_dung_N_bar(self):
        df = chuoi(n=60)
        th = np.zeros(len(df)); th[5] = 1.0
        for N in (1, 3, 7):
            r = DQ.dap(df, th, {"thoat_bar": N}, giu_toi_da=50)
            self.assertEqual(len(r["lenh"]), 1)
            self.assertEqual(r["lenh"][0]["bar"], N,
                             "thoat_bar=%d ma giu %d bar" % (N, r["lenh"][0]["bar"]))


class TieBreakPhaiTheoOPEN(unittest.TestCase):
    """CLAUDE.md muc 4: mot bar cham CA SL lan TP thi doan bang `open` cua bar
    do. Mac dinh lay SL la SAI - no lam moi he co TP gan trong te hon that."""

    def _df_cham_ca_hai(self, open_gan_tp: bool):
        # bar 2 la bar vao (open), bar 3 cham ca hai phia
        o = np.array([100.0, 100.0, 100.0, 100.0, 100.0])
        c = o.copy()
        h = np.array([100.5, 100.5, 100.5, 130.0, 100.5])
        l = np.array([99.5, 99.5, 99.5, 70.0, 99.5])
        if open_gan_tp:
            o[3] = 108.0            # mo GAN phia TP
        else:
            o[3] = 92.0             # mo GAN phia SL
        return pd.DataFrame({"open": o, "high": h, "low": l, "close": c},
                            index=pd.date_range("2020-01-01", periods=5, freq="D"))

    def test_mo_gan_TP_thi_an_TP(self):
        df = self._df_cham_ca_hai(True)
        th = np.zeros(5); th[0] = 1.0
        r = DQ.dap(df, th, {"sl_atr": 1.0, "tp_atr": 1.0}, giu_toi_da=4)
        if not r["lenh"]:
            self.skipTest("chuoi thu khong sinh lenh (ATR)")
        self.assertEqual(r["lenh"][0]["ly_do"], "tp")

    def test_mo_gan_SL_thi_an_SL(self):
        df = self._df_cham_ca_hai(False)
        th = np.zeros(5); th[0] = 1.0
        r = DQ.dap(df, th, {"sl_atr": 1.0, "tp_atr": 1.0}, giu_toi_da=4)
        if not r["lenh"]:
            self.skipTest("chuoi thu khong sinh lenh (ATR)")
        self.assertEqual(r["lenh"][0]["ly_do"], "sl")


class KhaiBaoSaiPhaiNEM_LOI(unittest.TestCase):
    def test_nut_la_bi_tu_choi(self):
        df = chuoi()
        with self.assertRaises(KeyError):
            DQ.dap(df, np.zeros(len(df)), {"sl_phan_tram": 2.0})

    def test_moi_nut_khai_bao_deu_CO_TAC_DUNG(self):
        """Moi ten trong `NUT` phai that su LAM DOI KET QUA. Mot nut chay khong
        loi nhung khong doi gi la mot luat chet nam trong danh sach - va no se
        am tham xuat hien trong bang so sanh nhu mot lua chon co that.

        (Ho benh `doi-tham-so-ma-khong-doi-ket-qua`: closure DSL nuot tham so.)"""
        df = chuoi(n=200, hat=3)
        th = np.zeros(len(df)); th[::10] = 1.0
        moc = DQ.dap(df, th, {}, giu_toi_da=30)
        self.assertGreater(moc["so_lenh"], 3, "chuoi thu khong du lenh de so")
        # Quet mot DAI gia tri chu khong mot diem: mot nut co the vo hieu o mot
        # nguong ma van dung o nguong khac. Do la hanh vi THAT, khong phai loi -
        # `quan-tri-can-cho-de-hoat-dong`: dat hue o 1,5 ATR vo hieu tren nhung
        # lenh khong bao gio quay lai diem vao sau khi da lai 1,5 ATR, con o 0,2
        # ATR thi no cat 5 lenh. Cai phai kiem la nut co CO THE doi ket qua
        # khong, tuc tham so co that su di den engine khong.
        for nut in DQ.NUT:
            dai = [2, 5, 12] if nut == "thoat_bar" else [0.2, 0.5, 1.0, 3.0]
            doi = False
            for gt in dai:
                luat = {nut: gt}
                if nut == "trail_buoc":
                    luat["trail_tu_atr"] = 0.5   # buoc chi co nghia khi trail bat
                r = DQ.dap(df, th, luat, giu_toi_da=30)
                self.assertTrue(np.all(np.isfinite(r["loi_tho"])), nut)
                self.assertTrue(np.all(r["khoi_luong"] >= 0), nut)
                if (r["so_lenh"] != moc["so_lenh"]
                        or not np.allclose(r["loi_tho"], moc["loi_tho"], atol=1e-12)):
                    doi = True
            self.assertTrue(doi, "nut '%s' khong doi ket qua o BAT KY gia tri nao "
                                 "trong %s -> tham so khong den duoc engine"
                            % (nut, dai))

    def test_nut_trail_buoc_co_tac_dung_khi_di_kem_trail_tu(self):
        df = chuoi(n=200, hat=3)
        th = np.zeros(len(df)); th[::10] = 1.0
        a = DQ.dap(df, th, {"trail_tu_atr": 1.0, "trail_buoc": 0.5}, giu_toi_da=30)
        b = DQ.dap(df, th, {"trail_tu_atr": 1.0, "trail_buoc": 3.0}, giu_toi_da=30)
        self.assertFalse(np.allclose(a["loi_tho"], b["loi_tho"], atol=1e-12),
                         "doi buoc trailing 0,5 -> 3,0 ATR ma ket qua y het")


class KhongDuocNHIN_TRUOC(unittest.TestCase):
    def test_tin_hieu_tuong_lai_khong_doi_qua_khu(self):
        df = chuoi(n=120)
        a = np.zeros(len(df)); a[10] = 1.0; a[40] = -1.0
        b = a.copy(); b[110] = 1.0
        ra = DQ.dap(df, a, {"sl_atr": 2.0, "tp_atr": 4.0}, giu_toi_da=20)
        rb = DQ.dap(df, b, {"sl_atr": 2.0, "tp_atr": 4.0}, giu_toi_da=20)
        np.testing.assert_allclose(ra["loi_tho"][:105], rb["loi_tho"][:105],
                                   atol=1e-12)

    def test_khong_giao_dich_truoc_hoac_dung_bar_tin_hieu(self):
        df = chuoi(n=80)
        th = np.zeros(len(df)); th[30] = 1.0
        r = DQ.dap(df, th, {"sl_atr": 2.0}, giu_toi_da=20)
        self.assertEqual(float(r["khoi_luong"][:31].sum()), 0.0)


class BoLuatDoiChieuPhaiCON_NGUYEN(unittest.TestCase):
    def test_khong_gi_la_moc_va_phai_rong(self):
        self.assertEqual(DQ.BO_LUAT["khong_gi"], {},
                         "moc doi chieu phai la KHONG luat nao")

    def test_moi_bo_luat_chi_dung_nut_hop_le(self):
        for ten, luat in DQ.BO_LUAT.items():
            for k in luat:
                self.assertIn(k, DQ.NUT, "%s dung nut la: %s" % (ten, k))


if __name__ == "__main__":
    unittest.main(verbosity=2)
