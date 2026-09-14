# -*- coding: utf-8 -*-
"""Test cho `nhan/tran_cpu.py` — MOT cho khai tran CPU.

May nay la may CA NHAN cua chu du an. Hai lan (12/09 va 14/09) phien lam viec bi
cat ngang de bao "ha CPU xuong", va ca hai lan deu sua tay. Module nay bien con so
do thanh mot cho khai bao; bo test nay giu cho no khong lang le mat tac dung.
"""
from __future__ import annotations

import json
import time

import pytest

from nhan import tran_cpu as TC


@pytest.fixture
def ch(tmp_path, monkeypatch):
    p = tmp_path / "qwen.json"
    monkeypatch.setattr(TC, "CAU_HINH", p)
    TC._BO_NHO.update(tran=None, luc=0.0)
    monkeypatch.delenv("TRAN_CPU", raising=False)
    return p


def test_doc_tran_tu_cau_hinh(ch):
    ch.write_text(json.dumps({"muc_tieu_cpu": 62.0}), encoding="utf-8")
    assert TC.tran(lam_moi=True) == 62.0


def test_thieu_cau_hinh_thi_dung_mac_dinh_chu_khong_nem(ch):
    assert TC.tran(lam_moi=True) == TC.TRAN_MAC_DINH


def test_cau_hinh_hong_thi_dung_mac_dinh(ch):
    ch.write_text("{ khong phai json", encoding="utf-8")
    assert TC.tran(lam_moi=True) == TC.TRAN_MAC_DINH


def test_bien_moi_truong_thang_cau_hinh(ch, monkeypatch):
    ch.write_text(json.dumps({"muc_tieu_cpu": 62.0}), encoding="utf-8")
    monkeypatch.setenv("TRAN_CPU", "40")
    assert TC.tran(lam_moi=True) == 40.0


def test_bien_moi_truong_rac_thi_bo_qua_chu_khong_nem(ch, monkeypatch):
    ch.write_text(json.dumps({"muc_tieu_cpu": 62.0}), encoding="utf-8")
    monkeypatch.setenv("TRAN_CPU", "tam muoi")
    assert TC.tran(lam_moi=True) == 62.0


def test_dat_tran_ghi_duoc_va_doc_lai_duoc(ch):
    TC.dat_tran(75)
    assert json.loads(ch.read_text(encoding="utf-8"))["muc_tieu_cpu"] == 75.0
    assert TC.tran(lam_moi=True) == 75.0


def test_dat_tran_KHONG_lam_mat_khoa_khac(ch):
    """`qwen.json` con giu khoa LLM, tran lan, ghi chu... Ghi tran khong duoc xoa."""
    ch.write_text(json.dumps({"muc_tieu_cpu": 62.0, "model": "qwen3.7-flash",
                              "tran_lan": {"TESTER": 1}}), encoding="utf-8")
    TC.dat_tran(80)
    d = json.loads(ch.read_text(encoding="utf-8"))
    assert d["model"] == "qwen3.7-flash" and d["tran_lan"] == {"TESTER": 1}


def test_tran_bi_kep_trong_khoang_hop_le(ch):
    assert TC.dat_tran(0) == 5.0
    assert TC.dat_tran(500) == 100.0


# ------------------------------------------------------------------ CHO
def test_khong_cho_khi_cpu_duoi_tran(ch, monkeypatch):
    ch.write_text(json.dumps({"muc_tieu_cpu": 80.0}), encoding="utf-8")
    monkeypatch.setattr(TC, "cpu_hien_tai", lambda do_giay=0.3: 30.0)
    assert TC.cho_neu_qua(nhip=0.01) == 0.0


def test_CO_cho_khi_cpu_tren_tran(ch, monkeypatch):
    """Chieu nguoc: neu khong bao gio cho that thi cai tran chi la trang tri."""
    ch.write_text(json.dumps({"muc_tieu_cpu": 50.0}), encoding="utf-8")
    dem = {"n": 0}

    def gia(do_giay=0.3):
        dem["n"] += 1
        return 95.0 if dem["n"] < 3 else 10.0     # cao hai lan roi ha

    monkeypatch.setattr(TC, "cpu_hien_tai", gia)
    da_ngu = TC.cho_neu_qua(nhip=0.01)
    assert da_ngu > 0 and dem["n"] >= 3


def test_cho_co_chan_tren_de_khong_treo_ca_me_viec(ch, monkeypatch):
    ch.write_text(json.dumps({"muc_tieu_cpu": 50.0}), encoding="utf-8")
    monkeypatch.setattr(TC, "cpu_hien_tai", lambda do_giay=0.3: 100.0)
    t0 = time.time()
    da = TC.cho_neu_qua(nhip=0.01, toi_da_giay=0.1)
    assert da >= 0.1 and time.time() - t0 < 5


def test_tran_100_thi_khong_cho_gi_ca(ch, monkeypatch):
    ch.write_text(json.dumps({"muc_tieu_cpu": 100.0}), encoding="utf-8")
    monkeypatch.setattr(TC, "cpu_hien_tai", lambda do_giay=0.3: 100.0)
    assert TC.cho_neu_qua(nhip=0.01) == 0.0


# ------------------------------------------------------------- SO LUONG
def test_so_luong_goi_y_giam_khi_may_dang_ban(ch, monkeypatch):
    ch.write_text(json.dumps({"muc_tieu_cpu": 80.0}), encoding="utf-8")
    monkeypatch.setattr(TC, "cpu_hien_tai", lambda do_giay=0.5: 10.0)
    ranh = TC.so_luong_goi_y()
    monkeypatch.setattr(TC, "cpu_hien_tai", lambda do_giay=0.5: 70.0)
    ban = TC.so_luong_goi_y()
    assert ban < ranh


def test_so_luong_goi_y_luon_it_nhat_1_va_chua_lai_mot_luong(ch, monkeypatch):
    import os
    ch.write_text(json.dumps({"muc_tieu_cpu": 80.0}), encoding="utf-8")
    monkeypatch.setattr(TC, "cpu_hien_tai", lambda do_giay=0.5: 99.0)
    assert TC.so_luong_goi_y() >= 1
    monkeypatch.setattr(TC, "cpu_hien_tai", lambda do_giay=0.5: 0.0)
    assert TC.so_luong_goi_y() <= (os.cpu_count() or 4) - 1
