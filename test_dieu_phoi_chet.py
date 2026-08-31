# -*- coding: utf-8 -*-
"""SUPERVISOR CHET MA KHONG DE LAI GI — lo hong te nhat cua mot he 24/7.

Xay ra that luc **09:19:03 ngay 31/08/2026**, 36 giay sau khi bat he: watchdog
ghi duoc dung mot dong

    WATCHDOG supervisor thoat rc=1

va **khong mot dong traceback nao ton tai o bat ky dau**. `dieu_phoi.log` chi
co dong dung binh thuong, `dieu_phoi_nen.log` khong co gi, so cai khong co gi.

Hai nguyen nhan chong len nhau:
  1. `main()` khong bat `BaseException`, nen loi bay qua `finally` (in ra dong
     "dung dieu phoi" tuong nhu binh thuong) roi ra thang interpreter -> rc=1.
  2. Watchdog goi `Popen` voi `CREATE_NO_WINDOW` ma khong truyen `stdout`/
     `stderr`, nen traceback di vao mot handle khong ai doc.

Vi sao no dat: chinh cau "khong ro nguyen nhan" nay da duoc ghi vao so cai cho
**346,1 gio gian doan**. Mot he tu bao cao suc khoe ma khong biet vi sao minh
chet thi moi so lieu ve thoi gian song deu vo nghia.

Bai kiem duoi day cho no chet CO CHU Y roi doi hai thu: ma thoat rieng (4, de
watchdog phan biet voi rc=1 vo danh) va traceback nam trong nhat ky.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

LAB = str(Path(__file__).resolve().parent)
if LAB not in sys.path:
    sys.path.insert(0, LAB)


class SupervisorPhaiKhaiBaoCaiChetCuaMinh(unittest.TestCase):

    def setUp(self):
        import tempfile
        import dieu_phoi as DP
        from nhan import so as SO

        self.DP = DP
        self.tam = Path(tempfile.mkdtemp(prefix="dp_chet_"))
        self.cu = {"LOG": DP.LOG, "KHOA": DP.KHOA, "DUNG": DP.DUNG,
                   "CONTROL": DP.CONTROL, "DB": SO.DB,
                   "cpu": DP._cpu_hien_tai, "argv": sys.argv,
                   "khoa": DP._khoa, "tha": DP._tha_khoa,
                   "chay_tru": DP.chay_tru}
        # Khoa la MUTEX cap he: mot supervisor that dang chay se lam bai kiem
        # nay thoat som (ma 3) va khong bao gio cham vao duong dang kiem. Bo
        # khoa o day la dung pham vi - bai kiem nay hoi ve DUONG CHET.
        DP._khoa = lambda: True
        DP._tha_khoa = lambda: None
        # Va KHONG duoc cho no chay tru that: mot luot QUANTLAB that la ~425
        # giay va se sinh tien trinh con ghi vao so cai that.
        DP.chay_tru = lambda ten: {
            "tru": ten, "rc": 0, "giay": 0.0, "status": "ok", "ok": True,
            "fatal": [], "degraded": [], "skip_reason": "", "tail": "",
            "stdout_tail": "", "stderr_tail": "", "payload_keys": [],
            "nhip": None, "resource_guard": "none"}
        DP.LOG = self.tam / "dieu_phoi.log"
        DP.KHOA = self.tam / "dieu_phoi.lock"
        DP.DUNG = self.tam / "DUNG_LAI"
        DP.CONTROL = self.tam / "control_plane.json"
        SO.DB = self.tam / "nao.db"          # KHONG duoc cham so cai that
        sys.argv = ["dieu_phoi.py", "--phut", "0.05"]

    def tearDown(self):
        import shutil
        from nhan import so as SO
        DP = self.DP
        DP.LOG, DP.KHOA, DP.DUNG = self.cu["LOG"], self.cu["KHOA"], self.cu["DUNG"]
        DP.CONTROL, SO.DB = self.cu["CONTROL"], self.cu["DB"]
        DP._cpu_hien_tai = self.cu["cpu"]
        DP._khoa, DP._tha_khoa = self.cu["khoa"], self.cu["tha"]
        DP.chay_tru = self.cu["chay_tru"]
        sys.argv = self.cu["argv"]
        shutil.rmtree(self.tam, ignore_errors=True)

    def _cho_chet(self):
        """Cho mot loi noi ra tu GIUA vong lap, dung cho no bay len tren."""
        def _no(*_a, **_k):
            raise RuntimeError("loi co y de kiem duong chet")
        self.DP._cpu_hien_tai = _no
        return self.DP.main()

    def test_ma_thoat_rieng_chu_khong_phai_rc1_vo_danh(self):
        ma = self._cho_chet()
        self.assertEqual(ma, 4, "chet vi loi khong bat ma van tra ma thoat cu")

    def test_traceback_nam_trong_nhat_ky(self):
        self._cho_chet()
        van = self.DP.LOG.read_text(encoding="utf-8", errors="replace")
        self.assertIn("SUPERVISOR CHET", van)
        self.assertIn("RuntimeError", van)
        self.assertIn("loi co y de kiem duong chet", van)
        self.assertIn("Traceback", van, "khong ghi lai traceback thi van la "
                                        "'khong ro nguyen nhan'")

    def test_van_de_duoc_ghi_vao_so(self):
        from nhan import so as SO
        self._cho_chet()
        v = SO.mot("SELECT * FROM van_de WHERE ma='dieu_phoi_chet_khong_bat'")
        self.assertIsNotNone(v, "chet ma khong bao van de - EVO se khong thay")
        self.assertEqual(v["muc"], "NANG")

    def test_chay_binh_thuong_van_tra_0(self):
        """Chieu nguoc lai: dung het gio thi ma thoat phai la 0, khong phai 4."""
        sys.argv = ["dieu_phoi.py", "--phut", "0.001"]
        self.assertEqual(self.DP.main(), 0)


class WatchdogPhaiBatDUOCStdioCuaCon(unittest.TestCase):
    """Nua con lai cua lo hong: watchdog phai TRUYEN handle, khong duoc trong
    cho tien trinh con thua ke - `CREATE_NO_WINDOW` cat mat duong thua ke do."""

    def test_popen_truyen_stdout_va_stderr(self):
        import ast
        import inspect
        import giam_sat_dieu_phoi as GS

        cay = ast.parse(inspect.getsource(GS))
        goi = [n for n in ast.walk(cay)
               if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == "Popen"]
        self.assertTrue(goi, "khong tim thay loi goi Popen nao")
        for g in goi:
            khoa = {k.arg for k in g.keywords}
            self.assertIn("stdout", khoa, "Popen khong truyen stdout - "
                                          "traceback cua con se bay mat")
            self.assertIn("stderr", khoa, "Popen khong truyen stderr")

    def test_co_khai_bao_file_stdio_rieng(self):
        import giam_sat_dieu_phoi as GS
        self.assertTrue(hasattr(GS, "LOG_CON"))
        self.assertNotEqual(GS.LOG_CON, GS.LOG,
                            "tron stdio tho vao nhat ky watchdog thi mot "
                            "traceback dai lam troi nhat ky")


if __name__ == "__main__":
    unittest.main()
