# -*- coding: utf-8 -*-
from qwen import dieu_toc as DT

OK = lambda: {"cpu_pct": 50, "ram_trong_gb": 20, "commit_trong_gb": 30}


def test_tester_di_thang(tmp_path):
    assert DT.duoc_vao("TESTER", do=lambda: {"cpu_pct": 99, "ram_trong_gb": 0, "commit_trong_gb": 0}, d=tmp_path)[0]


def test_chan_theo_cpu_ram_commit(tmp_path):
    assert not DT.duoc_vao("CPU", do=lambda: {"cpu_pct": 95, "ram_trong_gb": 20, "commit_trong_gb": 30}, d=tmp_path)[0]
    assert not DT.duoc_vao("CPU", do=lambda: {"cpu_pct": 10, "ram_trong_gb": 1, "commit_trong_gb": 30}, d=tmp_path)[0]
    assert not DT.duoc_vao("CPU", do=lambda: {"cpu_pct": 10, "ram_trong_gb": 20, "commit_trong_gb": 5}, d=tmp_path)[0]


def test_mot_bo_khoi_dong_moi_20s(tmp_path):
    assert DT.duoc_vao("CPU", do=OK, d=tmp_path, bay_gio=1000)[0]
    assert not DT.duoc_vao("CPU", do=OK, d=tmp_path, bay_gio=1005)[0]
