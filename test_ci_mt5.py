# -*- coding: utf-8 -*-
"""Test cho duong MT5 tren GitHub Actions (`.github/`).

Cong `kiem_ket_qua_ci` la cho quyet dinh RONG KHONG PHAI AM. Mot job xanh voi
bang so rong la thu nguy hiem nhat trong ca duong nay, nen cho do phai co test
- ke ca khi ban than workflow chi chay duoc tren runner Windows.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC / ".github" / "scripts"))

import kiem_ket_qua_ci as K  # noqa: E402


class DocSoDeal(unittest.TestCase):

    def test_doc_duoc_tu_bao_cao_HTML(self):
        self.assertEqual(K.doc_so_deal("<td>Total Trades</td><td>137</td>"), 137)

    def test_doc_duoc_dang_XML(self):
        self.assertEqual(K.doc_so_deal("<deals>42</deals>"), 42)

    def test_KHONG_TIM_THAY_tra_None_chu_khong_tra_0(self):
        """0 la "da do va bang 0"; None la "khong do duoc". Gop hai cai lam mot
        chinh la lop loi ma ca duong nay sinh ra de chan."""
        self.assertIsNone(K.doc_so_deal("<html>khong co gi</html>"))


class _ChayCong:
    def _chay(self, tao) -> int:
        with tempfile.TemporaryDirectory() as tm:
            cu = Path.cwd()
            os.chdir(tm)
            try:
                tao(Path(tm))
                return subprocess.run(
                    [sys.executable, str(GOC / ".github" / "scripts"
                                         / "kiem_ket_qua_ci.py"), "--ma", "X"],
                    capture_output=True, text=True).returncode
            finally:
                os.chdir(cu)


class CongPhaiCHAN_DUNG(_ChayCong, unittest.TestCase):

    def test_khong_co_thu_muc_ket_qua_thi_DO(self):
        self.assertNotEqual(self._chay(lambda tm: None), 0)

    def test_co_thu_muc_nhung_khong_bao_cao_thi_DO(self):
        self.assertNotEqual(
            self._chay(lambda tm: (tm / "ci_out").mkdir()), 0)

    def test_bao_cao_0_DEAL_thi_DO(self):
        """Lich su khong tai duoc, sai ten symbol, khung khong co du lieu -
        ca ba deu cho dung con so nay. Khong duoc doc la 'khong ra lenh'."""
        def tao(tm):
            d = tm / "ci_out"
            d.mkdir()
            (d / "bc.htm").write_text("<td>Total Trades</td><td>0</td>",
                                      encoding="utf-8")
        self.assertNotEqual(self._chay(tao), 0)

    def test_bao_cao_co_deal_thi_QUA(self):
        """Hieu chuan chieu nguoc: mot cong tu choi TAT CA cho so lieu y het
        mot cong tot."""
        def tao(tm):
            d = tm / "ci_out"
            d.mkdir()
            (d / "bc.htm").write_text("<td>Total Trades</td><td>137</td>",
                                      encoding="utf-8")
        self.assertEqual(self._chay(tao), 0)


class WorkflowPhaiHOP_LE(unittest.TestCase):

    def setUp(self):
        self.p = GOC / ".github" / "workflows" / "mt5-tester.yml"

    def test_file_ton_tai(self):
        self.assertTrue(self.p.exists())

    def test_yaml_doc_duoc_va_co_hai_job(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("khong co pyyaml")
        d = yaml.safe_load(self.p.read_text(encoding="utf-8"))
        self.assertIn("chuan_bi", d["jobs"])
        self.assertIn("tester", d["jobs"])

    def test_KHONG_huy_luot_dang_chay(self):
        """Huy giua chung de lai mot bao cao viet do dang, va bao cao do dang
        doc y het mot ket qua am."""
        try:
            import yaml
        except ImportError:
            self.skipTest("khong co pyyaml")
        d = yaml.safe_load(self.p.read_text(encoding="utf-8"))
        self.assertIs(d["concurrency"]["cancel-in-progress"], False)

    def test_mot_ma_hong_khong_keo_do_ca_me(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("khong co pyyaml")
        d = yaml.safe_load(self.p.read_text(encoding="utf-8"))
        self.assertIs(d["jobs"]["tester"]["strategy"]["fail-fast"], False)

    def test_KHONG_co_mat_khau_nam_trong_file(self):
        """Bi mat phai di qua `secrets:`, khong bao gio nam trong repo."""
        vb = self.p.read_text(encoding="utf-8")
        for xau in ("password=", "Password="):
            for d in vb.splitlines():
                if xau in d and "secrets." not in d and "MT5_PASSWORD" not in d:
                    self.fail("co ve co mat khau trong workflow: %s" % d[:60])
