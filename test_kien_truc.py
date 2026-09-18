# -*- coding: utf-8 -*-
"""Test cho `nhan/kien_truc.py` — bo sinh so do KIEN TRUC.

Thu duoc kiem o day la muc 0 (BAN DO THU MUC), them ngay 18/09 luc gom kho.
Cai dang test khong phai "ham co chay khong" ma la CAI PHANH cua no: thu muc
khong co trong bang vai tro thi phai HIEN RA o muc "chua khai vai tro", chu
khong duoc bien mat lang le. Do la thu giu so do khong rot sau vai thang.
"""
import unittest
from pathlib import Path

from nhan import kien_truc as KT


class DoThuMuc(unittest.TestCase):
    """`_do_thu_muc` dem that tren dia va khong nuot thu muc la."""

    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix="_kt_test_"))
        (self.tmp / "co_ten").mkdir()
        (self.tmp / "co_ten" / "a.txt").write_text("xin chao", encoding="utf-8")
        (self.tmp / "co_ten" / "b.txt").write_text("hai", encoding="utf-8")
        (self.tmp / "khong_ten").mkdir()
        (self.tmp / "khong_ten" / "c.txt").write_text("ba", encoding="utf-8")
        (self.tmp / "__pycache__").mkdir()
        (self.tmp / "__pycache__" / "rac.pyc").write_text("x" * 999, encoding="utf-8")
        (self.tmp / "file_roi.txt").write_text("khong phai thu muc", encoding="utf-8")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_dem_dung_so_file(self):
        da, _ = KT._do_thu_muc(self.tmp, {"co_ten": "co vai tro"})
        self.assertEqual([(n, so) for n, so, _ in da], [("co_ten", 2)])

    def test_thu_muc_la_KHONG_bien_mat_ma_roi_vao_chua_khai(self):
        """Day la cai phanh: them thu muc moi ma quen khai thi bao cao phai keu."""
        da, chua = KT._do_thu_muc(self.tmp, {"co_ten": "co vai tro"})
        self.assertEqual([n for n, _, _ in chua], ["khong_ten"])
        self.assertNotIn("khong_ten", [n for n, _, _ in da])

    def test_bo_qua_cache_khong_dem_lam_nhieu_so(self):
        da, chua = KT._do_thu_muc(self.tmp, {})
        ten = [n for n, _, _ in da] + [n for n, _, _ in chua]
        self.assertNotIn("__pycache__", ten)

    def test_file_roi_khong_bi_tinh_la_thu_muc(self):
        da, chua = KT._do_thu_muc(self.tmp, {})
        ten = [n for n, _, _ in da] + [n for n, _, _ in chua]
        self.assertNotIn("file_roi.txt", ten)


class BangVaiTro(unittest.TestCase):

    def test_moi_thu_muc_that_deu_da_duoc_khai(self):
        """Thu muc dang co tren dia ma chua khai vai tro thi test nay keu."""
        for goc, bang in ((KT.LAB.parent, KT.THU_MUC_GOC),
                          (KT.LAB, KT.THU_MUC_LAB)):
            _, chua = KT._do_thu_muc(goc, bang)
            self.assertEqual(
                [n for n, _, _ in chua], [],
                "thu muc chua khai vai tro trong %s — them vao THU_MUC_* "
                "cua nhan/kien_truc.py" % goc.name)

    def test_vai_tro_deu_la_chuoi_khong_rong(self):
        for bang in (KT.THU_MUC_GOC, KT.THU_MUC_LAB):
            for ten, mo in bang.items():
                self.assertIsInstance(mo, str)
                self.assertTrue(mo.strip(), ten)


class BaoCao(unittest.TestCase):

    def test_sinh_ra_du_cac_muc(self):
        vb = KT.sinh(in_ra=None)
        for muc in ("## 0. Thu muc", "## 1. Cua vao", "## 2. Tru",
                    "## 3. Lop nhan", "## 4. No kien truc", "## 5. So tong"):
            self.assertIn(muc, vb, muc)

    def test_no_kien_truc_khong_tinh_nghi_huu_va_co_che_ds(self):
        """Hai cho nay khong phai NO: mot da nghi huu, mot la co che tho."""
        vb = KT.sinh(in_ra=None)
        phan = vb.split("### 4.1")[1].split("### 4.2")[0]
        self.assertNotIn("nghi_huu/", phan)
        self.assertNotIn("co_che_ds/", phan)


if __name__ == "__main__":
    unittest.main()
