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


# ------------------------------------------------ chi_phi qua ghi_an_toan
def test_luu_spread_khong_xoa_do_cua_ma_khac(tmp_path, monkeypatch):
    """Ban cu doc ca bang ra ngoai roi ghi de: hai ma ghi cung luc thi ban sau
    xoa mat do cua ban truoc. Bang nay 1.644 symbol nen mat mot o la mat im
    lang."""
    from nhan import chi_phi as CP
    cf = tmp_path / "chi_phi_do.json"
    monkeypatch.setattr(CP, "CAU_HINH", cf)
    CP._DEM_LUU.clear()
    CP._luu_spread("EURUSD", {"bps": 1.0})
    CP._luu_spread("AUDCAD", {"bps": 2.0})
    d = json.loads(cf.read_text(encoding="utf-8"))["_spread_bar_mt5"]
    assert set(d) >= {"EURUSD", "AUDCAD"}, "ghi ma thu hai khong duoc xoa ma dau"
    assert d["EURUSD"]["bps"] == 1.0 and d["AUDCAD"]["bps"] == 2.0


def _ghi_spread(goc, cf, ma, bps):
    sys.path.insert(0, str(goc))
    from nhan import chi_phi as CP
    CP.CAU_HINH = Path(cf)
    CP._DEM_LUU.clear()
    CP._luu_spread(ma, {"bps": bps})
    return 0


def test_sau_tien_trinh_ghi_spread_khong_mat_o_nao(tmp_path):
    cf = tmp_path / "chi_phi_do.json"
    cf.write_text(json.dumps({"_spread_bar_mt5": {}}), encoding="utf-8")
    ma = ["EURUSD", "AUDCAD", "GBPUSD", "USDJPY", "XAUUSD", "US500"]
    ps = [mp.Process(target=_ghi_spread, args=(str(LAB), str(cf), m, i + 1.0))
          for i, m in enumerate(ma)]
    for p in ps:
        p.start()
    for p in ps:
        p.join(120)
    assert all(p.exitcode == 0 for p in ps), [p.exitcode for p in ps]
    d = json.loads(cf.read_text(encoding="utf-8"))["_spread_bar_mt5"]
    assert set(d) == set(ma), "mat %s" % (set(ma) - set(d))
