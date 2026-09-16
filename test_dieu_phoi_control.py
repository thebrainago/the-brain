"""Test duong dieu khien cua dieu_phoi (bat/dung/nhip)."""

import unittest
import sys
import json
import threading
import time
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dieu_phoi as DP


class ControlPlaneContractTest(unittest.TestCase):
    def test_trich_json_khi_stdout_co_log(self):
        got = DP._trich_json_cuoi('log truoc\n{"ok": true, "x": {"a": 1}}\nlog sau')
        self.assertEqual(got, {"ok": True, "x": {"a": 1}})

    def test_rc0_nhung_payload_loi_la_error(self):
        got = DP.danh_gia_ket_qua(
            0, {"loi": "provider rc=1"},
            {"trang_thai": "nghi", "chi_tiet_obj": {"loi": "provider rc=1"}}, True)
        self.assertEqual(got["status"], "error")
        self.assertFalse(got["ok"])

    def test_loi_thanh_phan_la_degraded(self):
        got = DP.danh_gia_ket_qua(
            0, {"phan_tich_sau": {"loi": "timeout"}},
            {"trang_thai": "nghi", "chi_tiet_obj": {}}, True)
        self.assertEqual(got["status"], "degraded")
        self.assertTrue(got["ok"])

    def test_bo_qua_hop_le_khong_phai_loi(self):
        got = DP.danh_gia_ket_qua(
            0, {"bo_qua": "chua den ky"},
            {"trang_thai": "nghi", "chi_tiet_obj": {"bo_qua": "chua den ky"}}, True)
        self.assertEqual(got["status"], "skipped")
        self.assertTrue(got["ok"])

    def test_thieu_nhip_moi_la_error_du_rc0(self):
        got = DP.danh_gia_ket_qua(
            0, {"ok": True}, {"trang_thai": "nghi", "chi_tiet_obj": {}}, False)
        self.assertEqual(got["status"], "error")
        self.assertIn("nhip_khong_cap_nhat", got["fatal"])

    def test_health_con_starting_khi_chua_du_nam_tru(self):
        self.assertEqual(DP._tong_quan_health({"EVO": {"status": "ok"}}), "starting")

    def test_scheduler_chay_song_song_va_dung_co_trat_tu(self):
        class FakeSO:
            @staticmethod
            def khoi_tao(): pass
            @staticmethod
            def don_viec_treo(): return 0
            @staticmethod
            def mot(sql, *args):
                if "SELECT luc" in sql:
                    return None
                return {"chi_tiet": "{}"}
            @staticmethod
            def ghi_su_kien(*args, **kwargs): pass
            @staticmethod
            def ghi_chi_so(*args, **kwargs): pass
            @staticmethod
            def bao_van_de(*args, **kwargs): pass
            @staticmethod
            def dong_van_de(*args, **kwargs): pass
            @staticmethod
            def nhip_tim(*args, **kwargs): pass

        class FakeJob:
            def __init__(self, _limit):
                self.active = True
                self.error = ""
            def close(self): pass

        lock = threading.Lock()
        active = 0
        max_active = 0
        da_chay = []

        def fake_chay(ten):
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
                da_chay.append(ten)
            time.sleep(0.12)
            with lock:
                active -= 1
            return {"tru": ten, "rc": 0, "giay": 0.12, "status": "ok", "ok": True,
                    "fatal": [], "degraded": [], "skip_reason": "", "tail": "",
                    "stdout_tail": "", "stderr_tail": "", "payload_keys": [],
                    "nhip": {"luc": "now", "trang_thai": "nghi"},
                    "resource_guard": "job"}

        with TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.multiple(
                    DP, SO=FakeSO, KHOA=root / "lock.json", DUNG=root / "stop",
                    LOG=root / "run.log", CONTROL=root / "control.json",
                    WindowsJob=FakeJob, chay_tru=fake_chay,
                    _khoa=lambda: True, _tha_khoa=lambda: None,
                    giu_may_thuc=lambda: True, tha_may_ngu=lambda: None,
                    _cpu_hien_tai=lambda: 10.0), \
                    mock.patch.object(sys, "argv", ["dieu_phoi.py", "--phut", "0.06"]):
                self.assertEqual(DP.main(), 0)
            state = json.loads((root / "control.json").read_text(encoding="utf-8"))

        self.assertGreaterEqual(max_active, 2)
        self.assertEqual(set(da_chay), set(DP.TRU))
        self.assertEqual(state["status"], "stopped")
        self.assertFalse(state["live"])


if __name__ == "__main__":
    unittest.main()
