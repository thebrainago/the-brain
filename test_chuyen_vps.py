# -*- coding: utf-8 -*-
"""Kiem ba module phuc vu CHUYEN VPS: duong_dan · san_sang_vps · doc_lenh_tester.

Chu du an 12/09/2026 chot: he se len **VPS chay 24/7 nhieu thang**.

Chuyen may la luc moi thu "chi chay tren may nay" lo ra cung mot luc - va tren
VPS **khong co ai ngoi canh de thay**. Bo kiem nay chan ba dang hong:

  1. `duong_dan` tra ve duong SAI hoac NEM LOI khi may khong co thu can tim.
     Mot script bao cao khong duoc chet chi vi VPS khong co Desktop.
  2. `san_sang_vps` bao "da san sang" trong khi chua - hoac nguoc lai, keu oan.
  3. `doc_lenh_tester` doc sai danh sach lenh. Day la dau vao cua ca duong
     "truy nguoc lich su giao dich", doc sai thi moi luat chung ra deu sai.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))

from nhan import duong_dan as DD        # noqa: E402
from nhan import san_sang_vps as V      # noqa: E402
from nhan import doc_lenh_tester as DLT  # noqa: E402


class DuongDanPhaiDO_TU_VI_TRI_FILE(unittest.TestCase):
    def test_LAB_la_thu_muc_lab_that(self):
        self.assertTrue((DD.LAB / "nhan").is_dir())
        self.assertTrue((DD.LAB / "b.py").exists())
        self.assertEqual(DD.LAB.name, "lab")

    def test_GOC_chua_ca_lab_lan_ds(self):
        self.assertEqual(DD.GOC, DD.LAB.parent)

    def test_KHONG_NEM_LOI_khi_khong_tim_thay(self):
        """Tren VPS co the khong co MT5, khong co Desktop. Cac ham phai tra ve
        None hoac mot duong lui, KHONG duoc nem loi."""
        cu = dict(os.environ)
        try:
            for k in ("BRAIN_MT5", "BRAIN_MT5_DATA", "BRAIN_DESKTOP",
                      "APPDATA", "ProgramFiles", "ProgramW6432", "LOCALAPPDATA"):
                os.environ.pop(k, None)
            DD.mt5_exe()          # co the None - khong duoc nem
            DD.mt5_du_lieu()
            d = DD.desktop()
            self.assertIsInstance(d, Path)
        finally:
            os.environ.clear()
            os.environ.update(cu)

    def test_bien_moi_truong_duoc_uu_tien(self):
        cu = os.environ.get("BRAIN_DESKTOP")
        try:
            os.environ["BRAIN_DESKTOP"] = str(GOC)
            self.assertEqual(DD.desktop(), GOC)
        finally:
            if cu is None:
                os.environ.pop("BRAIN_DESKTOP", None)
            else:
                os.environ["BRAIN_DESKTOP"] = cu

    def test_tom_tat_co_du_khoa(self):
        d = DD.tom_tat()
        for k in ("LAB", "GOC", "mt5_exe", "mt5_du_lieu", "desktop"):
            self.assertIn(k, d)


class BoKiemVpsPhaiDEM_DUOC(unittest.TestCase):
    def test_do_het_tra_du_nam_muc(self):
        k = V.do_het()
        for m in ("duong_go_cung", "thu_vien_thieu", "dung_luong",
                  "phu_thuoc_may_nay", "can_nguoi", "bien_moi_truong"):
            self.assertIn(m, k)

    def test_duong_go_cung_tra_ve_kem_TEP_va_SO_LAN(self):
        """Mot bao cao chi noi 'co 26 duong go cung' thi khong ai sua duoc -
        phai noi o dau va bao nhieu lan."""
        for d, tep, n in V.duong_dan_go_cung()[:5]:
            self.assertTrue(d and tep)
            self.assertGreaterEqual(n, 1)

    def test_can_nguoi_moi_muc_deu_co_CACH_LAM(self):
        for x in V.can_nguoi():
            self.assertTrue(x["viec"])
            self.assertTrue(x["lam_the_nao"],
                            "'%s' khong noi lam the nao" % x["viec"])
            self.assertTrue(x["vi_sao"])

    def test_bao_cao_ghi_ra_tep(self):
        vb = V.bao_cao(in_ra=lambda *a, **k: None)
        self.assertIn("SAN SANG VPS", vb)
        self.assertTrue(V.BAO_CAO.exists())


class DocLenhTesterPhaiDUNG(unittest.TestCase):
    F = GOC / "reports" / "TESTER_z5_M2.htm"

    def test_doc_duoc_danh_sach_lenh(self):
        if not self.F.exists():
            self.skipTest("khong co bao cao tester mau")
        df = DLT.doc(self.F)
        self.assertGreater(len(df), 100)
        for c in ("luc", "so_hieu", "ma", "chieu"):
            self.assertIn(c, df.columns)
        self.assertEqual(set(df["chieu"].unique()) - {1, -1}, set())

    def test_lenh_MO_chi_la_MOT_NUA(self):
        """Bang Orders cua MT5 liet ke ca lenh mo lan lenh dong. Dem ca hai lam
        dau vao cho mimic thi nua so 'tin hieu mua' that ra la luc DONG mot vi
        the ban - va bo chung luat se hoc mot thu vo nghia."""
        if not self.F.exists():
            self.skipTest("khong co bao cao tester mau")
        df = DLT.doc(self.F)
        mo = DLT.vao_lenh_moi(df)
        self.assertLess(len(mo), len(df))
        self.assertGreater(len(mo), 0)

    def test_khop_bar_KHONG_BAO_GIO_lay_bar_SAU(self):
        """Khop 'gan nhat' co the tra ve bar SAU luc vao - do la nhin truoc."""
        import pandas as pd
        bar = pd.DataFrame(
            {"open": [1.0, 2.0, 3.0], "high": [1, 2, 3], "low": [1, 2, 3],
             "close": [1.0, 2.0, 3.0]},
            index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]))
        lenh = pd.DataFrame({"luc": pd.to_datetime(
            ["2020-01-02 23:59:00", "2020-01-01 00:00:00"])})
        i = DLT.khop_vao_bar(lenh, bar)
        self.assertEqual(i, [1, 0], "khop sang bar SAU luc vao = nhin truoc")

    def test_lenh_truoc_bar_dau_tien_bi_bo(self):
        import pandas as pd
        bar = pd.DataFrame(
            {"open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0]},
            index=pd.to_datetime(["2020-06-01"]))
        lenh = pd.DataFrame({"luc": pd.to_datetime(["2019-01-01"])})
        self.assertEqual(DLT.khop_vao_bar(lenh, bar), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
