# -*- coding: utf-8 -*-
"""Test cho `qwen/tho_code.py` - GIAO VIEC VIET MA CHO LLM RE.

Chu du an 19/09/2026: *"code bang claude rat ton, cau co the goi llm vao nhu
tren may toi khong, toi nghi se tiet kiem hon nhieu con cau lo giam sat thoi"*.

Dung, va `qwen/` da co san duong LLM. Cai thieu la mot THO CODE: dua mot don
hang, no sua file, chay lenh cham, lap den khi xanh.

## RANH GIOI - lay tu chinh `qwen/cong.py`

*"qwen doc va viet; code cham va chan."* Ti le do duoc: LLM dien `co_che` cho
48 khai bao, bo tham dinh bac 41, rong cuu 3.

Nen o day: **`pytest` quyet dinh dat/khong, khong phai LLM.** Tho code khong
duoc phep noi "toi lam xong roi".

## RAO CHAN QUAN TRONG NHAT: KHONG DUOC SUA FILE TEST

Day la kieu hong kinh dien cua moi vong lap "sua den khi xanh": mo hinh thay
sua test de hon sua ma, va no sua test. Luc do bang so van xanh con cai cong
thi bien mat.

Ngay hom nay chinh toi da o dung the kho do mot lan: bai
`test_ty_le_lot_tren_nhieu_phai_THAP` do o muc 50%, va cach de nhat la ha
nguong xuong. Neu ha thi phat hien "cham mot duong khong phan biet duoc gi" da
khong bao gio ton tai.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from qwen import tho_code as TC


def _du_an(tm: Path) -> Path:
    """Mot du an nho: mot module thieu ham, mot bai test doi ham do."""
    (tm / "mo_dun.py").write_text("def cong(a, b):\n    return 0\n",
                                  encoding="utf-8")
    (tm / "test_mo_dun.py").write_text(textwrap.dedent("""
        from mo_dun import cong

        def test_cong():
            assert cong(2, 3) == 5
    """), encoding="utf-8")
    return tm


def _don(tm: Path, **kw) -> dict:
    d = {"ma": "thu", "muc_tieu": "sua `cong` cho dung",
         "file_test": "test_mo_dun.py",
         "lenh_cham": [sys.executable, "-m", "pytest", "test_mo_dun.py", "-q"],
         "duoc_sua": ["mo_dun.py"], "so_vong_toi_da": 3, "goc": str(tm)}
    d.update(kw)
    return d


class ThoCodeSuaDenKhiXANH(unittest.TestCase):

    def setUp(self):
        self._tm = tempfile.TemporaryDirectory()
        self.tm = _du_an(Path(self._tm.name))

    def tearDown(self):
        self._tm.cleanup()

    def test_sua_duoc_va_bao_DAT(self):
        def llm(_nhac):
            return "```python\ndef cong(a, b):\n    return a + b\n```"
        r = TC.lam(_don(self.tm), hoi=llm)
        self.assertEqual(r["trang_thai"], "DAT", r.get("ly_do"))
        self.assertIn("a + b", (self.tm / "mo_dun.py").read_text(encoding="utf-8"))

    def test_LLM_noi_xong_ma_test_do_thi_KHONG_dat(self):
        """Tho code khong duoc phep tu phan. `pytest` quyet dinh."""
        def llm(_nhac):
            return "Toi da sua xong roi, moi thu deu dung.\n```python\ndef cong(a, b):\n    return 0\n```"
        r = TC.lam(_don(self.tm), hoi=llm)
        self.assertEqual(r["trang_thai"], "KHONG_DAT")

    def test_het_vong_thi_TRA_LAI_NGUYEN_TRANG(self):
        """Bo dang mot file da sua giua chung con te hon khong lam gi."""
        goc = (self.tm / "mo_dun.py").read_text(encoding="utf-8")

        def llm(_nhac):
            return "```python\ndef cong(a, b):\n    return 999\n```"
        TC.lam(_don(self.tm, so_vong_toi_da=2), hoi=llm)
        self.assertEqual((self.tm / "mo_dun.py").read_text(encoding="utf-8"), goc)

    def test_dem_so_vong_da_dung(self):
        dem = {"n": 0}

        def llm(_nhac):
            dem["n"] += 1
            return "```python\ndef cong(a, b):\n    return 0\n```"
        TC.lam(_don(self.tm, so_vong_toi_da=3), hoi=llm)
        self.assertEqual(dem["n"], 3)


class KHONG_DUOC_SUA_FILE_TEST(unittest.TestCase):
    """Rao chan quan trong nhat. Sua test de hon sua ma, nen phai chan CUNG."""

    def setUp(self):
        self._tm = tempfile.TemporaryDirectory()
        self.tm = _du_an(Path(self._tm.name))

    def tearDown(self):
        self._tm.cleanup()

    def test_don_hang_de_test_vao_duoc_sua_thi_BI_TU_CHOI(self):
        with self.assertRaises(ValueError):
            TC.lam(_don(self.tm, duoc_sua=["mo_dun.py", "test_mo_dun.py"]),
                   hoi=lambda _: "")

    def test_file_test_KHONG_DOI_sau_khi_chay(self):
        goc = (self.tm / "test_mo_dun.py").read_text(encoding="utf-8")

        def llm(_nhac):
            # Mo hinh co ga sua bai test - phai bi bo qua hoan toan.
            return ("```python:test_mo_dun.py\ndef test_cong():\n    assert True\n```"
                    "\n```python\ndef cong(a, b):\n    return a + b\n```")
        TC.lam(_don(self.tm), hoi=llm)
        self.assertEqual((self.tm / "test_mo_dun.py").read_text(encoding="utf-8"),
                         goc)

    def test_file_NGOAI_danh_sach_khong_bao_gio_bi_ghi(self):
        (self.tm / "ngoai.py").write_text("# dung cham\n", encoding="utf-8")

        def llm(_nhac):
            return "```python:ngoai.py\n# da bi sua\n```"
        TC.lam(_don(self.tm), hoi=llm)
        self.assertEqual((self.tm / "ngoai.py").read_text(encoding="utf-8"),
                         "# dung cham\n")


class BaTrangThaiKhongPhaiHai(unittest.TestCase):
    """`CHUA_DO_DUOC` la trang thai quan trong nhat cua du an nay."""

    def setUp(self):
        self._tm = tempfile.TemporaryDirectory()
        self.tm = _du_an(Path(self._tm.name))

    def tearDown(self):
        self._tm.cleanup()

    def test_LLM_hong_thi_CHUA_DO_DUOC_chu_khong_phai_KHONG_DAT(self):
        """Het quota hay lech ten provider deu tra loi rong. Doc no nhu
        'mo hinh khong sua duoc' la lan mot khau HONG voi mot ket qua am."""
        def llm(_nhac):
            raise RuntimeError("thieu OPENAI_API_KEY")
        r = TC.lam(_don(self.tm), hoi=llm)
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC")

    def test_LLM_tra_RONG_cung_la_CHUA_DO_DUOC(self):
        r = TC.lam(_don(self.tm), hoi=lambda _: "")
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC")

    def test_lenh_cham_KHONG_CHAY_DUOC_thi_CHUA_DO_DUOC(self):
        r = TC.lam(_don(self.tm, lenh_cham=["khong_he_co_lenh_nay"]),
                   hoi=lambda _: "```python\npass\n```")
        self.assertEqual(r["trang_thai"], "CHUA_DO_DUOC")

    def test_da_xanh_san_thi_khong_goi_LLM_lan_nao(self):
        (self.tm / "mo_dun.py").write_text("def cong(a, b):\n    return a + b\n",
                                           encoding="utf-8")
        dem = {"n": 0}

        def llm(_nhac):
            dem["n"] += 1
            return ""
        r = TC.lam(_don(self.tm), hoi=llm)
        self.assertEqual(r["trang_thai"], "DAT")
        self.assertEqual(dem["n"], 0, "goi LLM cho mot viec da xong - dot tien")


class NhacPhaiCO_DU_VIEC_CAN(unittest.TestCase):

    def setUp(self):
        self._tm = tempfile.TemporaryDirectory()
        self.tm = _du_an(Path(self._tm.name))

    def tearDown(self):
        self._tm.cleanup()

    def test_nhac_chua_bai_test_va_loi_that(self):
        giu = {}

        def llm(nhac):
            giu["nhac"] = nhac
            return "```python\ndef cong(a, b):\n    return a + b\n```"
        TC.lam(_don(self.tm), hoi=llm)
        n = giu["nhac"]
        self.assertIn("def test_cong", n, "nhac thieu bai test - do la dac ta")
        self.assertIn("mo_dun.py", n)
        self.assertIn("assert", n)

    def test_vong_sau_duoc_thay_LOI_cua_vong_truoc(self):
        nhac = []

        def llm(n):
            nhac.append(n)
            return "```python\ndef cong(a, b):\n    return 0\n```"
        TC.lam(_don(self.tm, so_vong_toi_da=2), hoi=llm)
        self.assertGreaterEqual(len(nhac), 2)
        self.assertIn("assert", nhac[1])
