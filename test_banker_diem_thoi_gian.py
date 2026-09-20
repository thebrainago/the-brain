# -*- coding: utf-8 -*-
"""BANKER: "gia tri CUA ngay do" KHAC "ngay do ta BIET gi" (20/09/2026).

## LOI KHAI DA SUA

Docstring cua `tru/banker.py` tung viet: *"moi seri vi mo duoc LUU VAO SO theo
thoi gian, nen sau nay tra loi duoc cau hoi 'luc do ta biet gi' (point-in-time)
chu khong phai lay ban moi nhat ap nguoc cho qua khu"*.

Cau do SAI voi chinh ma nguon ben duoi no. Bang la
`vi_mo(seri, ngay, gia_tri)` voi `ngay` lay thang tu cot dau CSV cua FRED -
tuc **NGAY CUA SO LIEU**. CPI thang 3 duoc ghi `2026-03-01` nhung giua thang 4
moi cong bo, nen mot cau hoi "ngay 2026-03-15 ta biet gi" tra ve so CPI thang
3: **nhin truoc mot thang**, va no khong lo ra o bat ky bang so nao.

## BO BAI NAY DO CAI GI

Khong chi do "ham moi chay duoc". No **do bang so cai nhin truoc cua ban cu**
(`do_nhin_truoc`) - vi mot ket luan "da sua" ma khong kem con so thi khong
phan biet duoc voi "van the nhung nay co ten ham moi".
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from nhan import so as SO
from tru import banker as B


class NenDbTam(unittest.TestCase):
    """Moi bai dung MOT `nao.db` rieng - khong dung so cai that."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_cu = SO.DB
        SO.DB = Path(self.tmp.name) / "nao.db"
        with SO.ket_noi() as cn:
            cn.executescript(SO.SCHEMA if hasattr(SO, "SCHEMA") else "")
            cn.execute("CREATE TABLE IF NOT EXISTS vi_mo(seri TEXT, ngay TEXT,"
                       " gia_tri REAL, PRIMARY KEY(seri, ngay))")

    def tearDown(self):
        SO.DB = self.db_cu
        self.tmp.cleanup()

    def _nap(self, seri, diem):
        with SO.ket_noi() as cn:
            for ngay, gt in diem:
                cn.execute("INSERT OR REPLACE INTO vi_mo(seri,ngay,gia_tri)"
                           " VALUES(?,?,?)", (seri, ngay, gt))


class DoTreCongBo(unittest.TestCase):
    def test_moi_seri_da_khai_deu_co_do_tre(self):
        """Them seri moi ma quen khai do tre thi no khong hong ngay - no chi
        lang le tu choi moi cau hoi point-in-time ve chinh no."""
        self.assertEqual(B.seri_chua_khai_do_tre(), [],
                         "co seri chua khai DO_TRE_NGAY")

    def test_gia_thi_truong_biet_NGAY_TRONG_NGAY_con_vi_mo_thi_KHONG(self):
        """Hieu chuan: neu MOI seri deu do tre 0 thi bang do vo nghia."""
        self.assertEqual(B.do_tre_cua("SP500"), 0)
        self.assertEqual(B.do_tre_cua("VIX"), 0)
        self.assertGreaterEqual(B.do_tre_cua("CPIAUCSL"), 30)
        self.assertGreaterEqual(B.do_tre_cua("UNRATE"), 30)
        self.assertGreaterEqual(B.do_tre_cua("VN_GDP"), 365)

    def test_seri_chua_khai_tra_None_chu_khong_tra_0(self):
        """`0` la mot con so trong y het da can nhac; `None` thi khong."""
        self.assertIsNone(B.do_tre_cua("SERI_KHONG_CO_THAT"))
        self.assertIsNone(B.ngay_biet_cua("SERI_KHONG_CO_THAT", "2026-01-01"))


class DocPointInTime(NenDbTam):
    def test_CPI_thang_3_CHUA_BIET_vao_giua_thang_3(self):
        self._nap("CPIAUCSL", [("2026-01-01", 300.0), ("2026-02-01", 301.0),
                               ("2026-03-01", 302.0)])
        r = B.gia_tri_biet_luc("CPIAUCSL", "2026-03-15")
        self.assertEqual(r["trang_thai"], "DAT", r)
        self.assertEqual(r["ngay"], "2026-01-01",
                         "giua thang 3 ma da thay CPI thang 2 hay thang 3")

    def test_va_BIET_ROI_sau_khi_qua_do_tre(self):
        """Hieu chuan chieu nguoc: mot bo loc tu choi TAT CA cho so lieu y het
        mot bo loc tot."""
        self._nap("CPIAUCSL", [("2026-03-01", 302.0)])
        self.assertEqual(B.gia_tri_biet_luc("CPIAUCSL", "2026-04-14")["trang_thai"],
                         "AM")
        r = B.gia_tri_biet_luc("CPIAUCSL", "2026-04-16")
        self.assertEqual(r["trang_thai"], "DAT", r)
        self.assertEqual(r["gia_tri"], 302.0)

    def test_seri_chua_khai_do_tre_la_CHUA_DO_DUOC_chu_khong_phai_AM(self):
        self._nap("LA_HOAC", [("2026-01-01", 1.0)])
        r = B.gia_tri_biet_luc("LA_HOAC", "2026-06-01")
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC", r)
        self.assertIn("DO_TRE_NGAY", r["ly_do"])

    def test_khong_co_diem_nao_la_AM_chu_khong_phai_CHUA_DO_DUOC(self):
        """Hai thu khac nhau: 'khai bao du nhung chua co so' KHAC 'khong biet
        luc nao thi ta biet so nay'."""
        self._nap("CPIAUCSL", [("2026-03-01", 302.0)])
        r = B.gia_tri_biet_luc("CPIAUCSL", "2020-01-01")
        self.assertEqual(r["trang_thai"], "AM", r)

    def test_moc_hong_la_CHUA_DO_DUOC(self):
        for moc in ("hom qua", "", "2026-13-45"):
            self.assertEqual(B.gia_tri_biet_luc("SP500", moc)["trang_thai"],
                             "CHUA_DO_DUOC", moc)


class DoBangSoCaiNhinTruoc(NenDbTam):
    """Bien mot loi khai thanh mot CON SO."""

    def test_CPI_nhin_truoc_hon_mot_thang(self):
        self._nap("CPIAUCSL", [("2026-01-01", 300.0), ("2026-02-01", 301.0),
                               ("2026-03-01", 302.0)])
        d = B.do_nhin_truoc("CPIAUCSL", "2026-03-15")
        self.assertEqual(d["trang_thai"], "DAT", d)
        self.assertEqual(d["tho_thay"], "2026-03-01")
        self.assertEqual(d["dung_ra_thay"], "2026-01-01")
        self.assertGreaterEqual(d["lech_ngay"], 28,
                                "phep doc tho khong he nhin truoc - kiem lai "
                                "phep do chu dung ket luan bang cu dung")
        self.assertEqual(d["lech_gia_tri"], 2.0)

    def test_World_Bank_nhin_truoc_HANG_NAM(self):
        """Do tre 400 ngay, nen phai chon `moc` DU XA de con so dung ton tai.

        Ban dau toi dat `moc = 2026-01-15` va doi thay so cua 2024. Sai: o moc
        do thi 2024-12-31 + 400 ngay = 2026-02-04, tuc **chua biet ca hai** ->
        dung ra la `AM`. Bai kiem sai, khong phai ma nguon - va no cho thay
        chinh do tre nay lon den muc nao.
        """
        self._nap("VN_GDP", [("2024-12-31", 6.5), ("2025-12-31", 7.1)])
        # Giua thang 1/2026: chua biet SO NAO ca.
        self.assertEqual(B.gia_tri_biet_luc("VN_GDP", "2026-01-15")["trang_thai"],
                         "AM")
        # Thang 6/2026: moi biet so cua NAM 2024.
        d = B.do_nhin_truoc("VN_GDP", "2026-06-01")
        self.assertEqual(d["trang_thai"], "DAT", d)
        self.assertEqual(d["tho_thay"], "2025-12-31")
        self.assertEqual(d["dung_ra_thay"], "2024-12-31")
        self.assertGreaterEqual(d["lech_ngay"], 365)

    def test_HIEU_CHUAN_NGUOC_gia_thi_truong_KHONG_nhin_truoc(self):
        """Neu ham do bao MOI seri deu nhin truoc thi no dang do thu khac."""
        self._nap("SP500", [("2026-03-10", 5000.0), ("2026-03-13", 5050.0)])
        d = B.do_nhin_truoc("SP500", "2026-03-13")
        self.assertEqual(d["trang_thai"], "DAT", d)
        self.assertEqual(d["lech_ngay"], 0,
                         "gia thi truong biet ngay trong ngay ma van bao nhin truoc")
        self.assertEqual(d["lech_gia_tri"], 0.0)


class BangBanVintage(NenDbTam):
    """`INSERT OR IGNORE` cu NUOT ban sua ma khong ai biet."""

    def test_bang_vi_mo_ban_ton_tai_va_giu_duoc_HAI_ban_cua_cung_mot_ngay(self):
        with SO.ket_noi() as cn:
            cn.executescript(
                "CREATE TABLE IF NOT EXISTS vi_mo_ban(seri TEXT, ngay TEXT,"
                " ngay_biet TEXT, gia_tri REAL, uoc_tinh INTEGER DEFAULT 1,"
                " luc_tai REAL, PRIMARY KEY(seri, ngay, ngay_biet))")
            for nb, gt in (("2026-04-15", 302.0), ("2026-05-15", 302.4)):
                cn.execute("INSERT INTO vi_mo_ban(seri,ngay,ngay_biet,gia_tri)"
                           " VALUES(?,?,?,?)", ("CPIAUCSL", "2026-03-01", nb, gt))
        n = SO.nhieu("SELECT ngay_biet,gia_tri FROM vi_mo_ban WHERE seri=? "
                     "AND ngay=? ORDER BY ngay_biet", "CPIAUCSL", "2026-03-01")
        self.assertEqual(len(n), 2, "khong giu duoc hai ban cua cung mot ngay")
        self.assertNotEqual(n[0]["gia_tri"], n[1]["gia_tri"])

    def test_schema_that_trong_so_py_co_bang_nay(self):
        """Bang phai nam trong SCHEMA chinh, khong phai chi trong bai kiem."""
        txt = Path("nhan/so.py").read_text(encoding="utf-8")
        self.assertIn("vi_mo_ban", txt)
        self.assertIn("ngay_biet", txt)


if __name__ == "__main__":
    unittest.main()


class KhoiMainPhaiNamCUOI(unittest.TestCase):
    """Loi cau truc toi tu mac trong chinh goi nay (20/09/2026).

    Toi noi muc DIEM THOI GIAN vao SAU khoi `if __name__ == "__main__"`. Cu
    phap hop le, `import` van chay, moi bai kiem van xanh - nhung
    `python -m tru.banker` se thuc thi `mot_luot()` TRUOC khi cac ham do ton
    tai. Mot `NameError` cho duoc kich hoat, va khong bai kiem nao bat duoc vi
    bai kiem `import` chu khong chay `__main__`.

    Bai nay doc AST: khoi `__main__` phai la thu CUOI CUNG o muc file.
    """

    def test_khong_dinh_nghia_gi_sau_khoi_main(self):
        import ast
        for f in ("tru/banker.py", "tru/seeker.py", "tru/quantlab.py",
                  "tru/evolution.py", "tru/nghi.py", "tru/finder.py"):
            p = Path(f)
            if not p.exists():
                continue
            cay = ast.parse(p.read_text(encoding="utf-8"))
            vt = [i for i, n in enumerate(cay.body)
                  if isinstance(n, ast.If) and ast.dump(n.test).find("__main__") >= 0]
            if not vt:
                continue
            sau = [n for n in cay.body[vt[0] + 1:]
                   if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Assign))]
            self.assertEqual(
                [getattr(n, "name", "<gan>") for n in sau], [],
                "%s: co dinh nghia SAU khoi __main__ - `python -m` se chay "
                "khoi do truoc khi chung ton tai" % f)
