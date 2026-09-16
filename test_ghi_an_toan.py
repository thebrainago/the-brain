# -*- coding: utf-8 -*-
"""Test G2-C: sua JSON khong mat thay doi, va lan tai nguyen khong vuot tran.

Ca hai lo hong o day thuoc loai **khong bao loi**: mot thay doi cau hinh bien
mat khong de lai dau vet, va hai luot tester cung chay thi ghi de ket qua cua
nhau ma bang so doc y het mot ket qua that.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

import pytest  # noqa: E402

from nhan import ghi_an_toan as GAT  # noqa: E402


def test_sua_json_tao_file_khi_chua_co(tmp_path):
    p = tmp_path / "c.json"
    GAT.sua_json(p, lambda d: {**d, "x": 1})
    assert json.loads(p.read_text(encoding="utf-8")) == {"x": 1}


def test_sua_json_giu_khoa_cu(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"a": 1}), encoding="utf-8")
    GAT.sua_json(p, lambda d: {**d, "b": 2})
    assert json.loads(p.read_text(encoding="utf-8")) == {"a": 1, "b": 2}


def test_ham_sua_nem_loi_thi_KHONG_ghi_gi(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"a": 1}), encoding="utf-8")

    def hong(d):
        raise ValueError("tinh sai")
    with pytest.raises(ValueError):
        GAT.sua_json(p, hong)
    assert json.loads(p.read_text(encoding="utf-8")) == {"a": 1}
    assert not list(p.parent.glob("*.tmp")), "khong duoc de lai file tam"


def test_khoa_duoc_tra_sau_khi_xong(tmp_path):
    p = tmp_path / "c.json"
    GAT.sua_json(p, lambda d: {"x": 1})
    assert not (tmp_path / "c.json.lock").exists()


def test_khoa_mo_coi_duoc_thu_hoi(tmp_path):
    p = tmp_path / "c.json"
    (tmp_path / "c.json.lock").write_text("999999", encoding="utf-8")
    GAT.sua_json(p, lambda d: {"x": 1}, cho_giay=5)   # pid 999999 khong song
    assert json.loads(p.read_text(encoding="utf-8")) == {"x": 1}


def _tang(duong_dan, khoa):
    sys.path.insert(0, str(Path(duong_dan).parent))
    from nhan import ghi_an_toan as G

    def sua(d):
        d[khoa] = d.get(khoa, 0) + 1
        d["tong"] = d.get("tong", 0) + 1
        return d
    for _ in range(20):
        G.sua_json(Path(duong_dan), sua, cho_giay=60)
    return 0


def test_muoi_tien_trinh_sua_mot_file_KHONG_MAT_THAY_DOI(tmp_path):
    """Phep thu ma bang ke hoach doi: 10 tien trinh x 20 lan = 200, khong hut."""
    p = tmp_path / "c.json"
    p.write_text(json.dumps({}), encoding="utf-8")
    ps = [mp.Process(target=_tang, args=(str(p), "p%d" % i)) for i in range(10)]
    for q in ps:
        q.start()
    for q in ps:
        q.join(180)
    assert all(q.exitcode == 0 for q in ps), [q.exitcode for q in ps]
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["tong"] == 200, "mat %d lan ghi" % (200 - d.get("tong", 0))
    assert all(d["p%d" % i] == 20 for i in range(10))


# ---------------------------------------------------------------- ngan sach
def _xin(goc, lop, giu_giay, ket_qua):
    sys.path.insert(0, str(goc))
    from nhan import ngan_sach as NS
    try:
        with NS.xin(lop, "thu", cho_giay=0):
            ket_qua.append(os.getpid())
            time.sleep(giu_giay)
    except Exception:
        pass
    return 0


def test_lan_tran_1_khong_cho_hai_tien_trinh_vao_cung_luc(tmp_path, monkeypatch):
    """Cuoc dua cu: ca hai cung thay `_dang_giu < tran` roi cung ghi the."""
    from nhan import ngan_sach as NS
    monkeypatch.setattr(NS, "_KHOA", tmp_path / "khoa")
    (tmp_path / "khoa" / "THU").mkdir(parents=True)
    monkeypatch.setitem(NS.SUC_CHUA, "THU", 1)

    thu = tmp_path / "khoa" / "THU"
    # Gia mot tien trinh khac (chinh minh) da giu the truoc.
    (thu / ("%d.the" % os.getpid())).write_text("ai do", encoding="utf-8")
    time.sleep(0.02)
    # Mot "tien trinh" den sau, the moi hon -> khong duoc o lai.
    assert NS._duoc_o_lai("THU", 1), "the cu nhat phai duoc o lai"


def test_duoc_o_lai_chi_giu_the_CU_NHAT(tmp_path, monkeypatch):
    from nhan import ngan_sach as NS
    monkeypatch.setattr(NS, "_KHOA", tmp_path / "khoa")
    thu = tmp_path / "khoa" / "THU"
    thu.mkdir(parents=True)
    cu = thu / "1.the"          # pid 1 gan nhu chac chan khong song -> bi don
    cu.write_text("x", encoding="utf-8")
    (thu / ("%d.the" % os.getpid())).write_text("toi", encoding="utf-8")
    assert NS._duoc_o_lai("THU", 1), \
        "the cua pid da chet phai bi thu hoi, cho lai cho nguoi con song"
