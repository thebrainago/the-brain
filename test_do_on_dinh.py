# -*- coding: utf-8 -*-
"""DO HINH DANG CUA EDGE — va hai bat bien de no khong tro thanh curve-fitting.

Cong cu nay tra loi cau "chay di chay lai mot chien luoc thi co gi khac nhau
khong". Ranh gioi giua no va curve-fitting rat mong, nen ranh gioi do phai nam
trong bo kiem chu khong nam trong y dinh:

  1. **Khong tieu suat FDR.** Mot lan do 75 o la 75 lan goi cong; de chung vao
     so thi ngan sach cua ca ho bay sach trong mot lenh.
  2. **Khong chon tham so.** Dau ra la HINH DANG. Ngay khi mot ham o day tra ve
     "cau hinh tot nhat" thi cong cu doi phe.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)

import do_on_dinh as OD   # noqa: E402


class LanCanPhaiCanDoiQuanhTAM(unittest.TestCase):

    def test_tam_luon_nam_trong_lan_can(self):
        tam = {"n": 14, "vao": 30, "ra_": 55}
        self.assertIn(tam, OD.lan_can(tam))

    def test_moi_chieu_deu_co_hai_phia(self):
        """Lan can lech mot phia lam `do_doc` va `boi_dinh` deu sai."""
        tam = {"n": 14}
        gt = sorted(x["n"] for x in OD.lan_can(tam))
        self.assertLess(min(gt), 14, "khong co diem nao NHO hon tam")
        self.assertGreater(max(gt), 14, "khong co diem nao LON hon tam")

    def test_khong_sinh_tham_so_vo_nghia(self):
        for x in OD.lan_can({"n": 2, "vao": 5}):
            self.assertGreater(x["n"], 0)
            self.assertGreater(x["vao"], 0)

    def test_bool_khong_co_lan_can(self):
        ds = OD.lan_can({"chi_mua": True, "n": 9})
        self.assertEqual({x["chi_mua"] for x in ds}, {True},
                         "sinh lan can cho mot cong tac bat/tat")

    def test_tran_an_toan_van_giu_tam(self):
        """Vuot tran thi RUT so buoc, khong duoc cat bua danh sach."""
        tam = {"a": 10, "b": 20, "c": 30, "d": 40}
        ds = OD.lan_can(tam, toi_da=40)
        self.assertLessEqual(len(ds), 41)
        self.assertIn(tam, ds)


class DatTenHinhDangPhaiPhanBietDUOC(unittest.TestCase):
    """Chieu xuoi VA chieu nguoc: mot bo do luon keu 'cai gai' cung vo dung
    nhu mot bo do luon keu 'cao nguyen'."""

    def test_cai_gai_khi_dinh_cao_han(self):
        ten = OD._dat_ten(ty_le_duong=0.9, trung_vi=0.5, tot_nhat=9.0, a_tam=9.0)
        self.assertIn("CAI GAI", ten)

    def test_cai_gai_khi_da_so_lan_can_am(self):
        ten = OD._dat_ten(ty_le_duong=0.2, trung_vi=-1.0, tot_nhat=6.0, a_tam=6.0)
        self.assertIn("CAI GAI", ten)

    def test_cao_nguyen_khi_deu_va_khong_co_dinh_noi(self):
        ten = OD._dat_ten(ty_le_duong=0.95, trung_vi=3.0, tot_nhat=4.0, a_tam=3.5)
        self.assertIn("CAO NGUYEN", ten)

    def test_khong_do_duoc_thi_noi_la_khong_do_duoc(self):
        """Khong duoc bien 'chua do' thanh mot ket luan."""
        self.assertEqual(OD._dat_ten(0.9, 1.0, 2.0, None), "khong_do_duoc")


class KhongDuocTieuSuatFDR(unittest.TestCase):
    """Bat bien 1. Do bang cach DEM DONG trong so, khong bang doc code."""

    def setUp(self):
        import tempfile
        from nhan import so as SO
        self.SO = SO
        self.tam = Path(tempfile.mkdtemp(prefix="ondinh_"))
        self.db_cu = SO.DB
        SO.DB = self.tam / "nao.db"
        SO.khoi_tao()

    def tearDown(self):
        import shutil
        self.SO.DB = self.db_cu
        shutil.rmtree(self.tam, ignore_errors=True)

    def _dem(self):
        return (self.SO.mot("SELECT COUNT(*) c FROM fdr")["c"],
                self.SO.mot("SELECT COUNT(*) c FROM gia_thuyet")["c"])

    def test_do_mot_o_khong_ghi_gi_vao_so(self):
        truoc = self._dem()
        r = OD.do_mot_o("rsi_dao_chieu", {"n": 14, "vao": 30, "ra_": 55},
                        "AUDCAD", "H4")
        self.assertIsNotNone(r.get("alpha") or r.get("loi"))
        self.assertEqual(self._dem(), truoc,
                         "mot lan DO da ghi vao so - 75 o se dot sach ngan sach FDR")


class KhongDuocCHONThamSo(unittest.TestCase):
    """Bat bien 2, kiem bang AST: khong ham nao duoc tra ve 'tot nhat'."""

    def test_khong_ham_nao_ten_kieu_chon_toi_uu(self):
        import ast
        import inspect
        cay = ast.parse(inspect.getsource(OD))
        xau = [n.name for n in ast.walk(cay)
               if isinstance(n, ast.FunctionDef)
               and any(t in n.name.lower()
                       for t in ("chon", "toi_uu", "best", "optimi"))]
        self.assertEqual(xau, [], f"co ham chon tham so: {xau}")

    def test_khong_ghi_gi_vao_bang_gia_thuyet(self):
        import inspect
        nguon = inspect.getsource(OD).upper()
        for cam in ("INSERT INTO GIA_THUYET", "UPDATE GIA_THUYET",
                    "DANG_KY_GIA_THUYET", "DOI_TRANG_THAI_GT"):
            self.assertNotIn(cam, nguon, f"cong cu DO lai ghi vao so: {cam}")


if __name__ == "__main__":
    unittest.main()
