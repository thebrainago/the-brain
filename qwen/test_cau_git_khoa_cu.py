# -*- coding: utf-8 -*-
import os, time
from qwen import cau_git as CG


def test_khoa_cu_khong_chan(tmp_path):
    k = tmp_path / ".khoa_tester"
    assert not CG._khoa_con_song(k)
    k.write_text("1")
    assert CG._khoa_con_song(k)
    cu = time.time() - CG.KHOA_CU_GIAY - 10
    os.utime(k, (cu, cu))
    assert not CG._khoa_con_song(k)


def test_don_tester_can_mt5_du_khong_khai():
    d = {"lan": "TESTER", "lenh": []}
    assert not CG._hop_may(d, "nha-p1", ["windows", "data"])
    assert CG._hop_may(d, "nha-m1", ["windows", "mt5", "data"])
    assert CG._hop_may({"lan": "CPU"}, "nha-p1", ["windows"])
