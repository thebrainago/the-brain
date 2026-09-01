# -*- coding: utf-8 -*-
"""HIEN PHAP CUA BO TEST — cac chot chan chinh bo test tu lua doi minh.

Vi sao can. Bo test la TRONG TAI: no la thu duy nhat noi duoc mot thay doi co
lam hong bat bien nao khong. Mot trong tai co the bi mua chuoc theo hai cach,
va ca hai da xay ra that trong du an nay:

1. **Test rong.** Quet AST toan bo bo test ben `ds` ngay 21/08/2026 tim ra
   **33 test tu bao PASSED ma khong kiem gi** - trong do co dung hai chot quan
   trong nhat: `test_vault_leak` (chong ro kho niem phong) va `test_lookahead`
   (chong nhin truoc). Ca hai chi co `assert True`.

2. **Module khong ai kiem.** Mot module co the song ca doi ma khong mot bai
   kiem nao cham vao. Do 30/08/2026 tren `lab`: `canary.py` (thu GAC ca engine),
   `quant_plan.py` (giu bat bien pre-registration) va `evolution.py` (tru chiu
   trach nhiem phat hien he hong) deu **khong co file test nao**.

Hai chot duoi day chan ca hai. Chot thu hai la mot CAI COC: danh sach
`CHUA_CO_TEST` chi duoc phep NGAN LAI. Them module moi ma quen viet test thi
do; go duoc mot ten khoi danh sach ma quen cap nhat cung do.

Cong nay la dieu kien bat buoc truoc khi cho nhieu agent song song viet test:
mot agent toi uu theo "bo test xanh" se viet `assert True` neu khong co gi chan.
"""
from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

#: Module trong `nhan/` va `tru/` chua co file test nao nhac den.
#:
#: **Danh sach nay chi duoc NGAN LAI.** Viet test cho module nao thi xoa ten do
#: khoi day - `test_danh_sach_khong_con_ten_thua` se bao neu quen.
CHUA_CO_TEST = {
    "nhan/tu_dang_nhap.py",
}

#: File test khong tinh la "bai kiem cua module X" du co nhac ten X.
BO_QUA_FILE_TEST = {"test_hien_phap.py"}


def _cac_ham_test(cay: ast.AST):
    """Sinh (ten, node) cho moi ham test - ke ca method trong class TestCase."""
    for node in ast.walk(cay):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name.startswith("test"):
            yield node.name, node


def _la_test_rong(node: ast.AST) -> bool:
    """True neu ham nay tu bao PASSED ma khong kiem dieu gi."""
    dumped = ast.dump(node)
    khang_dinh = [n for n in ast.walk(node) if isinstance(n, ast.Assert)]
    # `assert True` / `assert 1` la hang so -> khong kiem gi.
    that_su = [a for a in khang_dinh if not isinstance(a.test, ast.Constant)]
    ten_goi = {
        (n.func.attr if isinstance(n.func, ast.Attribute)
         else getattr(n.func, "id", "")) or ""
        for n in ast.walk(node) if isinstance(n, ast.Call)
    }
    uy_thac = any(re.search(r"assert|validate|verify|check|fail|kiem|doi_chieu", t)
                  for t in ten_goi)
    co_raise = any(isinstance(n, ast.Raise) for n in ast.walk(node))
    return not (that_su or uy_thac or co_raise or "raises" in dumped)


class KhongTestRong(unittest.TestCase):

    def test_khong_ham_test_nao_tu_pass_ma_khong_kiem_gi(self):
        rong = []
        for f in sorted(LAB.glob("test_*.py")):
            if f.name in BO_QUA_FILE_TEST:
                continue
            cay = ast.parse(f.read_text(encoding="utf-8-sig"))
            for ten, node in _cac_ham_test(cay):
                if _la_test_rong(node):
                    rong.append(f"{f.name}::{ten}")
        self.assertEqual(
            rong, [],
            "test rong (tu bao PASSED ma khong kiem gi):\n  " + "\n  ".join(rong))

    def test_chinh_phep_do_nay_bat_duoc_test_rong(self):
        """Hieu chuan HAI CHIEU: mot bo do khong bat duoc gi thi vo dung.

        Cung mot bai hoc voi `null_ty_le_lot` - mot cong TU CHOI TAT CA cho so
        lieu y het mot cong hieu chuan tot, nen phep do phai tu chung minh la
        no NHAY truoc khi ket qua am tinh cua no dang tin.
        """
        rong = ast.parse("def test_gia(self):\n    assert True\n").body[0]
        that = ast.parse("def test_that(self):\n    assert 1 + 1 == 2\n").body[0]
        uy_thac = ast.parse("def test_uy(self):\n    self.assertEqual(1, 1)\n").body[0]
        self.assertTrue(_la_test_rong(rong), "khong bat duoc `assert True`")
        self.assertFalse(_la_test_rong(that), "bao nham mot test that")
        self.assertFalse(_la_test_rong(uy_thac), "bao nham assertEqual")


class MoiModuleDeuCoNguoiKiem(unittest.TestCase):

    @staticmethod
    def _ban_do() -> dict[str, int]:
        """{duong dan module: so file test co nhac ten module}."""
        van_test = {}
        for f in sorted(LAB.glob("test_*.py")):
            if f.name in BO_QUA_FILE_TEST:
                continue
            van_test[f.name] = f.read_text(encoding="utf-8-sig")
        ra = {}
        for thu in ("nhan", "tru"):
            for m in sorted((LAB / thu).glob("*.py")):
                if m.name == "__init__.py":
                    continue
                ten = m.stem
                ra[f"{thu}/{m.name}"] = sum(
                    1 for v in van_test.values()
                    if re.search(rf"\b{re.escape(ten)}\b", v))
        return ra

    def test_module_moi_khong_duoc_ra_doi_ma_khong_co_test(self):
        thieu = sorted(k for k, n in self._ban_do().items()
                       if n == 0 and k not in CHUA_CO_TEST)
        self.assertEqual(
            thieu, [],
            "module khong co file test nao nhac den, va khong nam trong "
            "CHUA_CO_TEST:\n  " + "\n  ".join(thieu) +
            "\n\nViet test, hoac them vao CHUA_CO_TEST kem ly do.")

    def test_danh_sach_khong_con_ten_thua(self):
        """CHUA_CO_TEST chi duoc ngan lai. Ten da co test phai bi go ra."""
        ban_do = self._ban_do()
        khong_ton_tai = sorted(k for k in CHUA_CO_TEST if k not in ban_do)
        da_co_test = sorted(k for k in CHUA_CO_TEST if ban_do.get(k, 0) > 0)
        self.assertEqual(khong_ton_tai, [],
                         "CHUA_CO_TEST ke ten module khong con ton tai: "
                         + ", ".join(khong_ton_tai))
        self.assertEqual(
            da_co_test, [],
            "cac module nay DA co test - go khoi CHUA_CO_TEST: "
            + ", ".join(da_co_test))


if __name__ == "__main__":
    unittest.main()
