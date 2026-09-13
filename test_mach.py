# -*- coding: utf-8 -*-
"""test_mach.py - MACH DAP DUONG ONG phai NHAY, khong chi phai chay.

Bai kiem quan trong nhat file nay la `test_mutation_audit_bat_duoc_het`. Mot
mach dap toan chu TOT khong noi len gi neu no khong bao gio bao DO - va dieu
do khong phai gia dinh: trong **luot chay dau tien** cua `nhan/mach.py`, hai
chang la TOT GIA:

  * `c_engine` goi `canary.chay` (ham khong ton tai) roi tra TOT
  * `c_bang_quan_tri` khong doi khi cong bi bit

Mot cai la loi cua chang, mot cai la loi cua phep be. Ca hai chi lo ra nho
mutation audit. Nen o day no la mot bai kiem, khong phai mot tuy chon.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))

from nhan import mach as M  # noqa: E402


def test_ba_trang_thai_khong_phai_hai():
    """Khau do hong phai la CHUA_DO_DUOC, khong bao gio la DO hay TOT."""
    assert {M.TOT, M.DO, M.CHUA} == {"TOT", "DO", "CHUA_DO_DUOC"}
    x = M._kq("thu", None, False, "khong do duoc", chua=True)
    assert x["trang_thai"] == M.CHUA


def test_moi_chang_tra_dung_hinh_dang():
    for f in M.CHANG:
        r = f()
        assert set(r) >= {"chang", "trang_thai", "mo_ta"}
        assert r["trang_thai"] in (M.TOT, M.DO, M.CHUA)
        assert r["mo_ta"], "chang %s khong noi gi" % r["chang"]


def test_chang_hong_khong_lam_sap_ca_mach():
    """Mot chang nem ngoai le phai thanh CHUA_DO_DUOC, khong chan cac chang
    con lai - dung luat 3 cua `day_viec.py`."""
    def no():
        raise RuntimeError("thu")
    cu = M.CHANG
    try:
        M.CHANG = (no,) + cu[:2]
        r = M.chay(in_ra=lambda *a: None)
        assert len(r["chang"]) == 3
        assert r["chua_do_duoc"] >= 1
    finally:
        M.CHANG = cu


def test_engine_khong_do_duoc_thi_KHONG_duoc_bao_TOT():
    """Dung loi da xay ra: `c_engine` tung tra TOT khi khong goi duoc canary."""
    from nhan import canary as CN
    cu = CN.chay_het
    try:
        del CN.chay_het
        assert M.c_engine()["trang_thai"] == M.CHUA
    finally:
        CN.chay_het = cu


def test_cong_quan_tri_bi_bit_thi_mach_phai_bao_DO():
    """Mot cong khong tu choi ai doc y het mot cong tot - phai phan biet."""
    from nhan import quan_tri_dsl as Q
    cu = Q.kiem_con_so
    try:
        Q.kiem_con_so = lambda spec: []
        assert M.c_bang_quan_tri()["trang_thai"] == M.DO
    finally:
        Q.kiem_con_so = cu


def test_kho_teo_thi_mach_phai_bao_DO():
    from nhan import ngu_phap as NP
    moc = NP._doc_moc_cao()
    try:
        NP._ghi_moc_cao(max(moc, 1) * 5)
        assert M.c_kho_co_che()["trang_thai"] == M.DO
    finally:
        NP._ghi_moc_cao(moc)


def test_het_dia_thi_mach_phai_bao_DO():
    from nhan import dia as D
    cu = D.NGUONG_GB
    try:
        D.NGUONG_GB = D.con_gb() + 1000
        assert M.c_dia()["trang_thai"] == M.DO
    finally:
        D.NGUONG_GB = cu



def test_mutation_audit_bat_duoc_het():
    """BAI KIEM QUAN TRONG NHAT FILE NAY.

    Neu mot chang khong nhay, mach dap chi la mot bang chu TOT.
    """
    r = M.be_thu(in_ra=lambda *a: None)
    assert r["be"], "khong be chang nao - audit rong"
    assert not r["khong_nhay"], (
        "chang KHONG NHAY: %s - mach dap dang bao TOT ma khong do gi"
        % ", ".join(r["khong_nhay"]))


# ------------------------------- PHEU UNG VIEN PHAI HIEU CHUAN HAI CHIEU
#
# "0/120 qua bo loc" co HAI nghia doi hoi hai hanh dong NGUOC NHAU:
#   a) bo loc hong  -> sua `boc_llm.DAU_HIEU_LUAT`
#   b) kho can hang -> di tim nguon moi; sua bo loc luc nay chi dot tien LLM
#                      vao rac
# Dem mot chieu khong phan biet duoc. Do 13/09: ton kho 0/3.656 nhung ban da
# boc 400/400 -> la (b), trong khi mach cu bao DO va goi y dung viec cua (a).

def _gia_lap(monkeypatch, ton, qua_ton, ty_mau, co_mau=True):
    from nhan import boc_llm as BL
    from nhan import mach as M
    from nhan import so as SO
    monkeypatch.setattr(SO, "mot", lambda *a, **k: {"n": ton})
    monkeypatch.setattr(BL, "ung_vien", lambda n=120: [{}] * qua_ton)
    mau = [{"van_ban": "x"}] * 100 if co_mau else []
    monkeypatch.setattr(SO, "nhieu", lambda *a, **k: mau)
    n = {"i": 0}

    def diem(_vb):
        n["i"] += 1
        return 1 if n["i"] <= int(100 * ty_mau) else 0
    monkeypatch.setattr(BL, "_diem_luat", diem)
    return M.c_pheu_ung_vien()


def test_kho_can_hang_KHONG_duoc_bao_bo_loc_hong(monkeypatch):
    """Ton kho 0 qua, nhung mau da boc van qua het -> bo loc SONG."""
    r = _gia_lap(monkeypatch, ton=3656, qua_ton=0, ty_mau=1.0)
    assert r["trang_thai"] != "DO", r
    assert "CAN HANG" in r["mo_ta"]
    assert "nguon" in r["goi_y"].lower()
    assert "DAU_HIEU_LUAT" not in r["goi_y"]


def test_bo_loc_hong_THI_phai_bao_DO(monkeypatch):
    """Chieu nguoc: mau da boc CUNG truot -> bo loc that su hong."""
    r = _gia_lap(monkeypatch, ton=3656, qua_ton=0, ty_mau=0.1)
    assert r["trang_thai"] == "DO", r
    assert "BO LOC HONG" in r["mo_ta"]
    assert "DAU_HIEU_LUAT" in r["goi_y"]


def test_khong_co_mau_hieu_chuan_thi_CHUA_DO_DUOC(monkeypatch):
    """Khong co ban da boc nao -> khong ket luan duoc. Ba trang thai, khong
    phai hai: day khong phai `DO`."""
    r = _gia_lap(monkeypatch, ton=3656, qua_ton=0, ty_mau=1.0, co_mau=False)
    assert r["trang_thai"] not in ("TOT", "DO"), r


def test_van_TOT_khi_ung_vien_chay_binh_thuong(monkeypatch):
    """Hieu chuan chieu con lai: duong chay tot thi khong duoc doi gi - va
    khong duoc ton mot cau truy van hieu chuan nao."""
    r = _gia_lap(monkeypatch, ton=3656, qua_ton=40, ty_mau=0.0)
    assert r["trang_thai"] == "TOT", r
