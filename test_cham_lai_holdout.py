# -*- coding: utf-8 -*-
"""Chot chan "mot gia thuyet cham holdout MOT lan" phai nam o CHO GHI.

Truoc 01/09/2026 luat nay chi duoc viet o cac CHO GOI trong `tru/quantlab.py`.
Do that tren so cai: 373 gia thuyet / 1.270 lan cham (3,40 lan moi gia thuyet),
mot gia thuyet bi cham 10 lan, 3 gia thuyet di FAIL -> PASS. Cac cho goi hien
tai deu co kiem, va tu 25/08 ty le da ve 1,00 - nhung mot luat chi song neu no
nam o cho HEP NHAT ma moi duong phai di qua, chu khong nam o tung nguoi goi.
"""
from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path

from nhan import so as SO


class ChamLaiPhaiKhaiLyDo(unittest.TestCase):
    """Cac bai o day GHI vao bang `ket_qua`, nen phai ghi vao so TAM.

    Ban dau (01/09) lop nay khong tro `SO.DB` di dau ca, va no da bom **60
    dong `test_cham_lai_*` vao so cai THAT** trong mot buoi chieu - moi lan
    chay `b test` them ~10 dong. Chung khong vao bang `fdr` nen ngan sach
    quyet dinh khong viec gi, nhung `so_ket_qua_tho` thi dem ca chung.
    Bo test khong duoc lam ban chinh cai so ma no dang di kiem.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._db_cu = SO.DB
        SO.DB = Path(self._tmp.name) / "nao_test.db"
        SO.khoi_tao()

    def tearDown(self):
        SO.DB = self._db_cu
        self._tmp.cleanup()

    def _gt_moi(self) -> str:
        return "test_cham_lai_" + uuid.uuid4().hex[:12]

    def _ghi(self, ma: str, verdict: str = "FAIL", **kw) -> int:
        return SO.ghi_ket_qua(ma, {"x": 1}, {"y": 2}, verdict, 0.5, 0.0, 0.0, **kw)

    def test_lan_dau_ghi_duoc(self):
        ma = self._gt_moi()
        self.assertGreater(self._ghi(ma), 0)

    def test_lan_hai_KHONG_khai_ly_do_thi_NEM_LOI(self):
        """Diem cot loi: khong duoc lang le ghi de - phai on ao."""
        ma = self._gt_moi()
        self._ghi(ma, "FAIL")
        with self.assertRaises(SO.ChamLaiHoldout):
            self._ghi(ma, "PASS")

    def test_lan_hai_CO_khai_ly_do_thi_ghi_duoc(self):
        """Du lieu moi den la ly do chinh dang - nhung phai co y thuc."""
        ma = self._gt_moi()
        cu = self._ghi(ma, "FAIL")
        moi = self._ghi(ma, "PASS", cham_lai="du lieu moi den 2026-09")
        self.assertNotEqual(cu, moi)
        r = SO.mot("SELECT superseded_by FROM ket_qua WHERE id=?", cu)
        self.assertEqual(r["superseded_by"], moi)

    def test_loi_noi_ro_gia_thuyet_nao(self):
        ma = self._gt_moi()
        self._ghi(ma)
        with self.assertRaises(SO.ChamLaiHoldout) as e:
            self._ghi(ma)
        self.assertIn(ma, str(e.exception))
        self.assertIn("cham_lai", str(e.exception))


class ChoGoiVanPhaiTUKIEM(unittest.TestCase):
    """Chot chan o cho ghi la LUOI CUOI, khong phai ly do de bo kiem o cho goi:
    de ham nem loi moi lan la bien mot luat thanh mot su co van hanh."""

    def test_quantlab_van_kiem_truoc_khi_goi(self):
        import inspect
        from tru import quantlab as QL
        src = inspect.getsource(QL)
        self.assertGreaterEqual(
            src.count("superseded_by IS NULL"), 4,
            "cho goi trong quantlab phai tu kiem truoc, khong dua het cho luoi cuoi")


if __name__ == "__main__":
    unittest.main()
